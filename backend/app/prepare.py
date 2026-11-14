"""Clean one cutout for display: remove the background and repair unusable pixels."""

import warnings

import numpy as np

# Mask planes from the FLAGS header (MSKNnnnn keywords): name -> bit number.
FLAG_BITS = {
    "TRANSIENT": 0, "OVERFLOW": 1, "SUR_ERROR": 2, "NONFUNC": 6, "DICHROIC": 7, "MISSING_DATA": 9,
    "HOT": 10, "COLD": 11, "FULLSAMPLE": 12, "PHANMISS": 14, "NONLINEAR": 15, "PERSIST": 17,
    "OUTLIER": 19, "CROSSTALK": 20, "SOURCE": 21, "GHOST": 22, "GHOST_FPA": 23, "GHOST_EXT": 24,
    "STREAK": 25, "BLOOM": 26, "SNOWBALL": 27, "HALO": 28,
}


def _mask(*names: str) -> int:
    return sum(1 << FLAG_BITS[n] for n in names)


# Pixels whose value cannot be trusted. SOURCE (bit 21) only marks a known star and is
# never bad. OUTLIER is left alone on purpose: a moving object could be flagged as one.
BAD = _mask("TRANSIENT", "SUR_ERROR", "NONFUNC", "MISSING_DATA", "HOT", "COLD", "PHANMISS", "SNOWBALL")
# Pixels lost because the star was too bright; these are repaired as bright, not as sky.
SATURATED = _mask("OVERFLOW", "NONLINEAR")


def flag_names(value: int) -> list[str]:
    return [name for name, bit in FLAG_BITS.items() if value >> bit & 1]


def background(image: np.ndarray, usable: np.ndarray) -> tuple[float, float]:
    """Sigma-clipped median and noise (from the median absolute deviation) of the sky."""
    values = image[usable]
    if values.size == 0:
        return 0.0, 0.0
    med, sigma = float(np.median(values)), 0.0
    for _ in range(4):
        sigma = 1.4826 * float(np.median(np.abs(values - med)))
        keep = np.abs(values - med) < 3 * sigma
        if sigma == 0 or keep.all():
            break
        values = values[keep]
        med = float(np.median(values))
    return med, sigma


def _neighbours(a: np.ndarray) -> np.ndarray:
    p = np.pad(a, 1, constant_values=np.nan)
    ny, nx = a.shape
    return np.stack([p[dy : dy + ny, dx : dx + nx] for dy in range(3) for dx in range(3) if (dy, dx) != (1, 1)])


def fill(image: np.ndarray, holes: np.ndarray, bright: np.ndarray, rounds: int = 4) -> np.ndarray:
    """Replace hole pixels from their neighbours: the largest neighbour where `bright`
    is set (cores of saturated stars), the median neighbour elsewhere."""
    out = image.astype("f4", copy=True)
    out[holes] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for _ in range(rounds):
            todo = np.isnan(out) & holes
            if not todo.any():
                break
            near = _neighbours(out)
            value = np.where(bright, np.nanmax(near, axis=0), np.nanmedian(near, axis=0))
            out[todo] = value[todo]
    return out


def prepare(image: np.ndarray, flags: np.ndarray) -> tuple[np.ndarray, dict]:
    """Background-subtracted, repaired image plus a few numbers about it."""
    finite = np.isfinite(image)
    bad = (flags & BAD) != 0
    saturated = (flags & SATURATED) != 0
    bg, noise = background(image, finite & ~bad & ~saturated)
    holes = ~finite | bad | saturated
    # A blank pixel touching a saturated one is part of the same blown-out core.
    core = saturated | (~finite & (_neighbours(saturated.astype("f4")).max(axis=0) > 0))
    clean = fill(image - bg, holes, core)
    return clean, {
        "background": bg,
        "noise": noise,
        "bad_fraction": float(np.mean(~finite | bad)),
        "saturated_pixels": int(np.sum(core)),
    }
