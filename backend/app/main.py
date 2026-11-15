"""VERRIER-X backend: SPHEREx image sequences for any sky position.

Run from the backend folder:
    uv run uvicorn app.main:app --reload
"""

import json
import re
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import config, overlays, pipeline
from .archive import ArchiveError

app = FastAPI(title="VERRIER-X", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def _run(key: str, args: tuple) -> None:
    def progress(**update):
        _jobs[key].update(update)

    try:
        result = pipeline.build_frames(*args, progress=progress)
        with _lock:
            if result["complete"]:
                _jobs.pop(key, None)  # now served from the disk cache
            else:
                _jobs[key] = result  # handed out once, then rebuilt on the next call
    except ArchiveError as exc:
        _jobs[key].update(status="error", message=str(exc))
    except Exception as exc:
        _jobs[key].update(status="error", message=f"Something went wrong while building the frames ({type(exc).__name__}).")


@app.get("/api/health")
def health():
    return {"status": "ok", "collections": config.COLLECTIONS, "jobs_running": len(_jobs)}


@app.get("/api/frames")
def frames(
    ra: float = Query(..., ge=0, le=360, description="Right ascension, degrees (ICRS)"),
    dec: float = Query(..., ge=-90, le=90, description="Declination, degrees (ICRS)"),
    fov: float = Query(config.FOV_DEFAULT_ARCMIN, ge=config.FOV_MIN_ARCMIN, le=config.FOV_MAX_ARCMIN,
                       description="Field of view, arcminutes"),
    band: int = Query(2, ge=1, le=6, description="Detector 1-6 (0.75-5.0 microns)"),
    mode: str = Query("exposures", pattern="^(exposures|seasons|difference)$",
                      description="exposures: one frame per exposure; seasons: one combined frame per visit; "
                                  "difference: each later visit minus the first"),
):
    """Frame list for a position. The first call starts the work and returns
    {"status": "working", ...}; repeat the same call until status is "done"."""
    key = pipeline.request_key(ra, dec, fov, band, mode)
    path = config.find(f"frames/{key}/result.json")
    if path:
        return json.loads(path.read_text())
    with _lock:
        job = _jobs.get(key)
        if job and job["status"] != "working":
            del _jobs[key]  # failures and incomplete answers are reported once; the next call tries again
            return job
        if not job:
            job = _jobs[key] = {"status": "working", "key": key, "stage": "queued", "done": 0, "total": 0,
                                "message": "Starting"}
            threading.Thread(target=_run, args=(key, (ra, dec, fov, band, mode)), daemon=True).start()
    return job


@app.get("/api/gaia")
def gaia(
    ra: float = Query(..., ge=0, le=360),
    dec: float = Query(..., ge=-90, le=90),
    fov: float = Query(config.FOV_DEFAULT_ARCMIN, ge=config.FOV_MIN_ARCMIN, le=config.FOV_MAX_ARCMIN),
):
    """Gaia DR3 stars around a position: 2016.0 positions and proper motions (mas/yr)."""
    try:
        return overlays.gaia_stars(ra, dec, fov)
    except ArchiveError as exc:
        raise HTTPException(503, str(exc))


@app.get("/api/frame/{key}/{name}.png")
def frame(key: str, name: str):
    if not re.fullmatch(r"[0-9a-f]{16}", key) or not re.fullmatch(r"\d{3}", name):
        raise HTTPException(404)
    path = config.find(f"frames/{key}/{name}.png")
    if not path:
        raise HTTPException(404)
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=31536000, immutable"})
