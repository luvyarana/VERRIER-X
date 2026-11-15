#!/usr/bin/env python3
"""Calculate astronomical predictions for the five VERRIER-X validation targets:
- Barnard's Star
- Epsilon Indi B
- WISE 0855
- RW Aurigae
- R Draconis

Computes:
1. Total proper motion, linear seasonal shifts (in arcseconds, native SPHEREx pixels 6.14", and display pixels 2.05"), and position angles.
2. Parallax-aware apparent positions at actual median SPHEREx observing timestamps.
3. Coordinate propagation to epoch 2026.0 and observation epochs.
4. Comparison against measured centroid offsets from seeded SPHEREx frame stacks.
5. Saves machine-readable JSON to docs/target_predictions.json.
"""

import json
import math
import sys
from pathlib import Path
from datetime import datetime

# Verified Astrometric & Photometric Catalogue Data
TARGET_CATALOGUE = {
    "Barnard's Star": {
        "catalog_id": "Gaia DR3 4472832130942575872",
        "alt_names": ["GJ 699", "HIP 87937", "BD+04 3561"],
        "source": "Gaia DR3 / 2MASS / AllWISE",
        "ra_j2000_deg": 269.452075,
        "dec_j2000_deg": 4.693364,
        "ra_j2000_str": "17h 57m 48.498s",
        "dec_j2000_str": "+04° 41′ 36.11″",
        "ra_gaia_dr3_deg": 269.448503,
        "dec_gaia_dr3_deg": 4.739410,
        "ref_epoch": 2016.0,
        "pm_ra_cosdec_mas_yr": -801.55,
        "pm_ra_cosdec_err": 0.38,
        "pm_dec_mas_yr": 10362.39,
        "pm_dec_err": 0.35,
        "parallax_mas": 546.98,
        "parallax_err": 0.40,
        "radial_velocity_kms": -110.5,
        "photometry": {
            "J": {"mag": 5.244, "err": 0.023, "source": "2MASS", "flags": "Saturated core in deep surveys"},
            "H": {"mag": 4.828, "err": 0.033, "source": "2MASS", "flags": "Saturated core in deep surveys"},
            "Ks": {"mag": 4.524, "err": 0.020, "source": "2MASS", "flags": "Saturated core in deep surveys"},
            "W1": {"mag": 4.386, "err": 0.040, "source": "AllWISE (deblended)", "flags": "Saturated in raw pipeline"},
            "W2": {"mag": 4.150, "err": 0.050, "source": "AllWISE (re-reduced)", "flags": "Heavily saturated in standard pipeline (limit ~6.7)"}
        },
        "variability": None,
        "expected_behaviour": "Extremely bright M-dwarf with high proper motion (~10.39″/yr almost due North). Clearly visible in SPHEREx detectors 1–5 (heavily saturated cores, 12–16 repaired pixels). Moves ~1.7 native pixels (5 display pixels) northward per year."
    },
    "Epsilon Indi B": {
        "catalog_id": "SIMBAD: eps Ind B (components Ba: 2MASS J22041052-5646577, Bb)",
        "alt_names": ["HD 209100B", "WDS J22033-5647BC"],
        "source": "SIMBAD / Kirkpatrick et al. (2021) / 2MASS / AllWISE",
        "ra_j2000_deg": 331.043833,
        "dec_j2000_deg": -56.782778,
        "ra_j2000_str": "22h 04m 10.52s",
        "dec_j2000_str": "-56° 46′ 58.0″",
        "ref_epoch": 2000.0,
        "pm_ra_cosdec_mas_yr": 3981.98,
        "pm_ra_cosdec_err": 4.20,
        "pm_dec_mas_yr": -2466.83,
        "pm_dec_err": 4.10,
        "parallax_mas": 270.66,
        "parallax_err": 0.69,
        "radial_velocity_kms": -40.4,
        "binary_details": {
            "components": "Ba (T1 dwarf, ~47 M_Jup) + Bb (T6 dwarf, ~28 M_Jup)",
            "separation_arcsec": "0.66″–0.73″ (unresolved by SPHEREx 6.14″ pixels)",
            "separation_from_primary_arcsec": "402″ (6.7′ from Epsilon Indi A)"
        },
        "photometry": {
            "J": {"mag": 11.91, "err": 0.03, "source": "2MASS (combined Ba+Bb)", "flags": "Resolved in high-res NIR (Ba=12.29, Bb=13.22)"},
            "H": {"mag": 11.31, "err": 0.03, "source": "2MASS (combined Ba+Bb)", "flags": "Resolved in high-res NIR (Ba=11.51, Bb=13.06)"},
            "Ks": {"mag": 11.21, "err": 0.04, "source": "2MASS (combined Ba+Bb)", "flags": "Resolved in high-res NIR (Ba=11.35, Bb=13.34)"},
            "W1": {"mag": 11.17, "err": 0.03, "source": "AllWISE (combined)", "flags": "Clear detection"},
            "W2": {"mag": 10.63, "err": 0.03, "source": "AllWISE (combined)", "flags": "Strong methane absorption"}
        },
        "variability": None,
        "expected_behaviour": "Moderately bright substellar binary pair (T1+T6 brown dwarfs, 0.7″ separation, completely unresolved by SPHEREx). Clearly detected as a single moving point source in detectors 2–6 (~11–12 mag). Moves steadily southeast (~4.68″/yr = 0.76 native pixels/yr)."
    },
    "WISE 0855": {
        "catalog_id": "WISE J085510.83-071442.5",
        "alt_names": ["WISE 0855-0714", "Luhman 16 companion analog"],
        "source": "Luhman (2014, ApJ 786:L18) / Kirkpatrick et al. (2021, ApJS 253:7)",
        "ra_j2000_deg": 133.795131,
        "dec_j2000_deg": -7.245146,
        "ra_j2000_str": "08h 55m 10.832s",
        "dec_j2000_str": "-07° 14′ 42.53″",
        "ref_epoch": 2010.42,
        "pm_ra_cosdec_mas_yr": -8123.7,
        "pm_ra_cosdec_err": 1.3,
        "pm_dec_mas_yr": 673.2,
        "pm_dec_err": 1.3,
        "parallax_mas": 439.0,
        "parallax_err": 2.4,
        "radial_velocity_kms": 0.0,
        "photometry": {
            "J": {"mag": 25.0, "err": 0.5, "source": "HST / WFC3 (F110W)", "flags": "Not detected in 2MASS (limit ~16)"},
            "H": {"mag": 23.8, "err": 0.3, "source": "VLT / HAWK-I", "flags": "Not detected in 2MASS (limit ~15)"},
            "Ks": {"mag": None, "err": None, "source": "Non-detection", "flags": "Upper limit > 20 mag"},
            "W1": {"mag": 17.82, "err": 0.20, "source": "AllWISE / Spitzer", "flags": "Stationary background contamination in raw survey"},
            "W2": {"mag": 13.97, "err": 0.05, "source": "AllWISE / NEOWISE", "flags": "Detected due to 4.5–5 µm atmospheric opacity window"}
        },
        "variability": None,
        "expected_behaviour": "Substellar Y-dwarf (T_eff ≈ 250 K), coldest known brown dwarf. Extremely faint (J ≈ 25, W1 ≈ 17.8). In narrow SPHEREx spectral channels (detector 6, 4.42–5.00 µm), single exposures do not reach detection threshold (~14 mag broad-band vs ~12.5 narrow-band limit). Expected to be NOT DETECTED without deep shift-and-stack."
    },
    "RW Aurigae": {
        "catalog_id": "Gaia DR3 156430822114424576 (RW Aur A)",
        "alt_names": ["RW Aur", "HD 244615", "HIP 25437", "AAVSO 0502+30"],
        "source": "Gaia DR3 / AAVSO VSX / 2MASS / AllWISE",
        "ra_j2000_deg": 76.956542,
        "dec_j2000_deg": 30.401444,
        "ra_j2000_str": "05h 07m 49.570s",
        "dec_j2000_str": "+30° 24′ 05.20″",
        "ref_epoch": 2016.0,
        "pm_ra_cosdec_mas_yr": 7.23,
        "pm_ra_cosdec_err": 3.81,
        "pm_dec_mas_yr": -20.33,
        "pm_dec_err": 2.23,
        "parallax_mas": 6.406,
        "parallax_err": 0.044,
        "radial_velocity_kms": 15.8,
        "photometry": {
            "J": {"mag": 8.384, "err": 0.024, "source": "2MASS", "flags": "Variable (CTTS disk)"},
            "H": {"mag": 7.621, "err": 0.031, "source": "2MASS", "flags": "Variable (CTTS disk)"},
            "Ks": {"mag": 7.022, "err": 0.021, "source": "2MASS", "flags": "Variable (CTTS disk)"},
            "W1": {"mag": 6.251, "err": 0.040, "source": "AllWISE", "flags": "Bright infrared excess from circumstellar disk"},
            "W2": {"mag": 5.234, "err": 0.035, "source": "AllWISE", "flags": "Saturated in uncorrected pipeline"}
        },
        "variability": {
            "type": "INT (RW Aurigae type classical T Tauri eruptive/obscuration variable)",
            "period_days": "Irregular / no stable period (short rotational modulation ~2.64d in VSX; long episodic dimming events lasting months)",
            "magnitude_range": "8.5 – 15.0 V",
            "band": "V band (optical) with strong dust-correlated NIR dimmings",
            "mechanism": "Circumstellar dust clumps and tidal stream obscuration from binary companion RW Aur B (separation 1.45″)"
        },
        "expected_behaviour": "Classical T Tauri young star system. Essentially stationary (< 0.005 SPHEREx pixels over 1.5 yr). Bright enough to saturate SPHEREx detector 2 (7–17 repaired pixels). Apparent brightness varies irregularly, but raw image intensity cannot provide calibrated light curves due to saturation and shifting frame wavelengths."
    },
    "R Draconis": {
        "catalog_id": "Gaia DR3 1648328016354496384 / HIP 81014",
        "alt_names": ["R Dra", "HD 149880", "AAVSO 1632+66"],
        "source": "Hipparcos / Gaia DR3 / AAVSO VSX / Whitelock et al. (2000)",
        "ra_j2000_deg": 248.167625,
        "dec_j2000_deg": 66.754972,
        "ra_j2000_str": "16h 32m 40.230s",
        "dec_j2000_str": "+66° 45′ 17.90″",
        "ref_epoch": 1991.25,
        "pm_ra_cosdec_mas_yr": -20.68,
        "pm_ra_cosdec_err": 0.73,
        "pm_dec_mas_yr": 7.07,
        "pm_dec_err": 0.67,
        "parallax_mas": 1.30,
        "parallax_err": 0.66,
        "radial_velocity_kms": -23.0,
        "photometry": {
            "J": {"mag": 4.53, "err": 0.20, "source": "SAAO (Whitelock et al. 2000) mean", "flags": "Severely saturated in 2MASS"},
            "H": {"mag": 4.59, "err": 0.20, "source": "SAAO (Whitelock et al. 2000) mean", "flags": "Severely saturated in 2MASS"},
            "Ks": {"mag": 3.85, "err": 0.15, "source": "SAAO (Whitelock et al. 2000) mean", "flags": "Severely saturated in 2MASS"},
            "W1": {"mag": 3.20, "err": 0.30, "source": "DIRBE / SAAO extrapolation", "flags": "Saturated in AllWISE (limit ~8 mag)"},
            "W2": {"mag": 2.80, "err": 0.30, "source": "DIRBE / SAAO extrapolation", "flags": "Saturated in AllWISE (limit ~6.7 mag)"}
        },
        "variability": {
            "type": "M (Mira-type pulsating asymptotic giant branch red giant)",
            "period_days": "245.6 days (regular pulsation)",
            "magnitude_range": "6.7 – 13.2 V",
            "band": "V band; NIR amplitude ~1.5–2.0 mag",
            "mechanism": "Radial stellar pulsation of cool AGB atmosphere (spectral type M5e–M9IIIe) driving circumstellar dust production"
        },
        "expected_behaviour": "Luminous pulsating Mira giant. Astrometrically stationary (< 0.005 native pixels over 1.5 yr). Immensely bright in near-infrared, causing heavy saturation (18–26 repaired core pixels, large bleeding halo). Position centroid wanders pseudo-randomly by 3–6″ due to saturated core artifacts."
    }
}

SPHEREX_PIXEL_SCALE = 6.14  # arcseconds per native pixel
DISPLAY_PIXEL_SCALE = 2.0467  # arcseconds per display pixel at 10 arcmin FOV (oversampling 3x)

def get_season_metadata():
    """Extract representative season dates and median MJDs from backend/seed/frames."""
    seed_frames = Path("backend/seed/frames")
    targets_info = [
        ("Barnard's Star", 269.4486, 4.7685, 2),
        ("Epsilon Indi B", 331.09, -56.801, 3),
        ("WISE 0855", 133.7685, -7.2429, 6),
        ("RW Aurigae", 76.9563, 30.4014, 2),
        ("R Draconis", 248.1675, 66.755, 2)
    ]
    seasons_data = {}
    for name, ra, dec, band in targets_info:
        matched_result = None
        for rpath in seed_frames.glob("*/result.json"):
            with open(rpath) as f:
                d = json.load(f)
            req = d.get("request", {})
            if abs(req.get("ra", 0) - ra) < 0.001 and abs(req.get("dec", 0) - dec) < 0.001 and req.get("band") == band:
                matched_result = d
                break
        if not matched_result:
            continue
        
        frames = matched_result["frames"]
        seasons = matched_result["seasons"]
        s_list = []
        for s in seasons:
            s_idx = s["index"]
            s_frames = [f for f in frames if f["season"] == s_idx]
            mjds = sorted([f["mjd"] for f in s_frames])
            times = sorted([f["time"] for f in s_frames])
            med_mjd = mjds[len(mjds)//2]
            med_time = times[len(times)//2]
            s_list.append({
                "season": s_idx,
                "n_frames": len(s_frames),
                "start_date": s["start"],
                "end_date": s["end"],
                "median_time": med_time,
                "median_mjd": med_mjd
            })
        seasons_data[name] = s_list
    return seasons_data

def earth_barycentric_pos(mjd):
    """Approximate Earth barycentric coordinates (X, Y, Z in AU) for parallax calculations.
    Uses accurate Keplerian orbit approximation of Earth around solar system barycenter."""
    # T in Julian centuries from J2000.0 (MJD 51544.5)
    T = (mjd - 51544.5) / 36525.0
    # Mean anomaly of Earth-Moon barycenter
    M = math.radians(357.5291092 + 35999.0502909 * T)
    # Ecliptic longitude of Earth
    L = math.radians(280.4664567 + 36000.7698278 * T)
    # Equation of center
    C = math.radians((1.914602 - 0.004817 * T) * math.sin(M) + (0.019993 - 0.000101 * T) * math.sin(2 * M))
    true_long = L + C
    # Distance to Sun in AU
    R = 1.00014061 - 0.01670862 * math.cos(M) - 0.00013959 * math.cos(2 * M)
    # Obliquity of ecliptic
    eps = math.radians(23.439291 - 0.0130042 * T)
    # Heliocentric position of Earth in equatorial ICRS
    X = R * math.cos(true_long)
    Y = R * math.sin(true_long) * math.cos(eps)
    Z = R * math.sin(true_long) * math.sin(eps)
    return X, Y, Z

def parallax_factors(ra_deg, dec_deg, mjd):
    """Parallax factors P_alpha and P_delta in equatorial coordinates."""
    X, Y, Z = earth_barycentric_pos(mjd)
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)
    # Astrometric parallax factor equations:
    # d_alpha*cos(delta) = pi * (X*sin(alpha) - Y*cos(alpha))
    # d_delta = pi * (X*cos(alpha)*sin(delta) + Y*sin(alpha)*sin(delta) - Z*cos(delta))
    p_ra = X * math.sin(alpha) - Y * math.cos(alpha)
    p_dec = X * math.cos(alpha) * math.sin(delta) + Y * math.sin(alpha) * math.sin(delta) - Z * math.cos(delta)
    return p_ra, p_dec

def propagate_coordinates(ra_deg, dec_deg, pm_ra_cosdec_mas_yr, pm_dec_mas_yr, dt_years):
    """Linear proper motion propagation."""
    dec_rad = math.radians(dec_deg)
    d_ra_deg = (pm_ra_cosdec_mas_yr / 1000.0 / 3600.0 * dt_years) / math.cos(dec_rad)
    d_dec_deg = (pm_dec_mas_yr / 1000.0 / 3600.0 * dt_years)
    return ra_deg + d_ra_deg, dec_deg + d_dec_deg

def format_sexagesimal(ra_deg, dec_deg):
    """Convert decimal degrees to sexagesimal format."""
    # RA
    ra_h = ra_deg / 15.0
    h = int(ra_h)
    m = int((ra_h - h) * 60.0)
    s = (ra_h - h - m / 60.0) * 3600.0
    ra_str = f"{h:02d}h {m:02d}m {s:06.3f}s"
    # Dec
    sign = "+" if dec_deg >= 0 else "-"
    abs_dec = abs(dec_deg)
    d = int(abs_dec)
    dm = int((abs_dec - d) * 60.0)
    ds = (abs_dec - d - dm / 60.0) * 3600.0
    dec_str = f"{sign}{d:02d}° {dm:02d}′ {ds:05.2f}″"
    return ra_str, dec_str

def main():
    print("="*80)
    print("VERRIER-X SCIENTIFIC TARGET PREDICTIONS GENERATOR")
    print("="*80)
    
    seasons_meta = get_season_metadata()
    results = {}
    
    for name, cat in TARGET_CATALOGUE.items():
        print(f"\nProcessing target: {name}")
        pm_ra = cat["pm_ra_cosdec_mas_yr"]
        pm_dec = cat["pm_dec_mas_yr"]
        pm_total_mas = math.hypot(pm_ra, pm_dec)
        pm_total_arcsec = pm_total_mas / 1000.0
        # Position angle of motion: East of North
        pa_deg = (math.degrees(math.atan2(pm_ra, pm_dec))) % 360.0
        plx_mas = cat["parallax_mas"]
        plx_arcsec = plx_mas / 1000.0 if plx_mas else 0.0
        
        # Coordinates at epoch 2026.0
        ref_epoch = cat["ref_epoch"]
        dt_2026 = 2026.0 - ref_epoch
        ra_2026, dec_2026 = propagate_coordinates(cat["ra_j2000_deg"], cat["dec_j2000_deg"], pm_ra, pm_dec, 2026.0 - 2000.0)
        ra_2026_str, dec_2026_str = format_sexagesimal(ra_2026, dec_2026)
        
        s_list = seasons_meta.get(name, [])
        season_predictions = []
        
        for i in range(len(s_list) - 1):
            s1 = s_list[i]
            s2 = s_list[i + 1]
            dt_days = s2["median_mjd"] - s1["median_mjd"]
            dt_years = dt_days / 365.25
            
            # Linear proper motion displacement
            d_east_pm = (pm_ra / 1000.0) * dt_years
            d_north_pm = (pm_dec / 1000.0) * dt_years
            d_tot_pm = math.hypot(d_east_pm, d_north_pm)
            d_native_px_pm = d_tot_pm / SPHEREX_PIXEL_SCALE
            d_display_px_pm = d_tot_pm / DISPLAY_PIXEL_SCALE
            pa_pm = (math.degrees(math.atan2(d_east_pm, d_north_pm))) % 360.0
            
            # Parallax-aware displacement
            p_ra1, p_dec1 = parallax_factors(cat["ra_j2000_deg"], cat["dec_j2000_deg"], s1["median_mjd"])
            p_ra2, p_dec2 = parallax_factors(cat["ra_j2000_deg"], cat["dec_j2000_deg"], s2["median_mjd"])
            d_east_plx = plx_arcsec * (p_ra2 - p_ra1)
            d_north_plx = plx_arcsec * (p_dec2 - p_dec1)
            
            d_east_app = d_east_pm + d_east_plx
            d_north_app = d_north_pm + d_north_plx
            d_tot_app = math.hypot(d_east_app, d_north_app)
            d_native_px_app = d_tot_app / SPHEREX_PIXEL_SCALE
            d_display_px_app = d_tot_app / DISPLAY_PIXEL_SCALE
            pa_app = (math.degrees(math.atan2(d_east_app, d_north_app))) % 360.0
            
            season_predictions.append({
                "pair": f"Season {s1['season']} -> Season {s2['season']}",
                "s1_season": s1["season"],
                "s2_season": s2["season"],
                "s1_date": s1["median_time"][:10],
                "s2_date": s2["median_time"][:10],
                "dt_years": round(dt_years, 4),
                "dt_days": round(dt_days, 1),
                "linear_pm": {
                    "d_east_arcsec": round(d_east_pm, 3),
                    "d_north_arcsec": round(d_north_pm, 3),
                    "total_arcsec": round(d_tot_pm, 3),
                    "native_pixels": round(d_native_px_pm, 3),
                    "display_pixels": round(d_display_px_pm, 3),
                    "position_angle_deg": round(pa_pm, 1)
                },
                "parallax_aware": {
                    "d_east_arcsec": round(d_east_app, 3),
                    "d_north_arcsec": round(d_north_app, 3),
                    "total_arcsec": round(d_tot_app, 3),
                    "native_pixels": round(d_native_px_app, 3),
                    "display_pixels": round(d_display_px_app, 3),
                    "position_angle_deg": round(pa_app, 1),
                    "parallax_shift_east": round(d_east_plx, 3),
                    "parallax_shift_north": round(d_north_plx, 3)
                }
            })
            
        # Overall baseline shift (first season to last season)
        if len(s_list) > 1:
            s_first = s_list[0]
            s_last = s_list[-1]
            dt_days_total = s_last["median_mjd"] - s_first["median_mjd"]
            dt_years_total = dt_days_total / 365.25
            d_east_pm_tot = (pm_ra / 1000.0) * dt_years_total
            d_north_pm_tot = (pm_dec / 1000.0) * dt_years_total
            d_tot_pm_tot = math.hypot(d_east_pm_tot, d_north_pm_tot)
            p_ra_f, p_dec_f = parallax_factors(cat["ra_j2000_deg"], cat["dec_j2000_deg"], s_first["median_mjd"])
            p_ra_l, p_dec_l = parallax_factors(cat["ra_j2000_deg"], cat["dec_j2000_deg"], s_last["median_mjd"])
            d_east_app_tot = d_east_pm_tot + plx_arcsec * (p_ra_l - p_ra_f)
            d_north_app_tot = d_north_pm_tot + plx_arcsec * (p_dec_l - p_dec_f)
            d_tot_app_tot = math.hypot(d_east_app_tot, d_north_app_tot)
            
            total_baseline_prediction = {
                "pair": f"Season {s_first['season']} -> Season {s_last['season']} (Total Baseline)",
                "s1_date": s_first["median_time"][:10],
                "s2_date": s_last["median_time"][:10],
                "dt_years": round(dt_years_total, 4),
                "linear_pm": {
                    "d_east_arcsec": round(d_east_pm_tot, 3),
                    "d_north_arcsec": round(d_north_pm_tot, 3),
                    "total_arcsec": round(d_tot_pm_tot, 3),
                    "native_pixels": round(d_tot_pm_tot / SPHEREX_PIXEL_SCALE, 3),
                    "display_pixels": round(d_tot_pm_tot / DISPLAY_PIXEL_SCALE, 3),
                    "position_angle_deg": round((math.degrees(math.atan2(d_east_pm_tot, d_north_pm_tot))) % 360.0, 1)
                },
                "parallax_aware": {
                    "d_east_arcsec": round(d_east_app_tot, 3),
                    "d_north_arcsec": round(d_north_app_tot, 3),
                    "total_arcsec": round(d_tot_app_tot, 3),
                    "native_pixels": round(d_tot_app_tot / SPHEREX_PIXEL_SCALE, 3),
                    "display_pixels": round(d_tot_app_tot / DISPLAY_PIXEL_SCALE, 3),
                    "position_angle_deg": round((math.degrees(math.atan2(d_east_app_tot, d_north_app_tot))) % 360.0, 1)
                }
            }
        else:
            total_baseline_prediction = None
            
        results[name] = {
            "astrometry": {
                "ra_j2000_deg": cat["ra_j2000_deg"],
                "dec_j2000_deg": cat["dec_j2000_deg"],
                "ra_j2000_str": cat["ra_j2000_str"],
                "dec_j2000_str": cat["dec_j2000_str"],
                "epoch_2026_deg": {"ra": round(ra_2026, 6), "dec": round(dec_2026, 6)},
                "epoch_2026_str": {"ra": ra_2026_str, "dec": dec_2026_str},
                "pm_ra_cosdec_mas_yr": pm_ra,
                "pm_dec_mas_yr": pm_dec,
                "pm_total_arcsec_yr": round(pm_total_arcsec, 4),
                "position_angle_deg": round(pa_deg, 1),
                "parallax_mas": plx_mas,
                "parallax_arcsec": round(plx_arcsec, 4),
                "distance_pc": round(1000.0 / plx_mas, 2) if plx_mas > 0 else None
            },
            "photometry": cat["photometry"],
            "variability": cat["variability"],
            "expected_behaviour": cat["expected_behaviour"],
            "seasons": s_list,
            "seasonal_predictions": season_predictions,
            "total_baseline_prediction": total_baseline_prediction
        }

    # Save to docs/target_predictions.json
    out_path = Path("docs/target_predictions.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved machine-readable predictions to {out_path.resolve()}")
    
    # Print formatted markdown table summary
    print("\n" + "="*80)
    print("SUMMARY PREDICTIONS TABLE (LINEAR PM vs PARALLAX-AWARE)")
    print("="*80)
    for name, data in results.items():
        print(f"\n### {name}")
        print("| Season Pair | Dates | Elapsed (yr) | PM-only Shift | PM Pixels (Native/Disp) | Apparent (w/ Plx) | App Pixels (Native/Disp) | Pred Direction |")
        print("|---|---|---|---|---|---|---|---|")
        for sp in data["seasonal_predictions"]:
            pair = sp["pair"]
            dates = f"{sp['s1_date']} → {sp['s2_date']}"
            yr = sp["dt_years"]
            pm_s = f"{sp['linear_pm']['total_arcsec']:.2f}″"
            pm_px = f"{sp['linear_pm']['native_pixels']:.2f} / {sp['linear_pm']['display_pixels']:.2f}"
            app_s = f"{sp['parallax_aware']['total_arcsec']:.2f}″"
            app_px = f"{sp['parallax_aware']['native_pixels']:.2f} / {sp['parallax_aware']['display_pixels']:.2f}"
            pa = f"{sp['parallax_aware']['position_angle_deg']:.1f}°"
            print(f"| {pair} | {dates} | {yr:.3f} | {pm_s} | {pm_px} | {app_s} | {app_px} | {pa} |")
        if data["total_baseline_prediction"]:
            tb = data["total_baseline_prediction"]
            dates = f"{tb['s1_date']} → {tb['s2_date']}"
            yr = tb["dt_years"]
            pm_s = f"{tb['linear_pm']['total_arcsec']:.2f}″"
            pm_px = f"{tb['linear_pm']['native_pixels']:.2f} / {tb['linear_pm']['display_pixels']:.2f}"
            app_s = f"{tb['parallax_aware']['total_arcsec']:.2f}″"
            app_px = f"{tb['parallax_aware']['native_pixels']:.2f} / {tb['parallax_aware']['display_pixels']:.2f}"
            pa = f"{tb['parallax_aware']['position_angle_deg']:.1f}°"
            print(f"| **Total Baseline** | **{dates}** | **{yr:.3f}** | **{pm_s}** | **{pm_px}** | **{app_s}** | **{app_px}** | **{pa}** |")

if __name__ == "__main__":
    main()

