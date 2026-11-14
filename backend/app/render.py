"""Turn aligned images into PNG frames with one shared brightness scale."""

import io

import numpy as np
from PIL import Image


def stretch_limits(frames: list[np.ndarray], noise: float) -> tuple[float, float, float]:
    """(low, high, soft) shared by all frames, so brightness is comparable between them."""
    sample = np.concatenate([f[np.isfinite(f)].ravel() for f in frames]) if frames else np.array([])
    if sample.size == 0:
        return 0.0, 1.0, 1.0
    if not noise > 0:
        noise = float(np.std(sample)) or 1.0
    low = -1.5 * noise
    high = max(float(np.percentile(sample, 99.8)), 10 * noise)
    return low, high, 3 * noise


def to_png(frame: np.ndarray, low: float, high: float, soft: float) -> bytes:
    """8-bit greyscale PNG, asinh stretch, north up (FITS row 0 is the bottom row)."""
    scaled = np.arcsinh((frame - low) / soft) / np.arcsinh((high - low) / soft)
    pixels = np.where(np.isfinite(scaled), np.clip(scaled, 0, 1) * 255, 0).astype("u1")
    buf = io.BytesIO()
    Image.fromarray(pixels[::-1], mode="L").save(buf, format="PNG", optimize=True)
    return buf.getvalue()
