"""Turn an object name into a sky position, using the CDS Sesame name resolver (SIMBAD).

SIMBAD gives the position at epoch 2000. For a star with a known proper motion the
position is moved to today's date, because a nearby star can be arcminutes away from
where it was in 2000. Answers are cached on disk.
"""

import json
import math
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from . import config
from .archive import ArchiveError, _write_atomic

SESAME = [
    "https://vizier.cfa.harvard.edu/viz-bin/nph-sesame/-oxp/SNV?",
    "https://vizier.idia.ac.za/viz-bin/nph-sesame/-oxp/SNV?",
    "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?",
]


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


def resolve(name: str) -> dict:
    name = " ".join(name.split())
    if not name or len(name) > 80:
        raise NotFound
    year = 2000.0 + (datetime.now(timezone.utc) - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).days / 365.25
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "x"
    known = config.find(f"resolve/{slug}.json")
    if known:
        return {"name": name, **move_to(json.loads(known.read_text()), year)}
    last = "no attempt"
    for base in SESAME:
        try:
            r = requests.get(base + quote(name), timeout=15)
            r.raise_for_status()
            found = parse_sesame(r.text)
            _write_atomic(config.CACHE_DIR / f"resolve/{slug}.json", json.dumps(found).encode())
            return {"name": name, **move_to(found, year)}
        except NotFound:
            raise
        except requests.RequestException as exc:
            last = type(exc).__name__
            time.sleep(0.5)
    raise ArchiveError(f"The name lookup service could not be reached ({last}).")
