"""Turn an object name into a sky position, using the CDS Sesame name resolver (SIMBAD).

SIMBAD gives the position at epoch 2000. For a star with a known proper motion the
position is moved to epoch 2026.0, the middle of the SPHEREx data, because a nearby
star can be arcminutes away from where it was in 2000. A fixed epoch (not today's
date) keeps the answer the same from day to day, so cached frames are reused.
Answers are cached on disk.
"""

import json
import math
import re
import time
from urllib.parse import quote

import requests

from . import config
from .archive import ArchiveError, _write_atomic

SESAME = [
    "https://vizier.cfa.harvard.edu/viz-bin/nph-sesame/-oxp/SNV?",
    "https://vizier.idia.ac.za/viz-bin/nph-sesame/-oxp/SNV?",
    "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?",
]


# Short names people use that SIMBAD does not know.
ALIASES = {
    "wise 0855": "WISE J085510.83-071442.5",
    "wise 0855-0714": "WISE J085510.83-071442.5",
    "wise0855": "WISE J085510.83-071442.5",
}


class NotFound(LookupError):
    """No object of that name is known."""


def _tag(xml: str, name: str) -> float | None:
    m = re.search(rf"<{name}>\s*([-+0-9.eE]+)\s*</{name}>", xml)
    return float(m.group(1)) if m else None


def parse_sesame(xml: str) -> dict:
    """Position (deg, epoch 2000) and proper motion (mas/yr) from a Sesame XML answer."""
    ra, dec = _tag(xml, "jradeg"), _tag(xml, "jdedeg")
    if ra is None or dec is None:
        raise NotFound
    return {"ra_j2000": ra, "dec_j2000": dec, "pm_ra": _tag(xml, "pmRA") or 0.0, "pm_dec": _tag(xml, "pmDE") or 0.0}


def move_to(found: dict, year: float) -> dict:
    """Add the position at `year`, moved from epoch 2000 by the proper motion."""
    dt = year - 2000.0
    dec = found["dec_j2000"] + found["pm_dec"] * dt / 3.6e6
    ra = (found["ra_j2000"] + found["pm_ra"] * dt / 3.6e6 / math.cos(math.radians(found["dec_j2000"]))) % 360
    moved = math.hypot(found["pm_ra"], found["pm_dec"]) * dt / 1000
    return {**found, "ra": round(ra, 5), "dec": round(max(-90.0, min(90.0, dec)), 5), "epoch": round(year, 2),
            "moved_arcsec": round(moved, 1)}


def snap(found: dict) -> dict:
    """Use the stored position of a test target when the answer is within 2 arcseconds of it,
    so that its ready-made frames are used."""
    ra, dec = config.snap_to_known(found["ra"], found["dec"])
    return {**found, "ra": ra, "dec": dec}


def resolve(name: str) -> dict:
    name = " ".join(name.split())
    if not name or len(name) > 80:
        raise NotFound
    name = ALIASES.get(name.lower(), name)
    year = config.MARKER_EPOCH
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "x"
    known = config.find(f"resolve/{slug}.json")
    if known:
        return {"name": name, **snap(move_to(json.loads(known.read_text()), year))}
    last = "no attempt"
    for base in SESAME:
        try:
            r = requests.get(base + quote(name), timeout=15)
            r.raise_for_status()
            found = parse_sesame(r.text)
            _write_atomic(config.CACHE_DIR / f"resolve/{slug}.json", json.dumps(found).encode())
            return {"name": name, **snap(move_to(found, year))}
        except NotFound:
            raise
        except requests.RequestException as exc:
            last = type(exc).__name__
            time.sleep(0.5)
    raise ArchiveError(f"The name lookup service could not be reached ({last}).")
