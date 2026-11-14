// Parse right ascension and declination typed as decimal degrees or as
// hours/degrees, minutes, seconds (e.g. "08h55m10.831s", "-7d14m42.53s", "17:57:48").

function parts(text: string): { sign: number; values: number[] } | null {
  const t = text.trim().replace(/[−–]/g, "-");
  if (!t) return null;
  const sign = t.startsWith("-") ? -1 : 1;
  const values = t
    .replace(/^[+-]/, "")
    .split(/[^0-9.]+/)
    .filter(Boolean)
    .map(Number);
  if (!values.length || values.length > 3 || values.some((v) => !Number.isFinite(v))) return null;
  return { sign, values };
}

const sexagesimal = (v: number[]) => v[0] + (v[1] ?? 0) / 60 + (v[2] ?? 0) / 3600;

/** RA in degrees. A single number is degrees; anything with h, m, s or colons is hours. */
export function parseRa(text: string): number | null {
  const p = parts(text);
  if (!p || p.sign < 0) return null;
  const isHours = p.values.length > 1 || /h/i.test(text);
  const deg = isHours ? sexagesimal(p.values) * 15 : p.values[0];
  return deg >= 0 && deg <= 360 ? deg : null;
}

/** Dec in degrees. */
export function parseDec(text: string): number | null {
  const p = parts(text);
  if (!p) return null;
  const deg = p.sign * sexagesimal(p.values);
  return deg >= -90 && deg <= 90 ? deg : null;
}

const pad = (n: number, w = 2) => String(n).padStart(w, "0");

export function formatRa(deg: number): string {
  const s = Math.round((deg / 15) * 3600 * 100) / 100;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${pad(h)}h ${pad(m)}m ${(s % 60).toFixed(2).padStart(5, "0")}s`;
}

export function formatDec(deg: number): string {
  const s = Math.round(Math.abs(deg) * 3600 * 10) / 10;
  const d = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${deg < 0 ? "−" : "+"}${pad(d)}° ${pad(m)}′ ${(s % 60).toFixed(1).padStart(4, "0")}″`;
}
