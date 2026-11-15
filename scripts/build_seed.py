"""Build the starter cache (backend/seed): finished frames and search results for the
five test targets, every detector, both views, 10 arcminutes. The backend image ships with it, so
these targets load at once after any restart and without the IRSA search.

Run from the backend folder (takes a while; cutouts are cached in backend/cache):
    PYTHONPATH=. caffeinate -i uv run python -u ../scripts/build_seed.py
"""

import shutil
import time

from app import archive, config, overlays, pipeline

# Same positions as the quick-pick buttons in frontend/app/page.tsx.
TARGETS = [
    ("Barnard's Star", 269.44627, 4.76819),
    ("Epsilon Indi B", 331.09636, -56.80058),
    ("WISE 0855", 133.75969, -7.24223),
    ("RW Aurigae", 76.9563, 30.4014),
    ("R Draconis", 248.1675, 66.755),
]
FOV = 10.0


def main() -> None:
    seed = config.SEED_DIR
    problems = []
    for name, ra, dec in TARGETS:
        for attempt in range(5):  # every collection must answer before anything is kept
            found = archive.search(ra, dec)
            if not found["errors"]:
                break
            time.sleep(20)
        counts = {c: sum(e["collection"] == c for e in found["exposures"]) for c in config.COLLECTIONS}
        print(f"{name}: {len(found['exposures'])} exposures {counts} errors {found['errors']}", flush=True)
        if found["errors"]:
            problems.append(f"{name}: search incomplete")
            continue
        for c in config.COLLECTIONS:
            src = config.CACHE_DIR / "search" / f"{c}_{ra:.4f}_{dec:.4f}.json"
            (seed / "search").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, seed / "search" / src.name)
        try:  # Gaia stars for the overlay
            stars = overlays.gaia_stars(ra, dec, FOV)
            (seed / "gaia").mkdir(parents=True, exist_ok=True)
            src = config.find(f"gaia/{ra:.4f}_{dec:.4f}_{FOV:.1f}.json")
            if src.parent != seed / "gaia":
                shutil.copy2(src, seed / "gaia" / src.name)
            print(f"  Gaia: {len(stars['stars'])} stars", flush=True)
        except Exception as exc:
            problems.append(f"{name} Gaia: {type(exc).__name__}: {exc}")
        for band in range(1, 7):
            for mode in ("seasons", "exposures"):
                t0 = time.time()
                try:
                    r = pipeline.build_frames(ra, dec, FOV, band, mode)
                except Exception as exc:
                    problems.append(f"{name} detector {band} {mode}: {type(exc).__name__}: {exc}")
                    continue
                src = pipeline.result_path(r["key"]).parent
                shutil.copytree(src, seed / "frames" / r["key"], dirs_exist_ok=True)
                print(f"  detector {band} {mode:9s}: {len(r['frames']):3d} frames, {len(r['seasons'])} seasons, "
                      f"{time.time() - t0:4.0f} s {r['warnings'] or ''}", flush=True)
                if any("could not be read" in w for w in r["warnings"]):
                    problems.append(f"{name} detector {band} {mode}: {r['warnings']}")
    print("problems:", problems or "none", flush=True)


if __name__ == "__main__":
    main()
