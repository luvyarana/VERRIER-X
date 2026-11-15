# Validation notes: the five test targets

What the tool shows for each target the challenge asks for, and what it does not show.
Measured on 2026-11-15 with `scripts/v19_target_evidence.py`, at 10 arcminutes, using the detector of each quick-pick button.

How the numbers were made: the frames of each season were combined (median), and the position of the object at the centre was measured as a brightness-weighted centre. Offsets are relative to the marker. Field stars in the same frames stay within 0.2 pixels (1.3″), so shifts larger than that are real. The season strips are in `docs/evidence/`; each panel is 4 arcminutes wide, north up, east left.

Catalogue values quoted below are approximate and from memory of standard references. They must be replaced by the checked values in `docs/targets.md` before they are used in the slides.

| Target | Link | Result |
|---|---|---|
| Barnard's Star | [open](https://frontend-ivory-one-19.vercel.app/?ra=269.4486&dec=4.7685&fov=10&band=2) | **Moves.** Clearly visible. |
| Epsilon Indi B | [open](https://frontend-ivory-one-19.vercel.app/?ra=331.09&dec=-56.801&fov=10&band=3) | **Moves.** Clearly visible. |
| WISE 0855 | [open](https://frontend-ivory-one-19.vercel.app/?ra=133.7685&dec=-7.2429&fov=10&band=6) | **Not detected.** |
| RW Aurigae | [open](https://frontend-ivory-one-19.vercel.app/?ra=76.9563&dec=30.4014&fov=10&band=2) | **Does not move.** Brightness appears to change, but the star is saturated. |
| R Draconis | [open](https://frontend-ivory-one-19.vercel.app/?ra=248.1675&dec=66.755&fov=10&band=2) | **Does not move.** Saturated; brightness cannot be measured. |

## Barnard's Star (1.10–1.62 µm, 61 frames, 3 seasons)

The star steps north at each season change while the crowded field around it stays still.

| Season | Frames | Offset east | Offset north |
|---|---|---|---|
| Aug 2025 | 18 | −6.7″ | −3.7″ |
| Mar 2026 | 18 | −4.9″ | +1.1″ |
| Aug–Sep 2026 | 25 | −7.5″ | +6.2″ |

That is 9.9″ north in about one year. The catalogue motion is about 10.4″ per year, almost entirely northward. The east–west position swings back and forth by about 2″ between August and March, which is the size and timing expected from the star's parallax (about 0.55″ each way) plus measurement error; it was not modelled.

Limits: the star's core is saturated in every frame (12–16 pixels are repaired per frame), so the measured centre is rough. The star is about 7″ from the marker because the quick-pick position is approximate.

## Epsilon Indi B (1.62–2.42 µm, 72 of 99 frames, 5 seasons)

The bright object near the centre moves steadily east and south across five visits; the field stars do not move.

| Season | Frames | Offset east | Offset north |
|---|---|---|---|
| Apr–May 2025 | 18 | +11.0″ | +2.7″ |
| Jun 2025 | 2 | +11.3″ | +2.6″ |
| Sep–Nov 2025 | 17 | +11.8″ | +1.0″ |
| Apr–May 2026 | 9 | +14.7″ | −0.1″ |
| Sep 2026 | 26 | +15.7″ | −1.4″ |

Total: 4.7″ east and 4.1″ south in 1.4 years, about 4.4″ per year. The Epsilon Indi system moves about 4.7″ per year toward the east and south, so the direction and size agree.

Limits: the object sits 11–16″ east of the marker, because the quick-pick position is approximate. Epsilon Indi B is a pair of brown dwarfs 0.7″ apart; SPHEREx (6″ pixels) sees them as one object. We have not independently confirmed that the moving object is Epsilon Indi B rather than another star, beyond its position and motion matching.

## WISE 0855 (4.42–5.00 µm, 45 frames, 3 seasons)

Nothing is detected at the marker. In the combined frames of each season, the brightest pixel within 16″ of the centre is 1–3 times the noise, which is not a detection. A faint source about 30″ from the centre is visible in two seasons but does not move, so it is a background object.

Why: WISE 0855 is the coldest known brown dwarf and very faint (about magnitude 14 in the WISE 4.6 µm band). One SPHEREx exposure covers only a narrow slice of wavelength, so it collects far less light than the broad WISE band. Combining 21 frames was still not enough. The quick-pick position is also approximate, and this object moves about 8″ per year, so the true position may be off-centre.

What would help: combining all frames from detectors 5 and 6 along the predicted track (shift-and-stack). This is not built.

## RW Aurigae (1.10–1.62 µm, 55 frames, 3 seasons)

The star stays on the marker in all three seasons (offsets under 1″), as expected for a distant young star.

| Season | Frames | Peak brightness of the combined image |
|---|---|---|
| Sep 2025 | 18 | 29 MJy/sr |
| Mar 2026 | 19 | 41 MJy/sr |
| Sep 2026 | 18 | 22 MJy/sr |

The peak changes by almost a factor of two between visits, and RW Aurigae is known for deep, irregular dimmings. But this is not a reliable measurement: the core is saturated in most frames (7–17 repaired pixels), and each season mixes different wavelengths. Treat it as a hint, not a light curve.

## R Draconis (1.10–1.62 µm, 71 of 90 frames, 3 seasons)

R Draconis is a very bright long-period variable. It is heavily saturated in every frame (18–26 repaired pixels) and shows a wide halo. The measured centre wanders by up to 5″ between seasons; this comes from the saturated core, not from real motion.

Its brightness changes cannot be read from these images because the core is lost. A measurement would have to use the unsaturated wings of the star's image, which is not built.

The field is inside one of the SPHEREx deep fields, so some detectors have nearly 600 exposures here. The tool shows 72, spread evenly in time.

## Known problems

- Quick-pick positions are approximate (up to about 15″ off).
- Some frames show a bright band across part of the field.
- New positions take one to two minutes on the free backend host.
- Saturated stars are repaired for display only; their brightness is not trustworthy.
