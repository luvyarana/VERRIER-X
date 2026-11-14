"""V02: read a small SPHEREx cutout straight from the Amazon S3 mirror.

Only the bytes needed are downloaded (HTTP range requests): each extension's
header, then the block of rows that contains the cutout.

Handles both file layouts:
  QR2 (older): IMAGE, FLAGS, VARIANCE, ZODI all stored as plain images.
  DR1 / QR3:   FLAGS is Rice-compressed, one image row per table row.

Findings are in docs/data-notes.md.

Run from the backend folder:
    uv run python -u ../scripts/v02_cutout_spike.py
"""

import time
import warnings
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from astropy.io import fits
from astropy.io.fits.hdu.compressed._codecs import Rice1
from astropy.wcs import WCS

warnings.simplefilter("ignore")

S3 = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/"
IRSA = "https://irsa.ipac.caltech.edu/ibe/data/spherex/"
BLOCK = 2880  # FITS files are made of 2880-byte blocks
WANTED = ("IMAGE", "FLAGS", "VARIANCE", "ZODI")

session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32))


def s3_url(access_url: str) -> str:
    """Turn an IRSA access URL into the matching S3 URL."""
    return access_url.replace(IRSA, S3)


def read_range(url: str, start: int, length: int, tries: int = 4) -> bytes:
    for attempt in range(tries):
        try:
            r = session.get(url, headers={"Range": f"bytes={start}-{start + length - 1}"}, timeout=60)
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
        buf += read_range(url, start + len(buf), 12 * BLOCK)


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
        raise ValueError("unexpected compression layout")
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


def cutout(url: str, ra: float, dec: float, half: int) -> dict:
    """Return square cutouts of side 2*half+1 pixels centred on (ra, dec)."""
    offset = BLOCK  # the primary header is one block and has no data
    out, box, found = {}, None, 0
    while found < len(WANTED):
        hdr, hdr_len = read_header(url, offset)
        data_start = offset + hdr_len
        offset = data_start + ((data_size(hdr) + BLOCK - 1) // BLOCK) * BLOCK
        name = hdr.get("EXTNAME", "").strip()
        if name not in WANTED:
            continue
        found += 1
        if name == "IMAGE":
            nx, ny = hdr["NAXIS1"], hdr["NAXIS2"]
            wcs = WCS(hdr).celestial
            x, y = (float(v) for v in wcs.world_to_pixel_values(ra, dec))
            box = (max(0, int(x) - half), min(nx, int(x) + half + 1),
                   max(0, int(y) - half), min(ny, int(y) + half + 1))
            if box[0] >= box[1] or box[2] >= box[3]:
                raise ValueError("position is outside this image")
            out["header"] = hdr
            out["wcs"] = wcs[box[2] : box[3], box[0] : box[1]]
            out["target_xy"] = (x - box[0], y - box[2])
        reader = read_rice_rows if hdr.get("ZIMAGE") else read_plain
        out[name] = reader(url, hdr, data_start, box)
    return out


QR2_FILE = "qr2/level2/2025W17_4B/l2b-v20-2025-240/2/level2_2025W17_4B_0001_{slew}D2_spx_l2b-v20-2025-240.fits"
DR1_FILE = "dr1/level2/2025W33_2C/l2b-v27-2026-228/3/level2_2025W33_2C_0321_1D3_spx_l2b-v27-2026-228.fits"


def main() -> None:
    for label, url, ra, dec in (
        ("QR2 layout", S3 + QR2_FILE.format(slew=1), 164.66, 29.05),
        ("DR1 layout", S3 + DR1_FILE, 269.4486, 4.7685),
    ):
        for half in (15, 50, 150):
            t0 = time.perf_counter()
            cut = cutout(url, ra, dec, half)
            side = 2 * half + 1
            flags = cut["FLAGS"]
            print(f"{label}: {side:4d} px ({side * 6.14 / 60:4.1f} arcmin) in {time.perf_counter() - t0:5.1f} s; "
                  f"shapes {cut['IMAGE'].shape} {flags.shape}; flagged {np.mean(flags != 0):.2f}; "
                  f"bit 21 set on {np.mean((flags >> 21) & 1):.2f}; {cut['header']['DATE-AVG']}")

    for workers in (8, 16):
        jobs = [1, 2, 3, 4] * (workers // 4)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(lambda s: cutout(S3 + QR2_FILE.format(slew=s), 164.66, 29.05, 50), jobs))
        dt = time.perf_counter() - t0
        print(f"{len(jobs):2d} cutouts (101 px), {workers:2d} at once: {dt:5.1f} s total, {dt / len(jobs):.2f} s each")


if __name__ == "__main__":
    main()
