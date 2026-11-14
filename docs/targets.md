# Target fact sheet

**Owner:** Sainy (`Sainyy56`)
**Time needed:** about 2 hours
**Needed by:** as early as possible on 14 November. The first data check (task V01) uses the coordinates from this sheet.

This page has two halves. The first half is the brief: what to do and how. The second half is the sheet itself: fill it in and commit.

---

## Brief

### Why this matters

The NASA challenge says: *"Test your tool on Barnard's Star, Epsilon Indi B, WISE 0855, and variable stars RW Aurigae and R Draconis."* Judges will try these five targets.

This sheet says, before the tool exists, what each target **should** look like in SPHEREx images. It is used three ways:

1. The backend uses your coordinates to search the SPHEREx archive.
2. When the tool is live, we compare what we see against your predictions. If they agree, that is our evidence that the tool is correct (the "Validity" judging criterion).
3. The numbers go on the slides.

### Background you need (5 minutes)

- **RA and Dec** are the sky's longitude and latitude. RA is written in hours, minutes, seconds (`17h 57m 48.5s`) or in degrees (0–360). Dec is in degrees (−90 to +90).
  - To convert RA to degrees: `degrees = 15 × (h + m/60 + s/3600)`.
  - To convert Dec to degrees: `d + m/60 + s/3600`, keeping the sign of `d`.
- **J2000** means "the coordinate grid of the year 2000". Catalogues list positions on this grid.
- **Epoch** is the date the star was actually at the listed position. Nearby stars move, so a position is only right for its epoch. SIMBAD usually gives epoch 2000.0; Gaia DR3 gives epoch 2016.0.
- **Proper motion** is how fast the star moves across the sky. Catalogues give it in milliarcseconds per year (mas/yr) as two numbers: `pmRA` (east–west) and `pmDec` (north–south). 1000 mas = 1 arcsecond (″).
- **Parallax** is a small yearly wobble caused by Earth's orbit. Larger parallax means a closer star. Give it in mas.
- **Magnitudes** measure brightness. **Smaller is brighter.** J, H and K are near-infrared bands (1.2, 1.6, 2.2 µm) from the 2MASS survey. W1 and W2 are from the WISE mission (3.4 and 4.6 µm). SPHEREx covers 0.75–5.0 µm, so these bands tell us how bright the target is for SPHEREx.
- **SPHEREx pixel:** 6.14″ across. SPHEREx re-images the whole sky about every 6 months (a "season").

### Where to look

| What | Site | How |
|---|---|---|
| Coordinates, proper motion, parallax, J/H/K | **SIMBAD**: https://simbad.cds.unistra.fr/simbad/sim-fid | Type the name from the table below. Read the "ICRS coord. (ep=J2000)", "Proper motions mas/yr", "Parallaxes (mas)" and "Fluxes" lines. |
| W1, W2 | **VizieR**: https://vizier.cds.unistra.fr | Search catalogue `II/328` (AllWISE) by the target's coordinates, radius 10–30″. For WISE 0855, use the discovery papers linked from SIMBAD instead. |
| Variable-star period and range | **AAVSO VSX**: https://www.aavso.org/vsx | Search by name. Read "Period", "Mag. range" and "Variability type". |
| Check against Gaia | **Gaia DR3** via VizieR catalogue `I/355` | Only Barnard's Star, RW Aurigae and R Draconis are in Gaia. The two brown dwarfs are too faint. |

**Names to type into SIMBAD**

| Target | SIMBAD name |
|---|---|
| Barnard's Star | `Barnard's Star` |
| Epsilon Indi B | `eps Ind B` (also look at `eps Ind Ba` and `eps Ind Bb`; it is a pair of brown dwarfs) |
| WISE 0855 | `WISE J085510.83-071442.5` |
| RW Aurigae | `RW Aur` |
| R Draconis | `R Dra` |

For every number, write down **which catalogue or paper it came from**. SIMBAD shows a reference code beside each value; copy that.

### The calculations

Do these for the three moving targets (Barnard's Star, Epsilon Indi B, WISE 0855). For the two variable stars, do them too; the answers will be close to zero, and that is the point.

**Step 1. Total proper motion**

```
pm_total (″/yr) = sqrt(pmRA² + pmDec²) / 1000        (pmRA, pmDec in mas/yr)
```

**Step 2. Shift between SPHEREx seasons**

```
shift (″)  = pm_total × years
shift (px) = shift (″) / 6.14
```

Work it out for 0.5, 1.0 and 1.5 years. SPHEREx has been observing since May 2025, so 1.5 years is the longest gap available.

**Step 3. Direction of motion**

Say it in words from the signs:

- `pmRA` positive → moving **east**; negative → **west**.
- `pmDec` positive → moving **north**; negative → **south**.

Example: pmRA = −800, pmDec = +10360 → "almost due north, slightly west". In our viewer north is up and east is **left**.

**Step 4. Where the star is now (epoch 2026.0)**

Catalogue positions are old. A fast star has moved well away from them.

```
years   = 2026.0 − epoch of the catalogue position
Dec_now = Dec + (pmDec / 1000 × years) / 3600                       (degrees)
RA_now  = RA  + (pmRA  / 1000 × years) / 3600 / cos(Dec)            (degrees)
```

Notes:

- `pmRA` in SIMBAD and Gaia already includes the cos(Dec) factor. That is why you divide by cos(Dec) here to get back to RA degrees.
- Use Dec in degrees inside `cos`. In a calculator or spreadsheet, convert to radians first: `COS(RADIANS(dec))`.
- For WISE 0855, the challenge gives a position (RA 08h55m10.831s, Dec −7d14m42.53s). Find its epoch in the discovery paper (Luhman 2014) and use that as the starting epoch.

**Step 5. Parallax wobble**

For the three nearby targets, note the parallax in arcseconds (mas / 1000) and in pixels (÷ 6.14). The star wobbles by up to this amount either side of its straight path over a year. One line is enough.

**Worked example to check your method** (rough numbers; replace with the catalogue values you find):

Barnard's Star, pmRA ≈ −800 mas/yr, pmDec ≈ +10360 mas/yr.

- pm_total = sqrt(800² + 10360²) / 1000 ≈ 10.39 ″/yr
- 0.5 yr → 5.2″ → 0.85 px; 1.0 yr → 10.4″ → 1.69 px; 1.5 yr → 15.6″ → 2.54 px
- Direction: almost due north, slightly west
- Since 2000.0 it has moved about 10.39 × 26 ≈ 270″, which is 4.5 arcminutes. So the J2000 position is no longer where the star is.

### Rough values to sanity-check against

These are from memory and may be off. **Do not copy them into the sheet.** If your catalogue value differs a lot from these, re-check the object name before trusting either.

| Target | Rough position (J2000) | Rough motion | Rough brightness / behaviour |
|---|---|---|---|
| Barnard's Star | 17h 57m 48s, +04° 41′ | about 10.4 ″/yr, northward | K ≈ 4.5 (very bright) |
| Epsilon Indi B | 22h 04m 10s, −56° 47′ | about 4.7 ″/yr | K ≈ 11; two brown dwarfs under 1″ apart, so SPHEREx sees one blob |
| WISE 0855 | 08h 55m 11s, −07° 15′ | about 8 ″/yr, westward; parallax about 0.4″ | W2 ≈ 14, J ≈ 25 (extremely faint except near 4.5 µm) |
| RW Aurigae | 05h 07m 50s, +30° 24′ | very small | Young star with irregular dimming; no fixed period |
| R Draconis | 16h 32m 40s, +66° 45′ | very small | Mira-type variable; period around 245 days; several magnitudes of change |

### What to write in "what a viewer should expect"

One or two plain sentences per target, answering:

- Will it be visible? Compare its magnitudes: K or W1 brighter than about 12 should be easy; fainter than about 16 is doubtful. State it as a prediction, not a fact.
- Will it move? Give the pixel shift over the longest gap.
- Will it change brightness? Only for the variables.

Example: *"Bright and easy to see. Moves about 2.5 pixels north over 1.5 years, while the stars around it stay still."*

### Rules

- **Never guess.** If you cannot find a value, write `not found` and where you looked.
- Keep the catalogue's full precision. Do not round coordinates.
- Record the reference for every value.
- If two sources disagree, record both and say which you chose and why.
- Disclose any AI tool you use to help. The hackathon requires it. Check every number it gives you against the catalogue.

### How to hand it in

1. Accept the GitHub invitation to `luvyarana/VERRIER-X` (check your email or https://github.com/notifications).
2. Open this file on GitHub: `docs/targets.md`.
3. Click the pencil icon to edit, fill in the sheet below, and click **Commit changes** (commit directly to `main`).
4. Commit as soon as the **coordinates and proper motions** for all five are in, even if the rest is unfinished. Those unblock the data check. Then carry on and commit again.
5. Message Luvya when the first commit is in.

### Done when

- [ ] All five targets have coordinates (sexagesimal and degrees), epoch and source.
- [ ] Proper motion and parallax are filled in, with sources.
- [ ] J, H, K and W1, W2 are filled in or marked `not found`.
- [ ] The three shift values (0.5, 1.0, 1.5 yr) are in arcseconds and pixels.
- [ ] Position at epoch 2026.0 is computed for the three moving targets.
- [ ] Period, type and range are filled in for the two variables.
- [ ] Each target has its "what a viewer should expect" sentence.

---

## The sheet

*Fill in below. Replace every `…`.*

### 1. Barnard's Star

| Field | Value | Source |
|---|---|---|
| RA (J2000), sexagesimal | … | … |
| Dec (J2000), sexagesimal | … | … |
| RA (degrees) | … | computed |
| Dec (degrees) | … | computed |
| Epoch of position | … | … |
| pmRA (mas/yr) | … | … |
| pmDec (mas/yr) | … | … |
| Parallax (mas) | … | … |
| J / H / K (mag) | … / … / … | … |
| W1 / W2 (mag) | … / … | … |

| Calculation | Value |
|---|---|
| Total proper motion (″/yr) | … |
| Direction | … |
| Shift in 0.5 yr (″ / px) | … / … |
| Shift in 1.0 yr (″ / px) | … / … |
| Shift in 1.5 yr (″ / px) | … / … |
| RA at 2026.0 (degrees) | … |
| Dec at 2026.0 (degrees) | … |
| Parallax wobble (″ / px) | … / … |

**What a viewer should expect:** …

### 2. Epsilon Indi B

| Field | Value | Source |
|---|---|---|
| RA (J2000), sexagesimal | … | … |
| Dec (J2000), sexagesimal | … | … |
| RA (degrees) | … | computed |
| Dec (degrees) | … | computed |
| Epoch of position | … | … |
| pmRA (mas/yr) | … | … |
| pmDec (mas/yr) | … | … |
| Parallax (mas) | … | … |
| J / H / K (mag) | … / … / … | … |
| W1 / W2 (mag) | … / … | … |
| Separation of Ba and Bb (″) | … | … |
| Distance on the sky from Epsilon Indi A (″) | … | … |

| Calculation | Value |
|---|---|
| Total proper motion (″/yr) | … |
| Direction | … |
| Shift in 0.5 yr (″ / px) | … / … |
| Shift in 1.0 yr (″ / px) | … / … |
| Shift in 1.5 yr (″ / px) | … / … |
| RA at 2026.0 (degrees) | … |
| Dec at 2026.0 (degrees) | … |
| Parallax wobble (″ / px) | … / … |

**What a viewer should expect:** …

### 3. WISE 0855 (WISE J085510.83−071442.5)

| Field | Value | Source |
|---|---|---|
| RA, sexagesimal | 08h 55m 10.831s | challenge page |
| Dec, sexagesimal | −07° 14′ 42.53″ | challenge page |
| RA (degrees) | … | computed |
| Dec (degrees) | … | computed |
| Epoch of position | … | … |
| pmRA (mas/yr) | … | … |
| pmDec (mas/yr) | … | … |
| Parallax (mas) | … | … |
| J / H / K (mag) | … / … / … | … |
| W1 / W2 (mag) | … / … | … |

| Calculation | Value |
|---|---|
| Total proper motion (″/yr) | … |
| Direction | … |
| Shift in 0.5 yr (″ / px) | … / … |
| Shift in 1.0 yr (″ / px) | … / … |
| Shift in 1.5 yr (″ / px) | … / … |
| RA at 2026.0 (degrees) | … |
| Dec at 2026.0 (degrees) | … |
| Parallax wobble (″ / px) | … / … |

**What a viewer should expect:** …

### 4. RW Aurigae

| Field | Value | Source |
|---|---|---|
| RA (J2000), sexagesimal | … | … |
| Dec (J2000), sexagesimal | … | … |
| RA (degrees) | … | computed |
| Dec (degrees) | … | computed |
| pmRA / pmDec (mas/yr) | … / … | … |
| Parallax (mas) | … | … |
| J / H / K (mag) | … / … / … | … |
| W1 / W2 (mag) | … / … | … |
| Variability type | … | … |
| Period (days), or "irregular" | … | … |
| Brightness range (mag, and in which band) | … | … |
| Shift in 1.5 yr (″ / px) | … / … | computed |

**What a viewer should expect:** …

### 5. R Draconis

| Field | Value | Source |
|---|---|---|
| RA (J2000), sexagesimal | … | … |
| Dec (J2000), sexagesimal | … | … |
| RA (degrees) | … | computed |
| Dec (degrees) | … | computed |
| pmRA / pmDec (mas/yr) | … / … | … |
| Parallax (mas) | … | … |
| J / H / K (mag) | … / … / … | … |
| W1 / W2 (mag) | … / … | … |
| Variability type | … | … |
| Period (days) | … | … |
| Brightness range (mag, and in which band) | … | … |
| Shift in 1.5 yr (″ / px) | … / … | computed |

**What a viewer should expect:** …

### Notes and problems

*Anything unclear, any sources that disagreed, anything not found.*

…
