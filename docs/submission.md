# Submission text (draft)

Drafts for the Space Apps project form. Check every line before pasting. Items marked **TO DO** need a person.

## Project name

VERRIER-X

## High-level project summary

VERRIER-X is a public website that turns NASA's SPHEREx sky survey into short movies. You type a sky position or an object name, and it finds every SPHEREx image of that spot, lines them up, and shows how the sky there changes between visits. Stars that are far away stay still; anything nearby that moves, such as a close star, a brown dwarf or an unknown planet in the outer solar system, jumps between visits and catches the eye. Known stars from ESA's Gaia catalogue are marked, so a moving object with no marker stands out as something new. SPHEREx re-observes the whole sky about every six months, so it is a new way to look for moving objects in the infrared, but its images are hard to use directly: each one is a large file, rotated differently, taken at a different wavelength. VERRIER-X hides that work so that anyone with a web browser can search for motion.

## Link to project demo

**TO DO:** public link to the slide deck (at most 7 slides). Test it in a private window.

## Link to final project

https://frontend-ivory-one-19.vercel.app
Code: https://github.com/luvyarana/VERRIER-X

## Detailed project description

WHAT IT DOES
The user enters Right Ascension and Declination (degrees, or hours/degrees with minutes and seconds), or simply an object name, and a field of view from 5 to 60 arcminutes. A name is looked up in SIMBAD, and a fast-moving star is shifted from its year-2000 catalogue position to where it was at the start of 2026. The site then shows every public SPHEREx image of that patch in three ways. "Visits combined" merges all exposures from each SPHEREx visit into one deep frame and blinks between visits. "Difference" subtracts the first visit from each later one, so still stars cancel and a moving object appears as a dark spot next to a bright one. "Every exposure" plays each single exposure as a movie, coloured by visit. Known stars from the European Space Agency's Gaia catalogue are circled at the position Gaia gives for the date of each frame, so a moving object with no circle is something Gaia does not know. The user can switch between the six SPHEREx detectors (0.75 to 5.0 microns). Each frame shows its date, wavelength and every quality flag present, explained in plain words, with a link to the original file. The whole view is stored in the page link, so it can be shared.

HOW IT WORKS
A Python service (FastAPI, Astropy) asks the IRSA image search which exposures contain the position, across SPHEREx Data Release 1 and Quick Release 3. It then reads only the needed rows of each file from the public SPHEREx mirror on Amazon S3 with byte-range requests, about 1 MB out of each 62 MB file. For each cutout it removes the sky background, repairs unusable pixels using the mission's flag bits, and resamples the image onto one north-up grid. Exposures from one visit are combined with a median, which removes cosmic-ray hits and lowers the noise. Frames are rendered with one shared brightness scale and cached. The web page (Next.js, TypeScript) plays them on a canvas with a position marker, scale bar, compass and the Gaia circles.

TESTING
Field stars stay on the same spot to within 0.2 SPHEREx pixels (1.3 arcseconds) across 61 frames. On the challenge's five test targets: Barnard's Star moves 10.1 arcseconds north in one year (predicted 10.2); Epsilon Indi B moves 6.3 arcseconds east-south-east in 1.4 years (predicted 6.8); RW Aurigae and R Draconis stay still. WISE 0855, the coldest known brown dwarf, is invisible in single exposures, but with visits combined a source appears at its predicted position in the 3.8 to 5.0 micron detectors and shifts about 8 arcseconds west in a year, as predicted. A background star lies 4.6 arcseconds away and the two are blended, so we report this as a probable detection, not a confirmed one. Catalogue values, predictions and the full validation record are in the docs folder of the repository: https://github.com/luvyarana/VERRIER-X

LIMITS
Very bright stars are saturated, so their brightness is not reliable. New positions take one to two minutes on the free host, and they depend on NASA's IRSA search being available; the five test targets are stored with the site and always load. In the Difference view, still stars leave small rings. Spectra and shifting frames along a trial motion before combining are not built.

TOOLS AND LANGUAGES
Python, FastAPI, Astropy, reproject, NumPy, SciPy, Pillow; TypeScript, Next.js, React, Tailwind CSS; Render and Vercel for hosting. Code and documentation were written with Claude Code (an AI coding assistant), directed and reviewed by the team.

## Use of AI tools

The code, tests and documentation were written with Claude Code (Anthropic's AI coding assistant), directed and reviewed by the team. This is stated in the repository README, and AI-written commits carry a `Co-Authored-By: Claude` line. The idea and the decisions about what to build are the team's own. No AI-generated images, video or audio are used; all images are made from SPHEREx data. No NASA logos are used.

## NASA data

- SPHEREx Level 2 spectral images, Data Release 1 and Quick Release 3, from the NASA/IPAC Infrared Science Archive (IRSA): https://irsa.ipac.caltech.edu/Missions/spherex.html
- IRSA Simple Image Access service (image search): https://irsa.ipac.caltech.edu/SIA
- SPHEREx data mirror on Amazon S3 (bucket `nasa-irsa-spherex`), part of the Registry of Open Data.
- SPHEREx Quick Release 3 spectral images, DOI 10.26131/IRSA662: https://doi.org/10.26131/IRSA662 (no separate DOI for Data Release 1 was found on the IRSA page on 15 November 2026).

## Space agency partner data and other references

- European Space Agency: Gaia Data Release 3 (star positions and proper motions), https://www.cosmos.esa.int/web/gaia/dr3 , read through the GAVO TAP service, https://dc.g-vo.org/tap
- SIMBAD database and Sesame name resolver, CDS Strasbourg: https://cds.unistra.fr/
- Software: Astropy, reproject, NumPy, SciPy, Pillow, FastAPI, Uvicorn, Next.js, React, Tailwind CSS.
- Challenge page: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- Catalogue sources for the test targets (2MASS, AllWISE, Hipparcos, AAVSO VSX and the papers cited) are listed in `docs/targets.md` §9.

## Before clicking "Submit for Judging"

- [ ] All team members are registered at the same Local Event.
- [ ] Slide link and site link open in a private window without a login.
- [ ] Slides have at most 7 pages and name the team, the members and the challenge.
- [ ] Deadline: Sunday 15 November, 11:59 pm local time.
