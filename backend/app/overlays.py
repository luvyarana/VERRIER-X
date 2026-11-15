"""Gaia DR3 stars around a position, for the marker overlay.

Gaia is a European Space Agency mission. The catalogue is read with a TAP query,
first from the GAVO mirror in Heidelberg and then from ESA's own archive. Each
star comes with its 2016.0 position and proper motion; the page moves it to the
date of each frame. Results are cached on disk.
"""

import csv
import io
import json
import time

import requests

from . import config
from .archive import ArchiveError, _write_atomic

GAIA_EPOCH = 2016.0
MAX_STARS = 400
SERVICES = [
    ("https://dc.g-vo.org/tap/sync", "gaia.dr3lite"),
    ("https://gea.esac.esa.int/tap-server/tap/sync", "gaiadr3.gaia_source"),
]


def _number(text: str) -> float | None:
    try:
        value = float(text)
        return value if value == value else None  # NaN -> None
    except (TypeError, ValueError):
        return None


def _query(url: str, table: str, ra: float, dec: float, radius: float, limit_mag: float) -> list[dict]:
    adql = (
        f"SELECT TOP {MAX_STARS} source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag FROM {table} "
        f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {radius:.5f})) "
        f"AND phot_g_mean_mag < {limit_mag:.1f} ORDER BY phot_g_mean_mag"
    )
    r = requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql}, timeout=40)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text)))
    if rows and "source_id" not in rows[0]:
        raise ValueError("unexpected answer from the Gaia service")
    stars = []
    for row in rows:
        star = {
            "id": row["source_id"],
            "ra": _number(row["ra"]),
            "dec": _number(row["dec"]),
            "pmra": _number(row["pmra"]) or 0.0,     # mas/yr, already multiplied by cos(dec)
            "pmdec": _number(row["pmdec"]) or 0.0,   # mas/yr
            "parallax": _number(row["parallax"]),
            "g": _number(row["phot_g_mean_mag"]),
        }
        if star["ra"] is not None and star["dec"] is not None:
            stars.append(star)
    return stars


def gaia_stars(ra: float, dec: float, fov_arcmin: float, limit_mag: float = 17.0) -> dict:
    """Up to MAX_STARS brightest Gaia stars around (ra, dec), brightest first.

    The search circle covers the corners of the field plus a margin, so that a fast
    star which was outside the field in 2016 but is inside it now is still found.
    """
    radius = fov_arcmin / 60 * 0.75 + 0.04
    name = f"gaia/{ra:.4f}_{dec:.4f}_{fov_arcmin:.1f}.json"
    known = config.find(name)
    if known:
        return json.loads(known.read_text())
    last = "no attempt"
    for url, table in SERVICES:
        for attempt in range(2):
            try:
                stars = _query(url, table, ra, dec, radius, limit_mag)
                result = {"epoch": GAIA_EPOCH, "catalogue": "Gaia DR3", "radius_deg": round(radius, 4),
                          "limit_mag": limit_mag, "stars": stars}
                _write_atomic(config.CACHE_DIR / name, json.dumps(result).encode())
                return result
            except (requests.RequestException, ValueError, KeyError) as exc:
                last = type(exc).__name__
                time.sleep(1 + attempt)
    raise ArchiveError(f"The Gaia catalogue could not be reached ({last}).")
