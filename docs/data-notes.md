# Data notes

Results of the two data checks (V01 coverage, V02 cutouts), run on 2026-11-14.
Scripts: `scripts/v01_coverage_spike.py`, `scripts/v02_cutout_spike.py`. Raw coverage output: `docs/coverage.json`.

## 1. Which collections to search

| Collection | Dates covered | Use |
|---|---|---|
| `spherex_dr1`, `spherex_dr1_deep` | April 2025 → May 2026 | **Yes.** Data Release 1, reprocessed (file version `l2b-v27`). |
| `spherex_qr3`, `spherex_qr3_deep` | May 2026 → October 2026 | **Yes.** Newest data, same file version. |
| `spherex_qr2`, `spherex_qr2_deep` | April 2025 → July 2026 on S3 | **No.** Older processing; its search returned nothing for the test targets. DR1 replaces it. |

DR1 is not mentioned in the IRSA documentation dated September 2026. It was found by listing the S3 bucket, which also holds an all-sky map at `dr1/hips5_cube/hips_20261026/`.

The "deep" collections cover only the survey's deep fields near the ecliptic poles. R Draconis is in one.

## 2. Coverage of the five test targets

Search radius 0.02°. A season is a run of exposures with no gap longer than 30 days.

| Target | Seasons (number of files) | Total |
|---|---|---|
| Barnard's Star | Aug–Oct 2025 (120), Mar–May 2026 (122), Aug–Sep 2026 (124) | 366 |
| Epsilon Indi B | Apr–Jun 2025 (128), Sep–Nov 2025 (147), Apr–May 2026 (76), Sep–Oct 2026 (120) | 471 |
| WISE 0855 | May 2025 (30), Oct–Dec 2025 (128), Apr–May 2026 (100) | 258 |
| RW Aurigae | Sep 2025 (113), Feb–Mar 2026 (114), Sep 2026 (111) | 338 |
| R Draconis (wide) | May–Jul 2025 (165), Oct 2025–Jan 2026 (214), Apr–May 2026 (48), May–Jul 2026 (127) | 554 |
| R Draconis (deep) | Apr–May 2025 (87), Aug–Nov 2025 (261), Feb–May 2026 (892), Jul–Sep 2026 (738) | 1,978 |

Every target has at least three seasons, so motion and variability can be shown for all five. R Draconis has far more data than the others, so requests need a cap on the number of exposures.

## 3. How to get the pixels

**Chosen route: read directly from the Amazon S3 mirror with byte-range requests.**

- Bucket: `nasa-irsa-spherex` (region `us-east-1`), public, no login.
- An IRSA access URL becomes an S3 URL by swapping the prefix `https://irsa.ipac.caltech.edu/ibe/data/spherex/` for `https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/`.
- The reader fetches each extension's header and then only the rows that contain the cutout. A 10-arcminute cutout needs about 1 MB per extension, not the whole 60–70 MB file.
- Checked: pixels are identical to a full local copy of the file (IMAGE, FLAGS, VARIANCE, ZODI), and the compressed FLAGS path matches astropy's own decoding.

**Why not the IRSA cutout service:** it works, but IRSA returned 502 and 503 errors repeatedly on 14 November, on the cutout service, the image search (SIA) and the table search (TAP). S3 never failed.

**Why not astropy's built-in remote reading:** it took 11–37 seconds per extension, because it reads row by row.

**Speed** (measured from a laptop in India to `us-east-1`):

| Test | Time |
|---|---|
| One 10-arcminute cutout, four extensions | 8–19 s |
| 8 cutouts at once | about 3.3 s each |
| 16 cutouts at once | about 2.3 s each |

Most of this is network distance. A backend hosted in the eastern US should be much faster; this must be re-measured after deployment.

**The search still depends on IRSA.** There is no footprint index on S3. Search results must be cached on disk, and the five test targets must be pre-fetched before judging.

## 4. Two file layouts

| Extension | QR2 (`l2b-v20`) | DR1 and QR3 (`l2b-v27`) |
|---|---|---|
| IMAGE | plain image | plain image |
| FLAGS | plain image | **Rice-compressed table**, one image row per table row |
| VARIANCE | plain image | plain image |
| ZODI | plain image | plain image |
| PSF | cube, 101×101×121 | replaced by **EPSF** table |
| WCS-WAVE | table | table |
| File size | about 71.6 MB | about 62 MB |

The reader finds extensions by name and handles both layouts.

## 5. End-to-end proof: Barnard's Star moves

Six detector-2 exposures per season, 17-pixel cutouts, rough brightness-weighted position of the star.

| Season | Offset east | Offset north |
|---|---|---|
| August 2025 | −5.5″ | −4.1″ |
| March 2026 | −8.2″ | +0.9″ |
| August 2026 | −9.8″ | +6.1″ |

- August 2025 → March 2026: 5.1″ north in 0.56 years, about 10.3″/yr.
- March 2026 → August 2026: 5.2″ north in 0.43 years, about 12.6″/yr.
- Catalogue value: about 10.4″/yr, northward.

The total over one year is 10.2″ north, or about 1.7 pixels. The measurement is rough: scatter between exposures is 1–3″, and the star's core has 4–5 blank (NaN) pixels in every exposure, probably from saturation. The east–west wobble is consistent in size with the star's parallax but was not modelled.

## 6. Things the tool must handle

- **Bright stars have blank cores.** Barnard's Star has NaN pixels at its centre. The display must not show these as black holes.
- **Flag bit 21 ("known source") is set on 96–100% of pixels near Barnard's Star.** That field is crowded. Bit 21 must never be treated as "bad".
- **Positions change.** Search at the star's current position, not its year-2000 catalogue position (Barnard's Star has moved about 4.5 arcminutes).
- **Each exposure is at a different wavelength.** Group frames by detector and label them.
- **IRSA can be down.** Retry, cache, and show a clear message.

## 7. Backend results (V04–V06, 2026-11-15)

Code: `backend/app/`. Tests: `backend/tests/` (16 offline tests). Alignment check: `scripts/v05_alignment_check.py`.

- **Search radius is 0.003°**, so the target itself is inside every exposure returned. This gives fewer files than the 0.02° counts in section 2 (Barnard's Star, detector 2: 61 exposures in 3 seasons).
- **Caching works.** Barnard's Star, 10 arcminutes, detector 2: the first run downloaded every cutout; the repeat run downloaded none and took 1.3 s. Over HTTP a finished request is answered in about 2 ms.
- **First-request time from a laptop in India:** about 40 s for 36–45 exposures. The IRSA search took 12–30 s of that.
- **Alignment:** six field stars near Barnard's Star, 61 frames: 90% of position measurements are within 0.21 native pixels (1.3″) of the star's median position. Target was 0.5 pixels.
- **Motion is visible in the aligned frames:** Barnard's Star moves 9.5″ north between August 2025 and August 2026 (catalogue: about 10.4″/yr).
- **Only IMAGE and FLAGS are read for frames.** ZODI is not read: over a field this small it is flat, and subtracting each frame's median background removes it. This halves the number of requests per cutout.
- **Wavelength** at the target comes from the `WCS-WAVE` table, which is the same for every file of a detector and is read once per detector.
- **Repaired pixels:** TRANSIENT, SUR_ERROR, NONFUNC, MISSING_DATA, HOT, COLD, PHANMISS and SNOWBALL pixels are replaced by the median of their neighbours. OVERFLOW and NONLINEAR pixels (cores of very bright stars) are replaced by their brightest neighbour. OUTLIER is left alone, because a moving object might be flagged as one.
- **An incomplete search is not cached.** If part of the IRSA search fails, the answer is returned with a warning and rebuilt on the next request.
- **Known display problem:** some frames have a bright band across part of the field (seen in one Barnard's Star frame from August 2025). Not yet handled.

## 8. Combined visits (V10, 2026-11-15)

- The API has a second view, `mode=seasons`: all exposures of one visit (same detector) are combined into one frame by taking the median of each pixel. The page calls this "Visits combined" and opens in it by default; "Every exposure" is the original view.
- A combined frame mixes the wavelengths within the detector's range, so it is a broad-band image. Its label gives the date range, the number of exposures and the wavelength range.
- Noise falls roughly with the square root of the number of exposures, and one-off artefacts (cosmic-ray hits, the bright band seen in single frames) drop out.
- Barnard's Star, detector 2: three frames (18, 18 and 25 exposures); the star visibly steps north between them.
- WISE 0855, detector 6: the combined frames are much deeper than single exposures, but the object has not been identified in them.
- The starter cache now holds both views for the five targets: 60 frame sets, 79 MB.
- At most 72 exposures per request are still used, so in the R Draconis deep field a combined frame uses only part of the available data.

## 9. Corrected target positions and WISE 0855 (2026-11-15)

- The quick-pick positions were recomputed for epoch 2026.0 (see `docs/targets.md` §0). The old ones were off by 8.4″ (Barnard's Star), 12.5″ (Epsilon Indi B) and 31.5″ (WISE 0855).
- IRSA's search returned 502 errors while the starter cache was rebuilt, so the exposure lists found at the old positions were reused for the new ones. The positions differ by at most 32″ and each exposure covers 3.5°, so the lists should be the same apart from exposures whose edge falls between the two positions.
- At the corrected position, WISE 0855 shows up in combined visits in detectors 5 and 6 at 10–17σ, moving about 8″ west in a year, blended with a fixed background star 4.6″ away. `docs/evidence/wise0855_detectors.png` shows panels 2.8 arcminutes wide (rows: detector 6, 5, 3; columns: visits in time order). The star is the bright central object in the detector-3 row.
