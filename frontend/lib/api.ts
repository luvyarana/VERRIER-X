export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type Query = { ra: number; dec: number; fov: number; band: number };

export type Frame = {
  index: number;
  id: string;
  time: string;
  mjd: number;
  season: number;
  detector: number;
  wavelength_um: number | null;
  bandwidth_um: number | null;
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
  request: { ra: number; dec: number; fov_arcmin: number; band: number };
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
  const params = new URLSearchParams({ ra: String(q.ra), dec: String(q.dec), fov: String(q.fov), band: String(q.band) });
  const res = await fetch(`${API_URL}/api/frames?${params}`, { signal });
  if (res.status === 422) return { status: "error", message: "Those coordinates or settings are out of range." };
  if (!res.ok) return { status: "error", message: `The server answered with an error (${res.status}).` };
  return res.json();
}
