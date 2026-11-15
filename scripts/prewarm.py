"""V18: load the five test targets on a running backend so their frames are cached.

Requests run one at a time. The quick-pick detector of each target goes first,
then (with --all) the other five detectors.

Run from the backend folder:
    uv run python -u ../scripts/prewarm.py https://verrier-x-api.onrender.com [--all]
"""

import sys
import time

import requests

# Same positions and detectors as the quick-pick buttons in frontend/app/page.tsx.
TARGETS = [
    ("Barnard's Star", 269.44627, 4.76819, 2),
    ("Epsilon Indi B", 331.09636, -56.80058, 3),
    ("WISE 0855", 133.75969, -7.24223, 6),
    ("RW Aurigae", 76.9563, 30.4014, 2),
    ("R Draconis", 248.1675, 66.755, 2),
]
FOV = 10


def warm(api: str, name: str, ra: float, dec: float, band: int) -> None:
    t0, errors = time.time(), 0
    while True:
        try:
            r = requests.get(f"{api}/api/frames", params={"ra": ra, "dec": dec, "fov": FOV, "band": band}, timeout=90).json()
        except (requests.RequestException, ValueError) as exc:
            r = {"status": "error", "message": type(exc).__name__}
        if r["status"] == "done":
            note = "" if r.get("complete", True) else " INCOMPLETE (not cached)"
            print(f"{name:15s} detector {band}: {len(r['frames']):3d} frames, {len(r['seasons'])} seasons, "
                  f"{time.time() - t0:4.0f} s{note} {r['warnings'] or ''}", flush=True)
            if r.get("complete", True) or errors >= 3:
                return
            errors += 1
        elif r["status"] == "error":
            errors += 1
            if errors > 3:
                print(f"{name:15s} detector {band}: FAILED, {r['message']}", flush=True)
                return
            time.sleep(15)
        else:
            time.sleep(5)


def main() -> None:
    api = sys.argv[1].rstrip("/")
    for name, ra, dec, band in TARGETS:
        warm(api, name, ra, dec, band)
    if "--all" in sys.argv:
        for name, ra, dec, first in TARGETS:
            for band in range(1, 7):
                if band != first:
                    warm(api, name, ra, dec, band)
    print("finished", flush=True)


if __name__ == "__main__":
    main()
