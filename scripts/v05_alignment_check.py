"""V05 check: do field stars sit on the same output pixel in every frame?

Builds the Barnard's Star frames (10 arcminutes, detector 2), picks the brightest
field stars away from the centre, and measures each star's centroid in every frame.

Run from the backend folder:
    PYTHONPATH=. uv run python ../scripts/v05_alignment_check.py
"""

import warnings

import numpy as np

warnings.simplefilter("ignore")

from app import align, archive, config, pipeline

RA, DEC, FOV, BAND = 269.4486, 4.7685, 10.0, 2


def centroid(img, x, y, r=5):
    box = img[y - r : y + r + 1, x - r : x + r + 1].astype(float)
    box = np.clip(box - np.nanpercentile(box, 60), 0, None)
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    return x + np.nansum(box * xx) / np.nansum(box), y + np.nansum(box * yy) / np.nansum(box)


def main():
    exposures = [e for e in archive.search(RA, DEC)["exposures"] if e["detector"] == BAND]
    grid, size, scale = align.target_grid(RA, DEC, FOV)
    half = align.cutout_half_size(FOV)
    frames = [pipeline._one_frame(e, RA, DEC, half, grid, size) for e in pipeline.pick_evenly(exposures, config.MAX_EXPOSURES)]
    frames.sort(key=lambda f: f["mjd"])
    cube = np.array([f["image"] for f in frames])
    median = np.nanmedian(cube, axis=0)

    c = size // 2
    yy, xx = np.mgrid[:size, :size]
    work = np.where((np.hypot(xx - c, yy - c) > 45) & (xx > 12) & (xx < size - 12) & (yy > 12) & (yy < size - 12), median, -np.inf)
    stars = []
    while len(stars) < 6:
        y, x = np.unravel_index(np.argmax(work), work.shape)
        stars.append((x, y))
        work[max(0, y - 20) : y + 21, max(0, x - 20) : x + 21] = -np.inf

    print(f"{len(frames)} frames, output pixel {scale:.2f} arcsec, native pixel {config.PIXEL_ARCSEC} arcsec")
    worst = 0.0
    for x, y in stars:
        pos = np.array([centroid(img, x, y) for img in cube])
        dev = np.hypot(*(pos - np.nanmedian(pos, axis=0)).T) * scale
        worst = max(worst, float(np.nanpercentile(dev, 90)))
        print(f"star at ({x:3d},{y:3d}): scatter rms {np.sqrt(np.nanmean(dev**2)):.2f} arcsec, "
              f"90% within {np.nanpercentile(dev, 90):.2f} arcsec, worst {np.nanmax(dev):.2f} arcsec")
    print(f"90% of measurements within {worst / config.PIXEL_ARCSEC:.2f} native pixels (target: 0.5)")

    # Barnard's Star itself, per season
    seasons = pipeline.assign_seasons([f["mjd"] for f in frames])
    for s in sorted(set(seasons)):
        pos = np.array([centroid(img, c, c, r=25) for img, k in zip(cube, seasons) if k == s])
        east, north = -(np.nanmedian(pos[:, 0]) - c) * scale, (np.nanmedian(pos[:, 1]) - c) * scale
        print(f"season {s} ({frames[seasons.index(s)]['date'][:7]}): Barnard's Star offset east {east:+.1f} arcsec, north {north:+.1f} arcsec")


if __name__ == "__main__":
    main()
