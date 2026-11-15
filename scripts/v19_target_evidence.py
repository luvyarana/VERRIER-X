"""V19: measure each test target in per-season median stacks (position offset, peak, aperture flux)
and save a strip of season images to the folder given as the first argument.

Run from the backend folder:
    PYTHONPATH=. uv run python ../scripts/v19_target_evidence.py ../docs/evidence
"""

import sys, warnings, json
import numpy as np
from PIL import Image
from app import align, archive, config, pipeline
warnings.simplefilter("ignore")
OUT = sys.argv[1]
T = [("barnard", 269.4486, 4.7685, 2), ("epsindi", 331.09, -56.801, 3), ("wise0855", 133.7685, -7.2429, 6),
     ("rwaur", 76.9563, 30.4014, 2), ("rdra", 248.1675, 66.755, 2)]
def centroid(img, x, y, r):
    box = img[y-r:y+r+1, x-r:x+r+1].astype(float)
    box = np.clip(box - np.nanpercentile(box, 60), 0, None)
    yy, xx = np.mgrid[-r:r+1, -r:r+1]
    return np.nansum(box*xx)/np.nansum(box), np.nansum(box*yy)/np.nansum(box)
for name, ra, dec, band in T:
    ex = [e for e in archive.search(ra, dec)["exposures"] if e["detector"] == band]
    grid, size, scale = align.target_grid(ra, dec, 10.0); half = align.cutout_half_size(10.0)
    fr = [pipeline._one_frame(e, ra, dec, half, grid, size) for e in pipeline.pick_evenly(ex, config.MAX_EXPOSURES)]
    fr = sorted([f for f in fr if f["coverage"] >= 0.5], key=lambda f: f["mjd"])
    seas = pipeline.assign_seasons([f["mjd"] for f in fr]); c = size // 2
    yy, xx = np.mgrid[:size, :size]; rr = np.hypot(xx-c, yy-c)
    print(f"\n== {name} band {band}: {len(fr)} frames")
    stacks = []
    for s in sorted(set(seas)):
        grp = [f for f, k in zip(fr, seas) if k == s]
        st = np.nanmedian([f["image"] for f in grp], axis=0); stacks.append(st)
        noise = 1.4826*np.nanmedian(np.abs(st[rr > 40] - np.nanmedian(st[rr > 40])))
        dx, dy = centroid(st, c, c, 12)
        peak = np.nanmax(st[rr < 8])
        print(f" season {s} {grp[0]['date'][:10]}..{grp[-1]['date'][:10]} n={len(grp)}: offset E {-dx*scale:+.1f}\" N {dy*scale:+.1f}\"; peak within 16\" = {peak:.3f} MJy/sr = {peak/noise:.0f} sigma (stack noise {noise:.4f}); sat px median {np.median([f['saturated_pixels'] for f in grp]):.0f}")
    # aperture flux per frame (r<5 px ~10") minus annulus
    ap = rr < 5; an = (rr > 12) & (rr < 20)
    flux = [(f["date"][:10], round(f["wavelength_um"], 3), round(float(np.nansum(f["image"][ap] - np.nanmedian(f["image"][an]))), 2), f["saturated_pixels"]) for f in fr]
    print(" flux samples (date, um, sum MJy/sr, sat):", flux[::max(1, len(flux)//10)])
    lo, hi = np.nanpercentile(np.array(stacks), [20, 99.7])
    tiles = [np.clip((st[c-60:c+61, c-60:c+61]-lo)/(hi-lo), 0, 1)**0.5 for st in stacks]
    im = np.concatenate([np.nan_to_num(t)[::-1] for t in tiles], axis=1)
    Image.fromarray((im*255).astype("u1")).resize((im.shape[1]*3, im.shape[0]*3), Image.NEAREST).save(f"{OUT}/{name}_seasons.png")
