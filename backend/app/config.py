"""Settings for the backend. A new data release is added by editing COLLECTIONS."""

import os
from pathlib import Path

# IRSA image-search collections, in order of preference (first wins on duplicates).
COLLECTIONS = ["spherex_dr1", "spherex_dr1_deep", "spherex_qr3", "spherex_qr3_deep"]

SIA_URL = "https://irsa.ipac.caltech.edu/SIA"
IRSA_PREFIX = "https://irsa.ipac.caltech.edu/ibe/data/spherex/"
S3_PREFIX = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/"

CACHE_DIR = Path(os.environ.get("VERRIER_CACHE", Path(__file__).resolve().parents[1] / "cache"))

# Starter cache shipped inside the image: search results and finished frames for the
# test targets. It is read-only and survives restarts; CACHE_DIR is checked first.
SEED_DIR = Path(os.environ.get("VERRIER_SEED", Path(__file__).resolve().parents[1] / "seed"))


def find(relative: str) -> Path | None:
    """Path of a cached file, looking in the live cache and then the starter cache."""
    for base in (CACHE_DIR, SEED_DIR):
        if (base / relative).exists():
            return base / relative
    return None


SEARCH_RADIUS_DEG = 0.003      # the target itself must be inside the exposure
SEARCH_TTL_DAYS = 7            # how long a cached search result is trusted
SEARCH_TRIES = 4

PIXEL_ARCSEC = 6.14            # native SPHEREx pixel size (used for sizing only)
OVERSAMPLE = 3                 # output pixels per native pixel at small fields of view
MAX_OUTPUT_PX = 512
FOV_MIN_ARCMIN, FOV_MAX_ARCMIN, FOV_DEFAULT_ARCMIN = 2.0, 60.0, 10.0

MAX_EXPOSURES = 72             # most frames returned for one request
MIN_COVERAGE = 0.5             # drop frames that cover less than this share of the field
WORKERS = 16                   # cutouts downloaded at once
SEASON_GAP_DAYS = 30           # a longer gap starts a new season

PIPELINE_VERSION = "1"         # bump to invalidate cached frames
