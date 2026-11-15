"""Find SPHEREx exposures (IRSA SIA2 search) and read small cutouts from the S3 mirror.

Only the bytes needed are downloaded, with HTTP range requests: each extension's
header, then the block of rows that contains the cutout. Both file layouts are
handled (FLAGS as a plain image, or Rice-compressed one image row per table row).
Search results and cutouts are cached on disk.
"""

import io
import json
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from astropy.io.fits.hdu.compressed._codecs import Rice1
from astropy.io.votable import parse_single_table
from astropy.wcs import WCS

from . import config

BLOCK = 2880  # FITS files are made of 2880-byte blocks

session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32))


class ArchiveError(RuntimeError):
    """The archive could not be reached or returned something unusable."""


# ---------------------------------------------------------------- search

def _search_one(collection: str, ra: float, dec: float) -> list[dict]:
    """Search one collection, using the disk cache when it is fresh."""
    name = f"search/{collection}_{ra:.4f}_{dec:.4f}.json"
    path = config.CACHE_DIR / name
    known = config.find(name)
    if known and time.time() - known.stat().st_mtime < config.SEARCH_TTL_DAYS * 86400:
        return json.loads(known.read_text())
    params = {"COLLECTION": collection, "POS": f"circle {ra} {dec} {config.SEARCH_RADIUS_DEG}"}
    last = "no attempt"
    for attempt in range(config.SEARCH_TRIES):
        try:
            r = session.get(config.SIA_URL, params=params, timeout=60)
            if r.status_code == 200:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    table = parse_single_table(io.BytesIO(r.content)).to_table(use_names_over_ids=True)
                rows = [
                    {
                        "collection": collection,
                        "mjd": float(row["t_min"]),
                        "detector": int(str(row["energy_bandpassname"]).strip()[-1]),
                        "irsa_url": str(row["access_url"]),
                    }
                    for row in table
                ]
                _write_atomic(path, json.dumps(rows).encode())
                return rows
            last = f"HTTP {r.status_code}"
        except (requests.RequestException, ValueError, KeyError) as exc:
            last = type(exc).__name__
        time.sleep(2 * (attempt + 1))
    if known:  # a stale answer is better than none
        return json.loads(known.read_text())
    raise ArchiveError(f"{collection}: {last}")


def exposure_id(url: str) -> str:
    """Observation name without the processing version, e.g. level2_2025W33_2C_0321_1D3."""
    return url.rsplit("/", 1)[-1].split("_spx_")[0]


def search(ra: float, dec: float) -> dict:
    """All exposures that contain (ra, dec). Returns {"exposures": [...], "errors": [...]}."""
    with ThreadPoolExecutor(len(config.COLLECTIONS)) as pool:
        futures = [pool.submit(_search_one, c, ra, dec) for c in config.COLLECTIONS]
    seen, errors = {}, []
    for future in futures:
        try:
            for row in future.result():
                row["id"] = exposure_id(row["irsa_url"])
                row["url"] = row["irsa_url"].replace(config.IRSA_PREFIX, config.S3_PREFIX)
                seen.setdefault(row["id"], row)
        except ArchiveError as exc:
            errors.append(str(exc))
    if errors and not seen:
        raise ArchiveError("The SPHEREx archive search at IRSA is not responding (" + "; ".join(errors) + ")")
    return {"exposures": sorted(seen.values(), key=lambda e: e["mjd"]), "errors": errors}


# ---------------------------------------------------------------- byte-range reading

def read_range(url: str, start: int, length: int, tries: int = 4) -> bytes:
    """Bytes [start, start+length). A negative start reads the last `length` bytes."""
    rng = f"bytes=-{length}" if start < 0 else f"bytes={start}-{start + length - 1}"
    for attempt in range(tries):
        try:
            r = session.get(url, headers={"Range": rng}, timeout=60)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if attempt == tries - 1:
                raise
            time.sleep(0.5 * (attempt + 1))


def read_header(url: str, start: int) -> tuple[fits.Header, int]:
    """Return the header that begins at byte `start`, and its length in bytes."""
    buf = read_range(url, start, 12 * BLOCK)
    while True:
        for i in range(0, len(buf), 80):
            if buf[i : i + 8] == b"END     ":
                length = ((i + 80 + BLOCK - 1) // BLOCK) * BLOCK
                return fits.Header.fromstring(buf[:length].decode("ascii")), length
        more = read_range(url, start + len(buf), 12 * BLOCK)
        if not more:
            raise ArchiveError("FITS header has no END card")
        buf += more


def data_size(hdr: fits.Header) -> int:
    """Bytes of data that follow this header, before padding."""
    if hdr.get("NAXIS", 0) == 0:
        return 0
    size = abs(hdr["BITPIX"]) // 8
    for k in range(1, hdr["NAXIS"] + 1):
        size *= hdr[f"NAXIS{k}"]
    return size + hdr.get("PCOUNT", 0)


def read_plain(url, hdr, data_start, box):
    x0, x1, y0, y1 = box
    nx, nbytes = hdr["NAXIS1"], abs(hdr["BITPIX"]) // 8
    raw = read_range(url, data_start + y0 * nx * nbytes, (y1 - y0) * nx * nbytes)
    dtype = {-32: ">f4", 32: ">i4", -64: ">f8", 16: ">i2"}[hdr["BITPIX"]]
    return np.frombuffer(raw, dtype=dtype).reshape(y1 - y0, nx)[:, x0:x1].astype(dtype[1:])


def read_rice_rows(url, hdr, data_start, box):
    """Compressed image stored one image row per table row (ZTILE2 = 1)."""
    x0, x1, y0, y1 = box
    if hdr["ZCMPTYPE"] != "RICE_1" or hdr["ZTILE2"] != 1 or hdr["TFORM1"][:2] != "1P":
        raise ArchiveError("unexpected compression layout")
    row_len, nx = hdr["NAXIS1"], hdr["ZNAXIS1"]
    heap_start = data_start + hdr.get("THEAP", row_len * hdr["NAXIS2"])
    table = read_range(url, data_start + y0 * row_len, (y1 - y0) * row_len)
    desc = np.frombuffer(table, dtype=">i4").reshape(y1 - y0, row_len // 4)[:, :2]  # (length, offset)
    first, last = int(desc[:, 1].min()), int((desc[:, 1] + desc[:, 0]).max())
    heap = read_range(url, heap_start + first, last - first)
    params = {hdr[f"ZNAME{i}"]: hdr[f"ZVAL{i}"] for i in range(1, 4) if f"ZNAME{i}" in hdr}
    codec = Rice1(blocksize=params.get("BLOCKSIZE", 32), bytepix=params.get("BYTEPIX", 4), tilesize=nx)
    rows = [
        np.asarray(codec.decode(np.frombuffer(heap, dtype=np.uint8, count=n, offset=off - first))).view("i4")[x0:x1]
        for n, off in desc
    ]
    return np.stack(rows) + int(hdr.get("ZZERO", hdr.get("BZERO", 0)))


def celestial_wcs(hdr: fits.Header) -> WCS:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return WCS(hdr).celestial


def cutout(url: str, ra: float, dec: float, half: int, wanted=("IMAGE", "FLAGS")) -> dict:
    """Square cutouts of side 2*half+1 pixels centred on (ra, dec), clipped to the detector.

    Returns the IMAGE header, the pixel box (x0, x1, y0, y1), the target's
    full-frame pixel position, and one array per extension in `wanted`.
    """
    offset = BLOCK  # the primary header is one block and has no data
    out, box, found = {}, None, 0
    while found < len(wanted):
        hdr, hdr_len = read_header(url, offset)
        data_start = offset + hdr_len
        offset = data_start + ((data_size(hdr) + BLOCK - 1) // BLOCK) * BLOCK
        name = hdr.get("EXTNAME", "").strip()
        if name == "IMAGE":
            nx, ny = hdr["NAXIS1"], hdr["NAXIS2"]
            x, y = (float(v) for v in celestial_wcs(hdr).world_to_pixel_values(ra, dec))
            if not (np.isfinite(x) and np.isfinite(y)):
                raise ValueError("position is outside this image")
            cx, cy = int(round(x)), int(round(y))
            box = (max(0, cx - half), min(nx, cx + half + 1), max(0, cy - half), min(ny, cy + half + 1))
            if box[0] >= box[1] or box[2] >= box[3]:
                raise ValueError("position is outside this image")
            out.update(header=hdr, box=box, target_xy=(x, y))
        if name not in wanted:
            continue
        if box is None:
            raise ArchiveError("IMAGE extension must come first")
        found += 1
        out[name] = (read_rice_rows if hdr.get("ZIMAGE") else read_plain)(url, hdr, data_start, box)
    return out


# ---------------------------------------------------------------- wavelength

_wave_tables: dict[int, tuple | None] = {}


def wave_table(url: str, detector: int):
    """Per-detector wavelength lookup table (control points X, Y and VALUES), read once.

    It is the last extension of every file: one header block and one data block.
    """
    if detector not in _wave_tables:
        table = None
        try:
            raw = read_range(url, -2 * BLOCK, 2 * BLOCK)
            hdr = fits.Header.fromstring(raw[:BLOCK].decode("ascii"))
            if hdr.get("EXTNAME", "").strip() == "WCS-WAVE":
                nx, ny = int(hdr["TFORM1"].strip()[:-1]), int(hdr["TFORM2"].strip()[:-1])
                data = raw[BLOCK:]
                xs = np.frombuffer(data, ">i4", nx, 0).astype(float)
                ys = np.frombuffer(data, ">i4", ny, 4 * nx).astype(float)
                values = np.frombuffer(data, ">f4", 2 * nx * ny, 4 * (nx + ny)).reshape(ny, nx, 2).astype(float)
                table = (xs, ys, values)
        except (requests.RequestException, KeyError, ValueError):
            return None  # not cached, so the next exposure tries again
        _wave_tables[detector] = table
    return _wave_tables[detector]


def wavelength_at(table, x: float, y: float) -> tuple[float | None, float | None]:
    """Central wavelength and bandwidth (microns) at 0-based detector pixel (x, y)."""
    if table is None:
        return None, None
    xs, ys, values = table
    fx = float(np.clip(np.interp(x + 1, xs, np.arange(len(xs))), 0, len(xs) - 1.000001))
    fy = float(np.clip(np.interp(y + 1, ys, np.arange(len(ys))), 0, len(ys) - 1.000001))
    i, j, u, v = int(fx), int(fy), fx % 1, fy % 1
    block = values[j : j + 2, i : i + 2]
    w = np.array([[(1 - u) * (1 - v), u * (1 - v)], [(1 - u) * v, u * v]])
    wave, width = (float((block[..., k] * w).sum()) for k in (0, 1))
    return wave, width


# ---------------------------------------------------------------- cached cutouts

def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)


def fetch_cutout(exposure: dict, ra: float, dec: float, half: int) -> dict:
    """Cutout of one exposure, from the disk cache if present.

    Returns image (MJy/sr), flags, header (text), box, target_xy, mjd, date,
    wavelength_um and bandwidth_um at the target.
    """
    path = config.CACHE_DIR / "cutouts" / f"{exposure['id']}_{ra:.5f}_{dec:.5f}_{half}.npz"
    if path.exists():
        with np.load(path) as z:
            return {**json.loads(str(z["meta"])), "image": z["image"], "flags": z["flags"], "cached": True}
    cut = cutout(exposure["url"], ra, dec, half)
    hdr = cut["header"]
    x, y = cut["target_xy"]
    wave, width = wavelength_at(wave_table(exposure["url"], exposure["detector"]), x, y)
    meta = {
        "header": hdr.tostring(),
        "box": list(cut["box"]),
        "target_xy": [x, y],
        "mjd": float(hdr.get("MJD-AVG", exposure["mjd"])),
        "date": str(hdr.get("DATE-AVG", "")),
        "wavelength_um": wave,
        "bandwidth_um": width,
    }
    buf = io.BytesIO()
    np.savez_compressed(buf, image=cut["IMAGE"], flags=cut["FLAGS"].astype("i4"), meta=np.array(json.dumps(meta)))
    _write_atomic(path, buf.getvalue())
    return {**meta, "image": cut["IMAGE"], "flags": cut["FLAGS"], "cached": False}


def cutout_wcs(cut: dict) -> WCS:
    """WCS of the cutout array (the full-frame WCS shifted to the cutout's corner)."""
    x0, x1, y0, y1 = cut["box"]
    return celestial_wcs(fits.Header.fromstring(cut["header"]))[y0:y1, x0:x1]
