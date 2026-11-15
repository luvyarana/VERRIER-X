# VERRIER-X

A web tool for watching the sky change in NASA SPHEREx images.
Built for the NASA Space Apps Challenge 2026: [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/).

Enter a sky position (Right Ascension and Declination) and VERRIER-X plays the SPHEREx images of that patch as a short movie, so that moving and changing objects stand out.

**Live site:** https://frontend-ivory-one-19.vercel.app

Try it on a fast-moving star: [Barnard's Star](https://frontend-ivory-one-19.vercel.app/?ra=269.44627&dec=4.76819&fov=10&band=2).

## What it does

- Takes RA and Dec in degrees or in hours/degrees, minutes and seconds, and a field of view from 5 to 60 arcminutes.
- Or takes an object name (looked up in SIMBAD) and moves a fast star from its catalogue position to where it is today.
- Finds every public SPHEREx exposure of that position (Data Release 1 and Quick Release 3, April 2025 to October 2026).
- Lines the images up north-up on one grid, so stars stay on the same pixel from frame to frame.
- Combines each visit's exposures into one deeper frame and blinks between visits ("Visits combined"), or plays every exposure as a movie coloured by observing season. Anything that jumps between visits has moved.
- Subtracts the first visit from each later one ("Difference"), so still stars cancel and a moving object shows as a dark spot next to a bright one.
- Lets you pick one of the six SPHEREx detectors (0.75 to 5.0 microns) and labels every frame with its date and wavelength.
- Marks known stars from ESA's Gaia DR3 catalogue, each moved to the date of the frame. A fast star's marker travels with it; something that moves with no marker is not in Gaia.
- Lists the quality flags in each frame with what they mean and how much of the field they cover, and links to the original file.
- Keeps the position in the link, so a view can be shared.

## How it works

| Part | Where | Built with |
|---|---|---|
| Web page | `frontend/` | Next.js, TypeScript, Tailwind CSS, HTML canvas |
| Image service | `backend/` | Python, FastAPI, Astropy, reproject, NumPy, Pillow |

1. The backend asks the IRSA image search (SIA2) which exposures contain the position.
2. It reads only the needed part of each file from the SPHEREx mirror on Amazon S3, using byte-range requests. A 10-arcminute cutout is about 1 MB of a 62 MB file.
3. It subtracts the sky background, repairs unusable pixels, and resamples every cutout onto one north-up grid.
4. It renders the frames as PNG images with one shared brightness scale and returns them with their dates, wavelengths and flags.

A new data release is added by editing one list in `backend/app/config.py`. The five challenge test targets ship with the backend as a starter cache (`backend/seed/`), so they load at once.

## Does it work?

See [docs/demo-script.md](docs/demo-script.md) for the five test targets. In short: Barnard's Star and Epsilon Indi B visibly move by the expected amounts; RW Aurigae and R Draconis stay put; WISE 0855 is invisible in single exposures but is probably detected, blended with a background star, once each visit's exposures are combined. The catalogue values and predictions are in [docs/targets.md](docs/targets.md).

More detail: [docs/data-notes.md](docs/data-notes.md) (data and measurements) and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (plan).

## Run it locally

Backend, from `backend/` (needs [uv](https://docs.astral.sh/uv/)):

```
uv sync
uv run uvicorn app.main:app --port 8000
```

Frontend, from `frontend/`:

```
npm install
npm run dev
```

Then open http://localhost:3000. Tests: `uv run pytest` in `backend/`.

## Use of AI tools

The code, tests and documentation in this repository were written with Claude Code (Anthropic's AI coding assistant), directed and reviewed by the team. Commits that contain AI-written work carry a `Co-Authored-By: Claude` line. The idea, the choice of challenge and the decisions about what to build are the team's. No AI-generated images are used; every image shown by the tool is made from SPHEREx data.

## Data credit

This project uses data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.

This research has made use of the NASA/IPAC Infrared Science Archive, which is funded by the National Aeronautics and Space Administration and operated by the California Institute of Technology.

This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia), processed by the Gaia Data Processing and Analysis Consortium (DPAC). The Gaia catalogue is read through the TAP service of the German Astrophysical Virtual Observatory (GAVO).

Object names are resolved with the Sesame service of the Centre de Données astronomiques de Strasbourg (CDS), which queries the SIMBAD database.

Software: Astropy, reproject, NumPy, SciPy, Pillow, FastAPI, Next.js, React, Tailwind CSS.
