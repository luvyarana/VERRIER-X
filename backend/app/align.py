"""Put every cutout on one common grid: north up, east left, centred on the request."""

import numpy as np
from astropy.wcs import WCS
from reproject import reproject_interp

from . import config


def cutout_half_size(fov_arcmin: float) -> int:
    """Half-size in native pixels that covers the field at any detector rotation."""
    return int(np.ceil(fov_arcmin * 60 / config.PIXEL_ARCSEC / 2 * np.sqrt(2))) + 3


def target_grid(ra: float, dec: float, fov_arcmin: float) -> tuple[WCS, int, float]:
    """Output WCS, its side in pixels, and its pixel size in arcseconds."""
    fov = fov_arcmin * 60
    scale = max(config.PIXEL_ARCSEC / config.OVERSAMPLE, fov / config.MAX_OUTPUT_PX)
    size = int(round(fov / scale))
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(size + 1) / 2, (size + 1) / 2]
    w.wcs.cdelt = [-scale / 3600, scale / 3600]
    w.wcs.radesys = "ICRS"
    return w, size, scale


def align(image: np.ndarray, wcs: WCS, grid: WCS, size: int) -> np.ndarray:
    """Resample `image` onto the grid. Pixels with no data are NaN."""
    out, _ = reproject_interp((image, wcs), grid, shape_out=(size, size), order="bilinear")
    return out.astype("f4")
