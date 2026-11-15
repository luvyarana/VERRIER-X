// Set NEXT_PUBLIC_API_URL to override. An empty value falls back to these defaults.
const DEFAULT_API = process.env.NODE_ENV === "production" ? "https://verrier-x-api.onrender.com" : "http://localhost:8000";
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API).replace(/\/$/, "");

export type Mode = "seasons" | "exposures";
export type Query = { ra: number; dec: number; fov: number; band: number; mode: Mode };

export type Frame = {
  index: number;
  id: string;
  time: string;
  mjd: number;
  season: number;
  detector: number;
  wavelength_um: number | null;
  bandwidth_um: number | null;
  wavelength_min_um?: number | null;
  wavelength_max_um?: number | null;
  time_start?: string;
  time_end?: string;
  n_exposures: number;
  coverage: number;
  bad_fraction: number;
  saturated_pixels: number;
  target_flags: string[];
  collection: string;
  png_url: string;
  source_url: string;
};

export type Season = { index: number; start: string; end: string; frames: number };

export type Result = {
  status: "done";
  key: string;
  request: { ra: number; dec: number; fov_arcmin: number; band: number; mode: Mode };
  grid: { size_px: number; scale_arcsec: number };
  exposures_per_detector: Record<string, number>;
  exposures_in_band: number;
  seasons: Season[];
  frames: Frame[];
  warnings: string[];
  complete: boolean;
};

export type Working = { status: "working"; stage: string; done: number; total: number; message: string };
export type Failed = { status: "error"; message: string };

/** Detector number -> wavelength range in microns. */
export const DETECTORS: { id: number; range: string }[] = [
  { id: 1, range: "0.75–1.10" },
  { id: 2, range: "1.10–1.62" },
  { id: 3, range: "1.62–2.42" },
  { id: 4, range: "2.42–3.82" },
  { id: 5, range: "3.82–4.42" },
  { id: 6, range: "4.42–5.00" },
];

export async function getFrames(q: Query, signal: AbortSignal): Promise<Result | Working | Failed> {
  const params = new URLSearchParams({ ra: String(q.ra), dec: String(q.dec), fov: String(q.fov), band: String(q.band), mode: q.mode });
  const res = await fetch(`${API_URL}/api/frames?${params}`, { signal });
  if (res.status === 422) return { status: "error", message: "Those coordinates or settings are out of range." };
  if (!res.ok) return { status: "error", message: `The server answered with an error (${res.status}).` };
  return res.json();
}

export type GaiaStar = { id: string; ra: number; dec: number; pmra: number; pmdec: number; parallax: number | null; g: number | null };

/** Gaia DR3 stars around a position (2016.0 positions, proper motions in mas/yr). Empty if unavailable. */
export async function getGaia(ra: number, dec: number, fov: number, signal: AbortSignal): Promise<GaiaStar[] | null> {
  try {
    const res = await fetch(`${API_URL}/api/gaia?ra=${ra}&dec=${dec}&fov=${fov}`, { signal });
    if (!res.ok) return null;
    return (await res.json()).stars as GaiaStar[];
  } catch {
    return null;
  }
}

const RAD = Math.PI / 180;

/** Where a Gaia star is at a given date, as offsets in arcseconds (east, north) from the field centre. */
export function starOffset(star: GaiaStar, mjd: number, ra0: number, dec0: number): [number, number] {
  const years = 2000 + (mjd - 51544.5) / 365.25 - 2016.0;
  const dec = star.dec + (star.pmdec * years) / 3.6e6;
  const ra = star.ra + (star.pmra * years) / 3.6e6 / Math.cos(star.dec * RAD);
  const da = (ra - ra0) * RAD, d = dec * RAD, d0 = dec0 * RAD;
  const denom = Math.sin(d0) * Math.sin(d) + Math.cos(d0) * Math.cos(d) * Math.cos(da);
  const xi = (Math.cos(d) * Math.sin(da)) / denom;
  const eta = (Math.cos(d0) * Math.sin(d) - Math.sin(d0) * Math.cos(d) * Math.cos(da)) / denom;
  return [(xi / RAD) * 3600, (eta / RAD) * 3600];
}
