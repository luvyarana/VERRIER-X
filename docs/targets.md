# VERRIER-X — Scientific Target Fact Sheets

**Challenge:** NASA Space Apps Challenge 2026 — [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)  
**Lead Contributor / Author:** Sainy (`Sainyy56`), Astronomical Data Scientist & Scientific Validation Engineer  
**Companion Documents:** [docs/demo-script.md](demo-script.md) (Validation Record) | [docs/data-notes.md](data-notes.md) (Archive & Processing Notes) | [docs/target_predictions.json](target_predictions.json) (Machine-Readable Predictions)  
**Calculation Script:** [scripts/calculate_target_predictions.py](../scripts/calculate_target_predictions.py)

---

## 0. Independent recheck and corrections (15 November 2026)

Every 2026.0 position in this sheet was recomputed independently with Astropy (`SkyCoord.apply_space_motion`) from the reference positions and proper motions given below, and compared with where each object actually appears in the SPHEREx frames.

| Target | Finding | Action |
|---|---|---|
| Barnard's Star | The 2026.0 right ascension was typed as 269.443900°; the correct value is 269.446267° (8.5″ further east). Declination was correct. The star's measured position in the frames agrees with the corrected value. | Corrected below. |
| Epsilon Indi B | The 2026.0 right ascension was typed as 331.090354°; the correct value is 331.096330° (11.8″ further east). Declination was correct. The object was measured 11–16″ east of the old marker, which confirms the corrected value. | Corrected below. |
| WISE 0855 | The 2026.0 position here (133.7597°, −7.2422°) is right. The app's old quick-pick was 31.5″ too far east because it assumed the wrong epoch for the catalogue position. | Quick-pick corrected. At the corrected position a source is detected; see §6.3. |
| RW Aurigae | Correct. | None. |
| R Draconis | The 2026.0 right ascension was typed as 248.161801°; the correct value is 248.167119°. The star moves 0.02″ per year, so it cannot have shifted 8″. The old quick-pick was within 0.5″. | Corrected below. |

Cause: `scripts/calculate_target_predictions.py` moved every target forward by a fixed 26 years, whatever epoch its tabulated position was for, and three right ascensions in this sheet did not match the script's own output. The script now uses each position's own epoch, and `docs/target_predictions.json` has been regenerated. The W2 flux of WISE 0855 was also wrong by a factor of ten (see §6.3).

The quick-pick buttons and the starter cache now use the corrected 2026.0 positions:

| Target | RA (deg) | Dec (deg) |
|---|---|---|
| Barnard's Star | 269.44627 | +4.76819 |
| Epsilon Indi B | 331.09636 | −56.80058 |
| WISE 0855 | 133.75969 | −7.24223 |
| RW Aurigae | 76.9563 | +30.4014 |
| R Draconis | 248.1675 | +66.7550 |

---

## 1. Purpose

The NASA Space Apps Challenge specification instructs teams to test their interactive SPHEREx viewer on five designated astronomical targets:
1. **Barnard's Star** (extreme proper-motion M-dwarf)
2. **Epsilon Indi B** (nearby binary brown-dwarf system)
3. **WISE 0855** (ultracool, faint nearby substellar Y-dwarf)
4. **RW Aurigae** (classical T Tauri eruptive/obscuration variable star)
5. **R Draconis** (luminous Mira-type pulsating AGB variable giant)

These five targets serve as scientific benchmarks covering three distinct astrophysical test regimes:
- **Astrometric displacement:** Validates that SPHEREx's multi-epoch exposures correctly reveal real stellar proper motion across 6-month survey cadence cycles (Barnard's Star: $\sim 10.39$″/yr; Epsilon Indi B: $\sim 4.68$″/yr; WISE 0855: $\sim 8.15$″/yr).
- **Astrometric stability:** Proves that distant background sources remain fixed to subpixel accuracy ($< 0.2$ pixels) without false motion artifacts (RW Aurigae and R Draconis move $< 0.022$″/yr, or $< 0.004$ native pixels/yr).
- **Photometric and detection limits:** Tests how SPHEREx's narrow-band linear variable filters (LVF) handle severe core saturation in bright targets ($K < 8$), irregular circumstellar dust extinction, large-amplitude stellar pulsations, and non-detection thresholds for extremely faint mid-infrared sources ($W2 \sim 14$ mag).

---

## 2. Methodology

### 2.1 Catalogue Selection & Identifier Resolution
Primary astrometric and photometric parameters were compiled from authoritative astronomical catalogues:
- **Gaia DR3** (I/355): Fundamental optical astrometry ($\alpha, \delta, \mu_{\alpha*}, \mu_{\delta}, \varpi$, radial velocity) at reference epoch J2016.0 for optical targets (Barnard's Star, RW Aurigae, R Draconis).
- **Hipparcos Re-reduction** (I/311, van Leeuwen 2007): Historical reference astrometry at epoch J1991.25.
- **SIMBAD / VizieR**: Cross-identifications, coordinate transformations, and bibliography verification.
- **Luhman (2014) & Kirkpatrick et al. (2021)**: Peer-reviewed discovery and precision Spitzer/JWST astrometric solutions for brown dwarf targets (WISE 0855 and Epsilon Indi B) not present or poorly resolved in optical catalogues.
- **2MASS Point Source Catalog** (II/246): Near-infrared $J, H, K_s$ photometry (1.25, 1.65, 2.16 µm).
- **AllWISE Source Catalog** (II/328): Mid-infrared $W1, W2$ photometry (3.4, 4.6 µm).
- **AAVSO International Variable Star Index (VSX)**: Classification, pulsation periods, and calibrated magnitude ranges for variable stars.

### 2.2 Coordinate Reference Frames & Epoch Propagation
All sky coordinates are referenced to the **International Celestial Reference System (ICRS)**.  
Because nearby stars possess substantial proper motion, coordinates are valid only at their specific observation epoch:
- **Equinox J2000.0** defines the celestial orientation of the coordinate grid.
- **Epoch** defines the exact moment in time when the object was located at the specified position.

To propagate coordinates from catalogue reference epoch $t_{\text{ref}}$ to another epoch $t$ (such as J2000.0 or the SPHEREx mission epoch 2026.0), rigorous astrometric propagation is applied:
$$\Delta t = t - t_{\text{ref}} \quad (\text{Julian years})$$
$$\delta(t) = \delta(t_{\text{ref}}) + \frac{\mu_{\delta} \times \Delta t}{3600 \times 1000} \quad (\text{degrees})$$
$$\alpha(t) = \alpha(t_{\text{ref}}) + \frac{(\mu_{\alpha} \cos\delta) \times \Delta t}{3600 \times 1000 \times \cos(\delta_{\text{mid}})} \quad (\text{degrees})$$
where $\mu_{\alpha*} = \mu_{\alpha}\cos\delta$ is the proper motion component along RA in mas/yr, and $\mu_{\delta}$ is the declination component in mas/yr.

### 2.3 SPHEREx Pixel Scale & Grid Resampling
- **Native SPHEREx detector pixel scale:** **$1\text{ pixel} = 6.14\text{ arcseconds}$**.
- **Viewer Display Grid:** To prevent spatial aliasing, `backend/app/align.py` resamples images onto an oversampled north-up, east-left grid with an oversampling factor of 3 at a 10-arcminute field of view, yielding:
  $$\text{Display grid scale} = \frac{6.14\text{ arcsec}}{3} = 2.0467\text{ arcsec/pixel}$$
- Both scales are explicitly reported: native detector pixels ($6.14$″/px) and viewer display pixels ($2.05$″/px).

### 2.4 Linear Proper-Motion Prediction
For two observation seasons with median timestamps $t_1$ and $t_2$, the elapsed time is:
$$\Delta t_{\text{years}} = \frac{\text{MJD}_2 - \text{MJD}_1}{365.25}$$
The displacement components on the sky (measured in arcseconds) are:
$$\Delta \text{East}_{\text{pm}} = (\mu_{\alpha*} / 1000.0) \times \Delta t_{\text{years}}$$
$$\Delta \text{North}_{\text{pm}} = (\mu_{\delta} / 1000.0) \times \Delta t_{\text{years}}$$
The total linear displacement and position angle (PA, degrees East of North) are:
$$\Delta \theta_{\text{pm}} = \sqrt{(\Delta \text{East}_{\text{pm}})^2 + (\Delta \text{North}_{\text{pm}})^2}$$
$$\text{PA} = \text{atan2}(\Delta \text{East}_{\text{pm}}, \Delta \text{North}_{\text{pm}}) \pmod{360^\circ}$$
$$\Delta \text{pixels}_{\text{native}} = \frac{\Delta \theta_{\text{pm}}}{6.14}, \quad \Delta \text{pixels}_{\text{display}} = \frac{\Delta \theta_{\text{pm}}}{2.0467}$$

### 2.5 Parallax-Aware Prediction & SPHEREx Geometry
Because nearby stars lie within a few parsecs of Earth, their apparent positions also reflect annual parallax wobbles caused by the observer's orbital motion around the Solar System barycenter.
SPHEREx operates in a Sun-synchronous low Earth orbit at $\sim 650\text{ km}$ altitude. Because the orbital radius of SPHEREx around Earth ($\sim 7000\text{ km} \approx 4.7 \times 10^{-5}\text{ AU}$) is negligible compared to Earth's orbit around the Sun ($1\text{ AU}$), the geocentric position serves as an exact model for SPHEREx to within $< 0.001$ pixels ($< 0.025\text{ mas}$).

The parallax displacement vector on the sky is calculated using standard astrometric parallax factors:
$$\Delta \text{East}_{\text{plx}} = \varpi \cdot P_{\alpha}(t) = \varpi \cdot [X_{\text{AU}}(t) \sin\alpha - Y_{\text{AU}}(t) \cos\alpha]$$
$$\Delta \text{North}_{\text{plx}} = \varpi \cdot P_{\delta}(t) = \varpi \cdot [X_{\text{AU}}(t) \cos\alpha \sin\delta + Y_{\text{AU}}(t) \sin\alpha \sin\delta - Z_{\text{AU}}(t) \cos\delta]$$
where $\varpi$ is the trigonometric parallax in arcseconds, and $(X_{\text{AU}}, Y_{\text{AU}}, Z_{\text{AU}})$ is the Earth's barycentric position vector in astronomical units.  
The net apparent displacement between Season 1 and Season 2 is:
$$\Delta \text{East}_{\text{apparent}} = \Delta \text{East}_{\text{pm}} + (\Delta \text{East}_{\text{plx}, 2} - \Delta \text{East}_{\text{plx}, 1})$$
$$\Delta \text{North}_{\text{apparent}} = \Delta \text{North}_{\text{pm}} + (\Delta \text{North}_{\text{plx}, 2} - \Delta \text{North}_{\text{plx}, 1})$$
$$\Delta \theta_{\text{apparent}} = \sqrt{(\Delta \text{East}_{\text{apparent}})^2 + (\Delta \text{North}_{\text{apparent}})^2}$$

---

## 3. Master Summary Table

| Target | RA (J2000) | Dec (J2000) | Total PM (″/yr) | Parallax (mas) | Dist (pc) | Photometry Summary | Expected Behaviour |
|---|---|---|---|---|---|---|---|
| **Barnard's Star** | `17h 57m 48.498s` (269.452075°) | `+04° 41′ 36.11″` (+4.693364°) | $10.3934 \pm 0.0004$ | $546.98 \pm 0.40$ | $1.83$ | $J=5.24, H=4.83, K=4.52$ | Saturated core; moves northward by $\sim 1.67$ native px/yr ($5.0$ disp px) with measurable E–W parallax swing. |
| **Epsilon Indi B** | `22h 04m 10.520s` (331.043833°) | `-56° 46′ 58.00″` (-56.782778°) | $4.6842 \pm 0.0042$ | $270.66 \pm 0.69$ | $3.70$ | $J=11.91, H=11.31, K=11.21$ | Tight binary (Ba+Bb) unresolved by SPHEREx; moves southeast by $\sim 0.76$ native px/yr ($2.3$ disp px). |
| **WISE 0855** | `08h 55m 10.832s` (133.795131°) | `-07° 14′ 42.53″` (-7.245146°) | $8.1515 \pm 0.0013$ | $439.00 \pm 2.40$ | $2.28$ | $J\approx 25.0, W1=17.8, W2=14.0$ | Coldest known brown dwarf ($T\approx 250\text{ K}$). Invisible in single exposures; **probably detected** in combined visits at 3.8–5.0 µm, blended with a background star (§6.3). |
| **RW Aurigae** | `05h 07m 49.570s` (76.956542°) | `+30° 24′ 05.20″` (+30.401444°) | $0.0216 \pm 0.0028$ | $6.406 \pm 0.044$ | $156.1$ | $V=8.5-15.0, J=8.38, K=7.02$ | Classical T Tauri star with irregular dimmings; stationary ($< 0.005$ px/yr); saturated core in Band 2. |
| **R Draconis** | `16h 32m 40.230s` (248.167625°) | `+66° 45′ 17.90″` (+66.754972°) | $0.0219 \pm 0.0007$ | $1.30 \pm 0.66$ | $\sim 770$ | $V=6.7-13.2, K\approx 3.85$ | Mira pulsating giant ($P=245.6\text{ d}$); stationary ($< 0.005$ px/yr); heavily saturated core wanders 3–6″ artificially. |

---

## 4. Target 1 — Barnard's Star

### 4.1 Basic Identifiers & Reference Astrometry
- **Catalogue Identifier:** Gaia DR3 4472832130942575872 (ICRS, epoch J2016.0)
- **Cross Identifiers:** GJ 699, HIP 87937, BD+04 3561, 2MASS J17574849+0441405
- **Coordinates (Equinox J2000, Epoch J2000.0):**
  - Sexagesimal: `17h 57m 48.498s` / `+04° 41′ 36.11″`
  - Decimal: $\alpha = 269.452075^\circ, \quad \delta = +4.693364^\circ$
- **Gaia DR3 Coordinates (Epoch J2016.0):**
  - $\alpha = 269.448503^\circ, \quad \delta = +4.739410^\circ$
- **Propagated Coordinates (Epoch 2026.0):**
  - Sexagesimal: `17h 57m 47.104s` / `+04° 46′ 05.50″`
  - Decimal: $\alpha = 269.446267^\circ, \quad \delta = +4.768194^\circ$
- **Quick-Pick App Coordinates:** now $\alpha = 269.44627^\circ, \delta = +4.76819^\circ$ (the 2026.0 position). The earlier quick-pick ($269.4486^\circ, +4.7685^\circ$) was $8.4$″ east of it.
- **Proper Motion:**
  - $\mu_{\alpha*} = -801.55 \pm 0.38\text{ mas/yr}$ (westward)
  - $\mu_{\delta} = +10362.39 \pm 0.35\text{ mas/yr}$ (northward)
  - $\mu_{\text{total}} = 10.3934 \pm 0.0004\text{ ″/yr}$
  - Position Angle ($\text{PA}$): $355.58^\circ$ (almost due North, $4.42^\circ$ West of North)
- **Parallax:** $\varpi = 546.98 \pm 0.40\text{ mas}$ ($0.5470\text{ ″}$), Distance $d = 1.828 \pm 0.001\text{ pc}$ ($5.963\text{ ly}$)
- **Radial Velocity:** $v_r = -110.5 \pm 0.5\text{ km/s}$

### 4.2 Infrared Photometry
| Band | Magnitude | Uncertainty | Source Catalogue | Photometric Notes |
|---|---|---|---|---|
| **$J$ (1.25 µm)** | 5.244 | $\pm 0.023$ | 2MASS PSC | Saturated core in deep integrations |
| **$H$ (1.65 µm)** | 4.828 | $\pm 0.033$ | 2MASS PSC | Saturated core in deep integrations |
| **$K_s$ (2.16 µm)** | 4.524 | $\pm 0.020$ | 2MASS PSC | Saturated core in deep integrations |
| **$W1$ (3.4 µm)** | 4.386 | $\pm 0.040$ | AllWISE (deblended) | Saturated in raw survey pipeline |
| **$W2$ (4.6 µm)** | 4.150 | $\pm 0.050$ | AllWISE (re-reduced) | Saturated in raw survey pipeline (limit $\sim 6.7$ mag) |

### 4.3 Seasonal Movement Predictions (Detector 2: 1.10–1.62 µm)
Actual observing dates extracted from `backend/seed/frames/01bea760d7549fb0/result.json`:
- **Season 0:** Median UTC: `2025-08-27T06:38:47` (MJD 60914.277, 18 frames)
- **Season 1:** Median UTC: `2026-03-15T07:20:59` (MJD 61114.306, 18 frames)
- **Season 2:** Median UTC: `2026-08-21T15:35:58` (MJD 61273.650, 25 frames)

| Season Interval | Dates (UTC) | $\Delta t$ (yr) | Linear PM Shift (″) | Linear Pixels (Native/Disp) | Apparent Shift w/ Plx (″) | Apparent Pixels (Native/Disp) | Pred Direction ($\text{PA}$) |
|---|---|---|---|---|---|---|---|
| **Season 0 → Season 1** | 2025-08-27 → 2026-03-15 | 0.548 | 5.696″ | 0.928 / 2.783 | 5.572″ | 0.907 / 2.723 | 6.2° (NNE) |
| **Season 1 → Season 2** | 2026-03-15 → 2026-08-21 | 0.436 | 4.531″ | 0.738 / 2.214 | 4.874″ | 0.794 / 2.381 | 343.7° (NNW) |
| **Total Baseline (S0 → S2)** | **2025-08-27 → 2026-08-21** | **0.984** | **10.227″** | **1.666 / 4.997** | **10.248″** | **1.669 / 5.007** | **355.7° (N)** |

*Parallax contribution breakdown:*
- Season 0 → Season 1: $\Delta \text{East}_{\text{plx}} = +1.039$″, $\Delta \text{North}_{\text{plx}} = -0.139$″. The linear westward PM ($-0.439$″) is overcome by eastward parallax wobble ($+1.039$″), causing the star to drift slightly East ($+0.60$″).
- Season 1 → Season 2: $\Delta \text{East}_{\text{plx}} = -1.015$″, $\Delta \text{North}_{\text{plx}} = +0.161$″. The star swings strongly West ($-1.36$″ net).

**What a viewer should expect:**
Bright red dwarf, immediately visible in all frames. Steps visibly northward by $\sim 1.7$ native pixels (5 display pixels) between August 2025 and August 2026 while background stars stay pinned in place; an East–West wobble of $\sim 2$ arcseconds between August and March reflects the star's parallax.

---

## 5. Target 2 — Epsilon Indi B

### 5.1 Basic Identifiers & Reference Astrometry
- **Catalogue Identifier:** SIMBAD: `eps Ind B` (resolved components: `eps Ind Ba` and `eps Ind Bb`)
- **Cross Identifiers:** 2MASS J22041052-5646577, WDS J22033-5647BC, HD 209100B
- **Coordinates (Equinox J2000, Epoch J2000.0):**
  - Sexagesimal: `22h 04m 10.520s` / `-56° 46′ 58.00″`
  - Decimal: $\alpha = 331.043833^\circ, \quad \delta = -56.782778^\circ$
- **Propagated Coordinates (Epoch 2026.0):**
  - Sexagesimal: `22h 04m 23.119s` / `-56° 48′ 02.14″`
  - Decimal: $\alpha = 331.096330^\circ, \quad \delta = -56.800594^\circ$
- **Quick-Pick App Coordinates:** now $\alpha = 331.09636^\circ, \delta = -56.80058^\circ$ (the 2026.0 position). The earlier quick-pick ($331.0900^\circ, -56.8010^\circ$) was $12.5$″ west of it.
- **Proper Motion:**
  - $\mu_{\alpha*} = +3981.98 \pm 4.20\text{ mas/yr}$ (eastward)
  - $\mu_{\delta} = -2466.83 \pm 4.10\text{ mas/yr}$ (southward)
  - $\mu_{\text{total}} = 4.6842 \pm 0.0042\text{ ″/yr}$
  - Position Angle ($\text{PA}$): $121.78^\circ$ (East-Southeast)
- **Parallax:** $\varpi = 270.66 \pm 0.69\text{ mas}$ ($0.2707\text{ ″}$), Distance $d = 3.695 \pm 0.009\text{ pc}$ ($12.05\text{ ly}$)
- **System Configuration:**
  - Binary brown dwarf pair: **Ba** (spectral type T1V, $M \approx 47\text{ M}_{\text{Jup}}$) and **Bb** (spectral type T6V, $M \approx 28\text{ M}_{\text{Jup}}$).
  - Mutual separation: $0.66\text{″} - 0.73\text{″}$ (semi-major axis $\sim 2.5\text{ AU}$, orbital period $\sim 11.2\text{ yr}$). Unresolved by SPHEREx ($6.14$″ pixels).
  - Separation from primary star $\varepsilon$ Indi A: $402\text{″}$ (6.7 arcminutes, projected separation $\sim 1460\text{ AU}$).

### 5.2 Infrared Photometry
| Band | Magnitude | Uncertainty | Source Catalogue | Photometric Notes |
|---|---|---|---|---|
| **$J$ (1.25 µm)** | 11.91 | $\pm 0.03$ | 2MASS PSC (combined) | Resolved in NIR: Ba = 12.29, Bb = 13.22 |
| **$H$ (1.65 µm)** | 11.31 | $\pm 0.03$ | 2MASS PSC (combined) | Resolved in NIR: Ba = 11.51, Bb = 13.06 |
| **$K_s$ (2.16 µm)** | 11.21 | $\pm 0.04$ | 2MASS PSC (combined) | Resolved in NIR: Ba = 11.35, Bb = 13.34 |
| **$W1$ (3.4 µm)** | 11.17 | $\pm 0.03$ | AllWISE (combined) | High SNR point source |
| **$W2$ (4.6 µm)** | 10.63 | $\pm 0.03$ | AllWISE (combined) | Strong methane absorption |

### 5.3 Seasonal Movement Predictions (Detector 3: 1.62–2.42 µm)
Actual observing dates extracted from `backend/seed/frames/4b2e67c61057a950/result.json`:
- **Season 0:** Median UTC: `2025-04-30T02:06:28` (MJD 60795.088, 18 frames)
- **Season 1:** Median UTC: `2025-06-10T04:32:08` (MJD 60836.189, 2 frames)
- **Season 2:** Median UTC: `2025-10-01T00:02:04` (MJD 60949.001, 17 frames)
- **Season 3:** Median UTC: `2026-04-29T08:50:04` (MJD 61159.368, 9 frames)
- **Season 4:** Median UTC: `2026-09-26T08:49:50` (MJD 61309.368, 26 frames)

| Season Interval | Dates (UTC) | $\Delta t$ (yr) | Linear PM Shift (″) | Linear Pixels (Native/Disp) | Apparent Shift w/ Plx (″) | Apparent Pixels (Native/Disp) | Pred Direction ($\text{PA}$) |
|---|---|---|---|---|---|---|---|
| **Season 0 → Season 1** | 2025-04-30 → 2025-06-10 | 0.113 | 0.527″ | 0.086 / 0.258 | 0.468″ | 0.076 / 0.229 | 108.1° (ESE) |
| **Season 1 → Season 2** | 2025-06-10 → 2025-10-01 | 0.309 | 1.447″ | 0.236 / 0.707 | 1.725″ | 0.281 / 0.843 | 109.5° (ESE) |
| **Season 2 → Season 3** | 2025-10-01 → 2026-04-29 | 0.576 | 2.698″ | 0.439 / 1.318 | 2.569″ | 0.418 / 1.255 | 132.6° (SE) |
| **Season 3 → Season 4** | 2026-04-29 → 2026-09-26 | 0.411 | 1.924″ | 0.313 / 0.940 | 2.126″ | 0.346 / 1.039 | 108.8° (ESE) |
| **Total Baseline (S0 → S4)** | **2025-04-30 → 2026-09-26** | **1.408** | **6.595″** | **1.074 / 3.222** | **6.774″** | **1.095 / 3.310** | **117.7° (ESE)** |

**What a viewer should expect:**
Clean, isolated point source of magnitude $\sim 11.2$ in detector 3, completely unresolved as a binary; steps steadily towards the east-southeast by $1.1$ native pixels ($3.3$ display pixels) across 1.4 years without core saturation.

---

## 6. Target 3 — WISE 0855 (WISE J085510.83−071442.5)

### 6.1 Basic Identifiers & Reference Astrometry
- **Catalogue Identifier:** WISE J085510.83-071442.5
- **Cross Identifiers:** WISE 0855-0714
- **Discovery Reference:** Luhman (2014, *Astrophysical Journal Letters*, 786:L18)
- **High-Precision Astrometric Solution:** Kirkpatrick et al. (2021, *ApJS*, 253:7)
- **Coordinates (Equinox J2000, Epoch J2010.42):**
  - Sexagesimal: `08h 55m 10.832s` / `-07° 14′ 42.53″`
  - Decimal: $\alpha = 133.795131^\circ, \quad \delta = -7.245146^\circ$
- **Propagated Coordinates (Epoch 2026.0):**
  - Sexagesimal: `08h 55m 02.326s` / `-07° 14′ 32.04″`
  - Decimal: $\alpha = 133.759690^\circ, \quad \delta = -7.242233^\circ$
- **Quick-Pick App Coordinates:** now $\alpha = 133.75969^\circ, \delta = -7.24223^\circ$ (the 2026.0 position). The earlier quick-pick ($133.7685^\circ, -7.2429^\circ$) was $31.5$″ east of it, because the catalogue position was assumed to be for 2014 rather than 2010.42.
- **Proper Motion:**
  - $\mu_{\alpha*} = -8123.7 \pm 1.3\text{ mas/yr}$ (westward)
  - $\mu_{\delta} = +673.2 \pm 1.3\text{ mas/yr}$ (northward)
  - $\mu_{\text{total}} = 8.1515 \pm 0.0013\text{ ″/yr}$
  - Position Angle ($\text{PA}$): $274.73^\circ$ (almost due West, $4.73^\circ$ North of West)
- **Parallax:** $\varpi = 439.00 \pm 2.40\text{ mas}$ ($0.4390\text{ ″}$), Distance $d = 2.278 \pm 0.012\text{ pc}$ ($7.43\text{ ly}$)
- **Physical Nature:** Sub-stellar Y-dwarf ($T_{\text{eff}} \approx 250\text{ K} = -23^\circ\text{C}$, $M \approx 3-10\text{ M}_{\text{Jup}}$). Fourth closest system to the Sun.

### 6.2 Infrared Photometry
| Band | Magnitude | Uncertainty | Source Catalogue | Photometric Notes |
|---|---|---|---|---|
| **$J$ (1.25 µm)** | 25.0 | $\pm 0.5$ | HST WFC3 (F110W) | Not detected in 2MASS (limit $\sim 16$) |
| **$H$ (1.65 µm)** | 23.8 | $\pm 0.3$ | VLT HAWK-I | Not detected in 2MASS (limit $\sim 15$) |
| **$K_s$ (2.16 µm)** | $> 20.0$ | upper limit | Deep Keck/VLT | Deep absorption by $\text{CH}_4$, $\text{H}_2$, and $\text{H}_2\text{O}$ |
| **$W1$ (3.4 µm)** | 17.82 | $\pm 0.20$ | AllWISE / Spitzer | Severe molecular absorption; contaminated in raw WISE |
| **$W2$ (4.6 µm)** | 13.97 | $\pm 0.05$ | AllWISE / NEOWISE | Detected in broad $4.5–5.0$ µm thermal window |

### 6.3 Detection in SPHEREx at the corrected position (rechecked 15 November 2026)

The first test of this target found nothing, because the app's marker was 31.5″ east of the object. At the corrected 2026.0 position, with each visit's exposures combined (median), a source is present in the two longest-wavelength detectors:

| Detector | Visit | Exposures | Peak within 16″ | Position of peak (east, north of 2026.0 position) |
|---|---|---|---|---|
| 6 (4.42–5.00 µm) | May 2025 | 3 | 4σ | not significant |
| 6 | Nov–Dec 2025 | 21 | 12σ | 0.0″, 0.0″ |
| 6 | Apr–May 2026 | 21 | 17σ | −2.0″, 0.0″ |
| 5 (3.82–4.42 µm) | May 2025 | 8 | 10σ | +6.1″, 0.0″ |
| 5 | Nov 2025 | 19 | 10σ | +2.0″, 0.0″ |
| 5 | Dec 2025 | 6 | 10σ | +2.0″, 0.0″ |
| 5 | May 2026 | 15 | 15σ | −2.0″, 0.0″ |

In detector 5 the peak moves about 8″ west in one year. WISE 0855 is predicted to move 7.9″ west in that time.

**Caution: this is a probable detection, not a clean one.** A background star sits 4.6″ from the 2026.0 position (4.1″ west, 2.0″ north). It is bright and does not move in detector 3 (1.62–2.42 µm), where WISE 0855 is invisible. In detectors 5 and 6 the two are blended: the source looks elongated to the east in 2025 and round by May 2026, as expected if a moving object is closing on a fixed star. The westward shift of the peak and the excess brightness at 4.4–5.0 µm point to WISE 0855, but the two have not been separated, and no photometry has been done.

Corrections to the earlier text of this section: a W2 magnitude of 13.97 corresponds to about 0.44 mJy, not 0.04 mJy; and the sensitivity limits quoted earlier (12.5 and 13.8 mag) were not taken from a SPHEREx reference and have been removed.

### 6.4 Seasonal Movement Predictions (Detector 6: 4.42–5.00 µm)
Observed epochs extracted from `backend/seed/frames/74bd1e1499d2b8d3/result.json`:
- **Season 0:** Median UTC: `2025-05-05T16:51:08` (MJD 60800.702, 3 frames)
- **Season 1:** Median UTC: `2025-11-14T12:10:27` (MJD 60993.507, 21 frames)
- **Season 2:** Median UTC: `2026-04-26T02:04:05` (MJD 61156.086, 21 frames)

| Season Interval | Dates (UTC) | $\Delta t$ (yr) | Linear PM Shift (″) | Linear Pixels (Native/Disp) | Apparent Shift w/ Plx (″) | Apparent Pixels (Native/Disp) | Pred Direction ($\text{PA}$) |
|---|---|---|---|---|---|---|---|
| **Season 0 → Season 1** | 2025-05-05 → 2025-11-14 | 0.528 | 4.303″ | 0.701 / 2.102 | 5.161″ | 0.841 / 2.522 | 276.9° (W) |
| **Season 1 → Season 2** | 2025-11-14 → 2026-04-26 | 0.445 | 3.628″ | 0.591 / 1.773 | 2.780″ | 0.453 / 1.358 | 271.4° (W) |
| **Total Baseline (S0 → S2)** | **2025-05-05 → 2026-04-26** | **0.973** | **7.931″** | **1.292 / 3.875** | **7.940″** | **1.293 / 3.880** | **275.0° (W)** |

**What a viewer should expect:**
Nothing in single exposures. In the "Visits combined" view with the 4.42–5.00 µm or 3.82–4.42 µm detector, a faint source appears at the marker and shifts west between visits. It is blended with a fixed background star 4.6″ away, so treat it as a probable detection (§6.3).

---

## 7. Target 4 — RW Aurigae

### 7.1 Basic Identifiers & Reference Astrometry
- **Catalogue Identifier:** Gaia DR3 156430822114424576 (RW Aur A)
- **Cross Identifiers:** RW Aur, HD 244615, HIP 25437, AAVSO 0502+30
- **Coordinates (Equinox J2000, Epoch J2016.0):**
  - Sexagesimal: `05h 07m 49.570s` / `+30° 24′ 05.20″`
  - Decimal: $\alpha = 76.956542^\circ, \quad \delta = +30.401444^\circ$
- **Propagated Coordinates (Epoch 2026.0):**
  - Sexagesimal: `05h 07m 49.576s` / `+30° 24′ 04.99″`
  - Decimal: $\alpha = 76.956565^\circ, \quad \delta = +30.401387^\circ$
- **Quick-Pick App Coordinates:** $\alpha = 76.9563^\circ, \delta = +30.4014^\circ$ (coincident within $0.8$″).
- **Proper Motion:**
  - $\mu_{\alpha*} = +7.23 \pm 3.81\text{ mas/yr}$
  - $\mu_{\delta} = -20.33 \pm 2.23\text{ mas/yr}$
  - $\mu_{\text{total}} = 0.0216 \pm 0.0028\text{ ″/yr}$ ($21.58\text{ mas/yr}$)
  - Position Angle ($\text{PA}$): $160.43^\circ$ (South-Southeast)
- **Parallax:** $\varpi = 6.406 \pm 0.044\text{ mas}$ ($0.0064\text{ ″}$), Distance $d = 156.1 \pm 1.1\text{ pc}$ ($509\text{ ly}$)
- **System Configuration:** Binary classical T Tauri system (A + B, separation $1.45$″, common proper motion in Taurus-Auriga star-forming complex).

### 7.2 Variable Star Properties (AAVSO VSX)
- **Variability Class:** **INT** (RW Aurigae-type young eruptive / circumstellar obscuration variable)
- **Periodicity:** **Irregular / Non-periodic**. AAVSO VSX notes a short rotational period of $2.64\text{ days}$, but deep photometric dimmings are irregular, lasting months to years.
- **Visual Range:** $8.5 - 15.0\text{ V}$ (amplitude up to $6.5\text{ mag}$ in optical).
- **Physical Mechanism:** Episodic occultation of the primary star by dense circumstellar dust clumps within a misaligned tidal bridge formed by ongoing dynamical flyby interactions with companion RW Aur B.

### 7.3 Infrared Photometry
| Band | Magnitude | Uncertainty | Source Catalogue | Photometric Notes |
|---|---|---|---|---|
| **$J$ (1.25 µm)** | 8.384 | $\pm 0.024$ | 2MASS PSC | CTTS accretion disk emission |
| **$H$ (1.65 µm)** | 7.621 | $\pm 0.031$ | 2MASS PSC | Strong near-infrared emission |
| **$K_s$ (2.16 µm)** | 7.022 | $\pm 0.021$ | 2MASS PSC | Infrared excess from inner dust rim |
| **$W1$ (3.4 µm)** | 6.251 | $\pm 0.040$ | AllWISE | Circumstellar thermal emission |
| **$W2$ (4.6 µm)** | 5.234 | $\pm 0.035$ | AllWISE | Saturated in raw uncorrected pipeline |

### 7.4 Seasonal Movement Predictions (Detector 2: 1.10–1.62 µm)
Observed epochs extracted from `backend/seed/frames/858513467d4d0c4f/result.json`:
- **Season 0:** Median UTC: `2025-09-09T20:12:43` (MJD 60927.842, 18 frames)
- **Season 1:** Median UTC: `2026-03-05T05:08:13` (MJD 61104.214, 19 frames)
- **Season 2:** Median UTC: `2026-09-13T13:41:02` (MJD 61296.570, 18 frames)

| Season Interval | Dates (UTC) | $\Delta t$ (yr) | Linear PM Shift (″) | Linear Pixels (Native/Disp) | Apparent Shift w/ Plx (″) | Apparent Pixels (Native/Disp) | Pred Direction ($\text{PA}$) |
|---|---|---|---|---|---|---|---|
| **Season 0 → Season 1** | 2025-09-09 → 2026-03-05 | 0.483 | 0.010″ | 0.002 / 0.005 | 0.016″ | 0.003 / 0.008 | 118.3° |
| **Season 1 → Season 2** | 2026-03-05 → 2026-09-13 | 0.527 | 0.011″ | 0.002 / 0.006 | 0.014″ | 0.002 / 0.007 | 217.0° |
| **Total Baseline (S0 → S2)** | **2025-09-09 → 2026-09-13** | **1.010** | **0.022″** | **0.004 / 0.011** | **0.022″** | **0.004 / 0.011** | **160.4°** |

**What a viewer should expect:**
Bright young star pinned firmly to the center marker; shows zero detectable motion ($< 0.02$ arcseconds over a year). Peak brightness fluctuates in the display (22 to 41 MJy/sr), but the star's core is saturated (7–17 repaired pixels), so raw pixel intensities do not constitute a calibrated light curve.

---

## 8. Target 5 — R Draconis

### 8.1 Basic Identifiers & Reference Astrometry
- **Catalogue Identifier:** Gaia DR3 1648328016354496384 / HIP 81014
- **Cross Identifiers:** R Dra, HD 149880, AAVSO 1632+66
- **Coordinates (Equinox J2000, Epoch J1991.25):**
  - Sexagesimal: `16h 32m 40.230s` / `+66° 45′ 17.90″`
  - Decimal: $\alpha = 248.167625^\circ, \quad \delta = +66.754972^\circ$
- **Propagated Coordinates (Epoch 2026.0):**
  - Sexagesimal: `16h 32m 40.109s` / `+66° 45′ 18.14″`
  - Decimal: $\alpha = 248.167119^\circ, \quad \delta = +66.755040^\circ$
- **Quick-Pick App Coordinates:** $\alpha = 248.1675^\circ, \delta = +66.7550^\circ$ (within $0.5$″ of the 2026.0 position; unchanged).
- **Proper Motion:**
  - $\mu_{\alpha*} = -20.68 \pm 0.73\text{ mas/yr}$
  - $\mu_{\delta} = +7.07 \pm 0.67\text{ mas/yr}$
  - $\mu_{\text{total}} = 0.0219 \pm 0.0007\text{ ″/yr}$ ($21.85\text{ mas/yr}$)
  - Position Angle ($\text{PA}$): $288.84^\circ$ (West-Northwest)
- **Parallax:** $\varpi = 1.30 \pm 0.66\text{ mas}$ ($0.0013\text{ ″}$), Distance $d \sim 770\text{ pc}$ ($\sim 2500\text{ ly}$)
- **Astrophysical Classification:** Mira-type pulsating asymptotic giant branch (AGB) red giant; spectral type M5e–M9IIIe.

### 8.2 Variable Star Properties (AAVSO VSX)
- **Variability Class:** **M** (Mira pulsating variable)
- **Period:** **$245.6\text{ days}$** (regular, well-established pulsation period)
- **Visual Range:** $6.7 - 13.2\text{ V}$ (extreme visual amplitude of $6.5\text{ mag}$ / factor of 400 in flux).
- **Near-Infrared Amplitude:** $\Delta K \sim 1.5 - 2.0\text{ mag}$ (much smaller than optical due to $\text{TiO}$ molecular band opacity changes in cooler phases).
- **Physical Mechanism:** Radial fundamental-mode atmospheric pulsations of a highly evolved cool giant with massive stellar winds and circumstellar silicate dust formation.

### 8.3 Infrared Photometry
| Band | Magnitude | Uncertainty | Source Catalogue | Photometric Notes |
|---|---|---|---|---|
| **$J$ (1.25 µm)** | 4.53 | $\pm 0.20$ | SAAO Mean (Whitelock 2000) | Heavily saturated in 2MASS PSC |
| **$H$ (1.65 µm)** | 4.59 | $\pm 0.20$ | SAAO Mean (Whitelock 2000) | Heavily saturated in 2MASS PSC |
| **$K_s$ (2.16 µm)** | 3.85 | $\pm 0.15$ | SAAO Mean (Whitelock 2000) | Heavily saturated in 2MASS PSC |
| **$W1$ (3.4 µm)** | 3.20 | $\pm 0.30$ | DIRBE / Extrapolated | Saturated in AllWISE (limit $\sim 8.0$ mag) |
| **$W2$ (4.6 µm)** | 2.80 | $\pm 0.30$ | DIRBE / Extrapolated | Saturated in AllWISE (limit $\sim 6.7$ mag) |

### 8.4 Seasonal Movement Predictions (Detector 2: 1.10–1.62 µm)
Observed epochs extracted from `backend/seed/frames/fc84f9dc9a9662d3/result.json`:
- **Season 0:** Median UTC: `2025-06-22T15:37:00` (MJD 60848.651, 26 frames)
- **Season 1:** Median UTC: `2025-12-10T20:58:46` (MJD 61019.874, 30 frames)
- **Season 2:** Median UTC: `2026-06-21T16:30:39` (MJD 61212.688, 15 frames)

| Season Interval | Dates (UTC) | $\Delta t$ (yr) | Linear PM Shift (″) | Linear Pixels (Native/Disp) | Apparent Shift w/ Plx (″) | Apparent Pixels (Native/Disp) | Pred Direction ($\text{PA}$) |
|---|---|---|---|---|---|---|---|
| **Season 0 → Season 1** | 2025-06-22 → 2025-12-10 | 0.469 | 0.010″ | 0.002 / 0.005 | 0.010″ | 0.002 / 0.005 | 299.2° |
| **Season 1 → Season 2** | 2025-12-10 → 2026-06-21 | 0.528 | 0.012″ | 0.002 / 0.006 | 0.012″ | 0.002 / 0.006 | 276.8° |
| **Total Baseline (S0 → S2)** | **2025-06-22 → 2026-06-21** | **0.997** | **0.022″** | **0.004 / 0.011** | **0.022″** | **0.004 / 0.011** | **288.8°** |

**What a viewer should expect:**
Brilliant pulsating red giant, astrometrically stationary ($< 0.02$ arcseconds per year); causes severe detector core saturation (18–26 repaired pixels) and a wide bleeding halo in detector 2. The measured brightness-weighted centroid wanders artificially by 3–6 arcseconds between seasons solely because of pixel repair interpolation across its saturated core.

---

## 9. Catalogue Sources & Scientific References

1. **Gaia DR3:** Gaia Collaboration, Vallenari, A., et al. (2023), *"Gaia Data Release 3: Summary of the content and survey properties"*, Astronomy & Astrophysics, 674, A1. [DOI: 10.1051/0004-6361/202243940](https://doi.org/10.1051/0004-6361/202243940).
2. **2MASS:** Skrutskie, M. F., et al. (2006), *"The Two Micron All Sky Survey (2MASS)"*, Astronomical Journal, 131, 1163–1183. [DOI: 10.1086/498708](https://doi.org/10.1086/498708).
3. **AllWISE:** Wright, E. L., et al. (2010), *"The Wide-field Infrared Survey Explorer (WISE): Mission Description and Initial On-orbit Performance"*, Astronomical Journal, 140, 1868–1881. [DOI: 10.1088/0004-6256/140/6/1868](https://doi.org/10.1088/0004-6256/140/6/1868).
4. **WISE 0855 Discovery:** Luhman, K. L. (2014), *"Discovery of a ~250 K Brown Dwarf at 2 pc from the Sun"*, Astrophysical Journal Letters, 786, L18. [DOI: 10.1088/2041-8205/786/2/L18](https://doi.org/10.1088/2041-8205/786/2/L18).
5. **Substellar Astrometry Compilation:** Kirkpatrick, J. D., et al. (2021), *"The Field Substellar Mass Function Based on the Full-sky 20-pc Census of 525 L, T, and Y Dwarfs"*, Astrophysical Journal Supplement Series, 253, 7. [DOI: 10.3847/1538-4365/abd107](https://doi.org/10.3847/1538-4365/abd107).
6. **Epsilon Indi Ba/Bb Binary:** King, R. R., et al. (2010), *"$\varepsilon$ Indi Ba,Bb: a spectroscopic study of the nearest known brown dwarf binary"*, Astronomy & Astrophysics, 510, A99. [DOI: 10.1051/0004-6361/200912981](https://doi.org/10.1051/0004-6361/200912981).
7. **RW Aurigae System:** Schneider, P. C., et al. (2015), *"The 2014/2015 dimming event of RW Aurigae A"*, Astronomy & Astrophysics, 584, L9. [DOI: 10.1051/0004-6361/201527284](https://doi.org/10.1051/0004-6361/201527284).
8. **R Draconis NIR Monitoring:** Whitelock, P., Marang, F., & Feast, M. (2000), *"Infrared colours for Mira-like long-period variables found in the Hipparcos Catalogue"*, Monthly Notices of the Royal Astronomical Society, 319, 728–758. [DOI: 10.1046/j.1365-8711.2000.03842.x](https://doi.org/10.1046/j.1365-8711.2000.03842.x).
9. **AAVSO VSX:** Watson, C. L., Henden, A. A., & Price, A. (2006), *"AAVSO International Variable Star Index (VSX)"*, Society for Astronomical Sciences Annual Symposium, 25, 47.

---

## 10. Assumptions and Limitations

1. **Spacecraft Orbit Approximation:** As demonstrated in §2.5, treating SPHEREx's position as Earth-geocentric introduces a maximum parallax error of $< 0.025\text{ mas}$ ($< 0.000004\text{ pixels}$), which is completely negligible compared to the $6.14$″ native detector resolution.
2. **Radial Motion Acceleration:** Perspective acceleration (secular change in proper motion: $\dot{\mu} \approx -2\mu v_r \varpi$) is $< 1.2\text{ mas/yr}^2$ even for Barnard's Star, introducing $< 0.001$″ of curvature over the 1.5-year baseline.
3. **Core Saturation in Bright Sources:** For stars with $K < 8$ (Barnard's Star, RW Aurigae, R Draconis), detector pixels are flagged `OVERFLOW` and `NONLINEAR`. `prepare.py` repairs these pixels for display by nearest-neighbour interpolation. Consequently, brightness-weighted centroids on saturated stars carry an astrometric uncertainty of $\pm 0.5$ to $1.5$ arcseconds.
4. **Display Interpolation:** The web viewer resamples images using bilinear interpolation onto an oversampled $2.05$″/px grid. This preserves total surface brightness while improving subpixel centroid visibility for human spotters.

---

## 11. Reproducibility

Every numerical calculation, seasonal baseline, proper motion component, parallax factor, and pixel conversion in this document can be reproduced deterministically:
```bash
# From the repository root:
python3 scripts/calculate_target_predictions.py
```
This reads the official observation timestamps directly from the seeded SPHEREx frame metadata (`backend/seed/frames/*/result.json`), calculates linear proper motions and parallax-aware apparent positions, and outputs the structured dataset to `docs/target_predictions.json`.
