"""One request from start to finish: search, fetch, clean, align, render, describe."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from astropy.time import Time

from . import align, archive, config, prepare, render

_pool = ThreadPoolExecutor(config.WORKERS)


def request_key(ra: float, dec: float, fov: float, band: int, mode: str) -> str:
    text = f"{ra:.5f}_{dec:.5f}_{fov:.2f}_{band}_{mode}_{config.PIPELINE_VERSION}"
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def result_path(key: str):
    return config.CACHE_DIR / "frames" / key / "result.json"


def assign_seasons(mjds: list[float]) -> list[int]:
    """Season number for each time (sorted ascending); a gap over 30 days starts a new one."""
    seasons, current = [], 0
    for i, mjd in enumerate(mjds):
        if i and mjd - mjds[i - 1] > config.SEASON_GAP_DAYS:
            current += 1
        seasons.append(current)
    return seasons


def pick_evenly(items: list, limit: int) -> list:
    """At most `limit` items, spread evenly through the list."""
    if len(items) <= limit:
        return items
    return [items[i] for i in np.unique(np.linspace(0, len(items) - 1, limit).round().astype(int))]


def image_noise(image: np.ndarray) -> float:
    """Noise of an image from the median absolute deviation of its pixels."""
    values = image[np.isfinite(image)]
    return 1.4826 * float(np.median(np.abs(values - np.median(values)))) if values.size else 0.0


def _round(value, digits=4):
    return None if value is None else round(float(value), digits)


def single_frame(frame: dict, season: int) -> dict:
    """Description of one exposure, plus its image."""
    e = frame["exposure"]
    return {
        "id": e["id"],
        "time": frame["date"] or Time(frame["mjd"], format="mjd").isot,
        "mjd": frame["mjd"],
        "season": season,
        "detector": e["detector"],
        "wavelength_um": frame["wavelength_um"],
        "bandwidth_um": frame["bandwidth_um"],
        "n_exposures": 1,
        "coverage": round(frame["coverage"], 3),
        "bad_fraction": round(frame["bad_fraction"], 4),
        "saturated_pixels": frame["saturated_pixels"],
        "target_flags": frame["target_flags"],
        "collection": e["collection"],
        "source_url": e["irsa_url"],
        "image": frame["image"],
    }


def stack_season(season: int, group: list[dict]) -> dict:
    """All exposures of one season combined (median of each pixel).

    The median ignores a value that appears in only a few exposures, so cosmic-ray
    hits and other one-off artefacts drop out, and the noise falls roughly with the
    square root of the number of exposures. The exposures are at different
    wavelengths within the detector's range, so the result is a broad-band image.
    """
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        image = np.nanmedian(np.array([f["image"] for f in group]), axis=0).astype("f4")
    waves = [f["wavelength_um"] for f in group if f["wavelength_um"] is not None]
    mjd = float(np.median([f["mjd"] for f in group]))
    first = group[0]["exposure"]
    return {
        "id": f"season-{season}",
        "time": Time(mjd, format="mjd").isot,
        "time_start": group[0]["date"],
        "time_end": group[-1]["date"],
        "mjd": mjd,
        "season": season,
        "detector": first["detector"],
        "wavelength_um": _round(np.median(waves)) if waves else None,
        "wavelength_min_um": _round(min(waves)) if waves else None,
        "wavelength_max_um": _round(max(waves)) if waves else None,
        "bandwidth_um": None,
        "n_exposures": len(group),
        "coverage": round(float(np.mean(np.isfinite(image))), 3),
        "bad_fraction": round(float(np.mean([f["bad_fraction"] for f in group])), 4),
        "saturated_pixels": int(np.median([f["saturated_pixels"] for f in group])),
        "target_flags": sorted({name for f in group for name in f["target_flags"]}),
        "collection": first["collection"],
        "source_url": first["irsa_url"],
        "image": image,
    }


def difference(later: dict, first: dict) -> dict:
    """A later visit minus the first visit (both already combined).

    Anything that did not change cancels. An object that moved leaves a negative
    spot where it was and a positive spot where it is now. Bright stars leave some
    residue, because the two visits sample different wavelengths.
    """
    return {
        **later,
        "id": f"{later['id']}-minus-{first['id']}",
        "image": later["image"] - first["image"],
        "n_exposures": later["n_exposures"] + first["n_exposures"],
        "minus": {k: first[k] for k in ("season", "time_start", "time_end", "n_exposures")},
        "coverage": round(float(np.mean(np.isfinite(later["image"] - first["image"]))), 3),
    }


def _one_frame(exposure, ra, dec, half, grid, size):
    cut = archive.fetch_cutout(exposure, ra, dec, half)
    clean, stats = prepare.prepare(cut["image"], cut["flags"])
    aligned = align.align(clean, archive.cutout_wcs(cut), grid, size)
    x0, _, y0, _ = cut["box"]
    tx, ty = int(round(cut["target_xy"][0])) - x0, int(round(cut["target_xy"][1])) - y0
    inside = 0 <= ty < cut["flags"].shape[0] and 0 <= tx < cut["flags"].shape[1]
    return {
        "exposure": exposure,
        "image": aligned,
        "coverage": float(np.mean(np.isfinite(aligned))),
        "target_flags": prepare.flag_names(int(cut["flags"][ty, tx])) if inside else [],
        "cached": cut["cached"],
        **{k: cut[k] for k in ("mjd", "date", "wavelength_um", "bandwidth_um")},
        **stats,
    }


def build_frames(ra: float, dec: float, fov: float, band: int, mode: str = "exposures", progress=None) -> dict:
    """Run the pipeline, write PNGs and result.json to the cache, and return the result."""
    progress = progress or (lambda **kw: None)
    key = request_key(ra, dec, fov, band, mode)
    out_dir = result_path(key).parent
    warnings = []

    progress(stage="search", message="Searching the SPHEREx archive")
    found = archive.search(ra, dec)
    if found["errors"]:
        warnings.append("Part of the archive search failed, so some exposures may be missing.")
    per_detector = {str(d): sum(e["detector"] == d for e in found["exposures"]) for d in range(1, 7)}
    in_band = [e for e in found["exposures"] if e["detector"] == band]
    chosen = pick_evenly(in_band, config.MAX_EXPOSURES)
    if len(chosen) < len(in_band):
        warnings.append(f"Showing {len(chosen)} of {len(in_band)} exposures, spread evenly in time.")

    grid, size, scale = align.target_grid(ra, dec, fov)
    half = align.cutout_half_size(fov)
    frames, failed, downloaded = [], 0, 0
    futures = [_pool.submit(_one_frame, e, ra, dec, half, grid, size) for e in chosen]
    for n, future in enumerate(as_completed(futures), 1):
        try:
            frame = future.result()
            downloaded += not frame["cached"]
            if frame["coverage"] >= config.MIN_COVERAGE:
                frames.append(frame)
        except Exception:  # one bad exposure must not sink the whole request
            failed += 1
        progress(stage="fetch", done=n, total=len(chosen), message=f"Fetched {n} of {len(chosen)} exposures")
    if failed:
        warnings.append(f"{failed} exposures could not be read and were skipped.")
    if chosen and failed == len(chosen):
        raise archive.ArchiveError("None of the exposures could be downloaded. Please try again.")

    progress(stage="render", message="Rendering frames")
    frames.sort(key=lambda f: f["mjd"])
    seasons = assign_seasons([f["mjd"] for f in frames])
    signed = mode == "difference"
    if mode in ("seasons", "difference"):
        items = [stack_season(s, [f for f, k in zip(frames, seasons) if k == s]) for s in sorted(set(seasons))]
        if signed:
            if len(items) == 1:
                warnings.append("Only one visit covers this position, so there is nothing to subtract yet.")
            items = [difference(later, items[0]) for later in items[1:]]
        noise = float(np.median([image_noise(i["image"]) for i in items])) if items else 0.0
    else:
        items = [single_frame(f, s) for f, s in zip(frames, seasons)]
        noise = float(np.median([f["noise"] for f in frames])) if frames else 0.0
    if signed:
        noise = noise or 1.0
        low, high, soft = -12 * noise, 12 * noise, 2 * noise
    else:
        low, high, soft = render.stretch_limits([i["image"] for i in items], noise)
    out_dir.mkdir(parents=True, exist_ok=True)
    listing = []
    for i, item in enumerate(items):
        image = item.pop("image")
        png = render.to_png_signed(image, high, soft) if signed else render.to_png(image, low, high, soft)
        (out_dir / f"{i:03d}.png").write_bytes(png)
        listing.append({"index": i, **item, "png_url": f"/api/frame/{key}/{i:03d}.png"})
    season_list = [
        {"index": s, "start": group[0]["date"][:10], "end": group[-1]["date"][:10], "frames": len(group)}
        for s in sorted(set(seasons))
        for group in [[f for f, k in zip(frames, seasons) if k == s]]
    ]
    result = {
        "status": "done",
        "key": key,
        "request": {"ra": ra, "dec": dec, "fov_arcmin": fov, "band": band, "mode": mode},
        "grid": {"size_px": size, "scale_arcsec": round(scale, 4), "orientation": "north up, east left"},
        "stretch": {"low": low, "high": high, "unit": "MJy/sr", "scale": "asinh", "signed": signed},
        "exposures_per_detector": per_detector,
        "exposures_in_band": len(in_band),
        "downloaded": downloaded,
        "seasons": season_list,
        "frames": listing,
        "warnings": warnings,
        "complete": not found["errors"],
    }
    if result["complete"]:  # an incomplete answer is returned but not kept, so the next call retries
        result_path(key).write_text(json.dumps(result))
    return result
