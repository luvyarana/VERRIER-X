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
