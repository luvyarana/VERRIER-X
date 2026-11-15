# Submission text (draft)

Drafts for the Space Apps project form. Check every line before pasting. Items marked **TO DO** need a person.

## Project name

VERRIER-X

## High-level project summary

VERRIER-X is a public website that turns NASA's SPHEREx sky survey into short movies. You type a sky position, and it finds every SPHEREx image of that spot, lines them up, and plays them in time order. Stars that are far away stay still; anything nearby that moves, such as a close star, a brown dwarf or an unknown planet in the outer solar system, jumps between visits and catches the eye. SPHEREx re-observes the whole sky about every six months, so it is a new way to look for moving objects in the infrared, but its images are hard to use directly: each one is a large file, rotated differently, taken at a different wavelength. VERRIER-X hides that work so that anyone with a web browser can search for motion.

## Link to project demo

**TO DO:** public link to the slide deck (at most 7 slides). Test it in a private window.

## Link to final project

https://frontend-ivory-one-19.vercel.app
Code: https://github.com/luvyarana/VERRIER-X

## Detailed project description

**What it does.** The user enters Right Ascension and Declination (degrees, or hours/degrees with minutes and seconds) and a field of view from 5 to 60 arcminutes. The site shows a movie of all public SPHEREx exposures of that patch from one detector, with play, pause, step and speed controls. Frames are coloured by observing season, so a jump at a colour change means real motion between visits. Each frame is labelled with its date and exact wavelength, and a side panel shows the quality flags at the centre and a link to the original file. The user can switch between the six detectors (0.75 to 5.0 microns). The position, field of view and detector are stored in the page link, so any view can be shared.

**How it works.** A Python service (FastAPI, Astropy) asks the IRSA image search which exposures contain the position, across SPHEREx Data Release 1 and Quick Release 3. It then reads only the needed rows of each file from the public SPHEREx mirror on Amazon S3 with byte-range requests, about 1 MB out of each 62 MB file. For each cutout it removes the sky background, repairs unusable pixels using the mission's flag bits, and resamples the image onto one north-up grid. Frames are rendered with a single shared brightness scale and cached. The web page (Next.js, TypeScript) loads the frames and plays them on a canvas with a position marker, scale bar and compass.

**Testing.** Field stars stay on the same spot to within 0.2 SPHEREx pixels (1.3 arcseconds) across 61 frames. On the challenge's test targets: Barnard's Star moves 9.9 arcseconds north in one year (catalogue: about 10.4); Epsilon Indi B moves about 4.4 arcseconds per year east and south (catalogue: about 4.7); RW Aurigae and R Draconis stay still; WISE 0855 is too faint to detect. Full notes: `docs/demo-script.md` in the repository.

**Limits.** Very bright stars are saturated, so their brightness is not reliable. New positions take one to two minutes on the free host. Stacking, image differencing, spectra and Gaia overlays were planned but not built.

**Tools and languages.** Python, FastAPI, Astropy, reproject, NumPy, SciPy, Pillow; TypeScript, Next.js, React, Tailwind CSS; Render and Vercel for hosting.

## Use of AI tools

The code, tests and documentation were written with Claude Code (Anthropic's AI coding assistant), directed and reviewed by the team. This is stated in the repository README, and AI-written commits carry a `Co-Authored-By: Claude` line. The idea and the decisions about what to build are the team's own. No AI-generated images, video or audio are used; all images are made from SPHEREx data. No NASA logos are used.

## NASA data

- SPHEREx Level 2 spectral images, Data Release 1 and Quick Release 3, from the NASA/IPAC Infrared Science Archive (IRSA): https://irsa.ipac.caltech.edu/Missions/spherex.html
- IRSA Simple Image Access service (image search): https://irsa.ipac.caltech.edu/SIA
- SPHEREx data mirror on Amazon S3 (bucket `nasa-irsa-spherex`), part of the Registry of Open Data.
- **TO DO:** add the SPHEREx data DOI from the IRSA SPHEREx page.

## Space agency partner data and other references

- No partner-agency data is used in this version.
- Software: Astropy, reproject, NumPy, SciPy, Pillow, FastAPI, Uvicorn, Next.js, React, Tailwind CSS.
- Challenge page: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- **TO DO:** add the catalogue sources used in `docs/targets.md` (SIMBAD, Gaia DR3, AllWISE, AAVSO) once that sheet is filled in.

## Before clicking "Submit for Judging"

- [ ] All team members are registered at the same Local Event.
- [ ] Slide link and site link open in a private window without a login.
- [ ] Slides have at most 7 pages and name the team, the members and the challenge.
- [ ] Deadline: Sunday 15 November, 11:59 pm local time.
