"""V01: which SPHEREx exposures cover each challenge test target, and in which seasons?

Queries IRSA's SIA2 service for the SPHEREx DR1 and QR3 collections (wide and deep), with retries,
and writes a summary to docs/coverage.json.

Run from the backend folder:
    uv run python -u ../scripts/v01_coverage_spike.py

Positions are approximate 2026 positions (catalogue position moved by proper
motion). They are good enough for a coverage search with a 0.02 degree radius;
docs/targets.md will hold the exact values.
"""

import io
import json
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import requests
from astropy.io.votable import parse_single_table
from astropy.time import Time

warnings.simplefilter("ignore")

SIA = "https://irsa.ipac.caltech.edu/SIA"
COLLECTIONS = ["spherex_dr1", "spherex_dr1_deep", "spherex_qr3", "spherex_qr3_deep"]
RADIUS_DEG = 0.02
SEASON_GAP_DAYS = 30
TARGETS = {
    "Barnard's Star": (269.4486, 4.7685),
    "Epsilon Indi B": (331.0900, -56.8010),
    "WISE 0855": (133.7685, -7.2429),
    "RW Aurigae": (76.9563, 30.4014),
    "R Draconis": (248.1675, 66.7550),
}
OUT = Path(__file__).resolve().parents[1] / "docs" / "coverage.json"


def query(ra: float, dec: float, collection: str, tries: int = 6):
    params = {"COLLECTION": collection, "POS": f"circle {ra} {dec} {RADIUS_DEG}"}
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(SIA, params=params, timeout=90)
            if r.status_code == 200:
                return parse_single_table(io.BytesIO(r.content)).to_table(use_names_over_ids=True), attempt
            last = f"HTTP {r.status_code}"
        except requests.RequestException as exc:
            last = type(exc).__name__
        time.sleep(5 * (attempt + 1))
    return last, tries


def seasons(mjd: np.ndarray, detectors: list[str]) -> list[dict]:
    order = np.argsort(mjd)
    mjd = mjd[order]
    detectors = [detectors[i] for i in order]
    groups, start = [], 0
    for i in range(1, len(mjd) + 1):
        if i == len(mjd) or mjd[i] - mjd[i - 1] > SEASON_GAP_DAYS:
            groups.append(
                {
                    "start": Time(mjd[start], format="mjd").iso[:10],
                    "end": Time(mjd[i - 1], format="mjd").iso[:10],
                    "files": i - start,
                    "per_detector": dict(sorted(Counter(detectors[start:i]).items())),
                }
            )
            start = i
    return groups


def main() -> None:
    results = {}
    for name, (ra, dec) in TARGETS.items():
        results[name] = {"ra": ra, "dec": dec, "collections": {}}
        for collection in COLLECTIONS:
            table, fails = query(ra, dec, collection)
            if isinstance(table, str):
                entry = {"error": table}
                print(f"{name:16s} {collection:17s} FAILED after {fails} tries: {table}")
            else:
                entry = {"files": len(table), "failed_attempts": fails, "seasons": []}
                if len(table):
                    dets = [str(b)[-2:] for b in table["energy_bandpassname"]]
                    entry["seasons"] = seasons(np.array(table["t_min"], dtype=float), dets)
                    entry["example_url"] = str(table["access_url"][0])
                print(f"{name:16s} {collection:17s} {len(table):4d} files; seasons: "
                      + "; ".join(f"{s['start']}..{s['end']} ({s['files']})" for s in entry["seasons"]))
            results[name]["collections"][collection] = entry
            OUT.parent.mkdir(exist_ok=True)
            OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
