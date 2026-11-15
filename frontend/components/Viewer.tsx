"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL, type Frame, type Result } from "@/lib/api";

const SEASON_COLOURS = ["#38bdf8", "#fbbf24", "#f472b6", "#4ade80", "#c084fc", "#fb923c"];
const SPEEDS = [1, 2, 4, 8, 15];

function dateRange(a: string, b: string) {
  return niceDate(a) === niceDate(b) ? niceDate(a) : `${niceDate(a)} – ${niceDate(b)}`;
}

function niceDate(iso: string) {
  const d = new Date(iso + "Z");
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export default function Viewer({ result }: { result: Result }) {
  const { frames, grid, seasons } = result;
  const canvas = useRef<HTMLCanvasElement>(null);
  const images = useRef<HTMLImageElement[]>([]);
  const [loaded, setLoaded] = useState(0);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const stacked = result.request.mode === "seasons";
  const [fps, setFps] = useState(stacked ? 1 : 4);
  const [marker, setMarker] = useState(true);
  const ready = loaded >= frames.length;
  const frame: Frame | undefined = frames[Math.min(index, frames.length - 1)];

  // Load every frame up front so the movie plays without gaps.
  useEffect(() => {
    let alive = true;
    images.current = frames.map((f) => {
      const img = new Image();
      img.onload = img.onerror = () => alive && setLoaded((n) => n + 1);
      img.src = API_URL + f.png_url;
      return img;
    });
    return () => {
      alive = false;
    };
  }, [frames]);

  useEffect(() => {
    if (!playing || !ready || frames.length < 2) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % frames.length), 1000 / fps);
    return () => clearInterval(timer);
  }, [playing, ready, fps, frames.length]);

  const step = useCallback(
    (by: number) => {
      setPlaying(false);
      setIndex((i) => (i + by + frames.length) % frames.length);
    },
    [frames.length],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === "INPUT") return;
      if (e.key === " ") {
        e.preventDefault();
        setPlaying((p) => !p);
      }
      if (e.key === "ArrowRight") step(1);
      if (e.key === "ArrowLeft") step(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step]);

  // Draw the current frame, then the markers on top.
  useEffect(() => {
    const c = canvas.current;
    const img = images.current[index];
    if (!c || !img || !img.complete || !img.naturalWidth) return;
    const ctx = c.getContext("2d")!;
    const s = c.width;
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(img, 0, 0, s, s);
    const perArcsec = s / (grid.size_px * grid.scale_arcsec);
    ctx.lineWidth = 2;
    ctx.font = "600 20px ui-sans-serif, system-ui, sans-serif";
    if (marker) {
      // Open cross at the position that was asked for; the gap keeps the target visible.
      ctx.strokeStyle = "#22d3ee";
      const m = s / 2, gap = Math.max(14, 12 * perArcsec), len = 26;
      ctx.beginPath();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        ctx.moveTo(m + dx * gap, m + dy * gap);
        ctx.lineTo(m + dx * (gap + len), m + dy * (gap + len));
      }
      ctx.stroke();
    }
    // Scale bar: 1 arcminute, or 5 for wide fields.
    const arcmin = grid.size_px * grid.scale_arcsec > 1500 ? 5 : 1;
    const bar = arcmin * 60 * perArcsec;
    ctx.strokeStyle = ctx.fillStyle = "#e2e8f0";
    ctx.beginPath();
    ctx.moveTo(24, s - 28);
    ctx.lineTo(24 + bar, s - 28);
    ctx.stroke();
    ctx.fillText(`${arcmin}′`, 24, s - 38);
    // Compass: north is up, east is left.
    ctx.beginPath();
    ctx.moveTo(s - 30, 78);
    ctx.lineTo(s - 30, 34);
    ctx.moveTo(s - 30, 78);
    ctx.lineTo(s - 74, 78);
    ctx.stroke();
    ctx.fillText("N", s - 37, 28);
    ctx.fillText("E", s - 96, 85);
  }, [index, loaded, marker, grid]);

  if (!frame) return null;
  const colour = SEASON_COLOURS[frame.season % SEASON_COLOURS.length];

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,640px)_1fr]">
      <div>
        <div className="relative aspect-square w-full overflow-hidden rounded-lg border border-slate-700 bg-black">
          <canvas ref={canvas} width={880} height={880} className="h-full w-full" aria-label="SPHEREx image sequence" />
          {!ready && (
            <div className="absolute inset-0 grid place-items-center bg-black/70 text-sm text-slate-300">
              Loading images… {loaded} of {frames.length}
            </div>
          )}
          <div className="pointer-events-none absolute left-3 top-3 rounded bg-black/60 px-2 py-1 text-sm font-medium" style={{ color: colour }}>
            {stacked && frame.time_start && frame.time_end ? dateRange(frame.time_start, frame.time_end) : niceDate(frame.time)}
            {stacked ? (
              <span className="text-slate-200"> · {frame.n_exposures} exposures combined</span>
            ) : (
              frame.wavelength_um != null && <span className="text-slate-200"> · {frame.wavelength_um.toFixed(2)} µm</span>
            )}
          </div>
        </div>

        {/* One coloured block per frame; colour shows the season. Click to jump. */}
        <div className="mt-3 flex h-4 gap-px" role="slider" aria-label="Frame" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={frames.length}>
          {frames.map((f) => (
            <button
              key={f.index}
              onClick={() => (setPlaying(false), setIndex(f.index))}
              title={stacked && f.time_start && f.time_end ? dateRange(f.time_start, f.time_end) : niceDate(f.time)}
              className="h-full min-w-0 flex-1 rounded-[1px] transition-opacity"
              style={{ background: SEASON_COLOURS[f.season % SEASON_COLOURS.length], opacity: f.index === index ? 1 : 0.3 }}
            />
          ))}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <button onClick={() => step(-1)} className="btn" aria-label="Previous frame">◀</button>
          <button onClick={() => setPlaying((p) => !p)} className="btn w-20 !bg-cyan-500 font-semibold !text-slate-950">
            {playing ? "Pause" : "Play"}
          </button>
          <button onClick={() => step(1)} className="btn" aria-label="Next frame">▶</button>
          <span className="ml-1 tabular-nums text-slate-400">
            {index + 1} / {frames.length}
          </span>
          <label className="ml-auto flex items-center gap-2 text-slate-400">
            Speed
            <select value={fps} onChange={(e) => setFps(Number(e.target.value))} className="field !w-auto !py-1">
              {SPEEDS.map((s) => (
                <option key={s} value={s}>{s} per second</option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-1.5 text-slate-400">
            <input type="checkbox" checked={marker} onChange={(e) => setMarker(e.target.checked)} className="accent-cyan-500" />
            Marker
          </label>
        </div>
        <p className="mt-2 text-xs text-slate-500">Space plays or pauses. Left and right arrows step one frame.</p>
      </div>

      <div className="space-y-5 text-sm">
        <section>
          <h2 className="heading">Seasons</h2>
          <ul className="space-y-1.5">
            {seasons.map((s) => (
              <li key={s.index}>
                <button
                  onClick={() => (setPlaying(false), setIndex(frames.findIndex((f) => f.season === s.index)))}
                  className={`flex w-full items-center gap-2 rounded px-2 py-1 text-left hover:bg-slate-800 ${frame.season === s.index ? "bg-slate-800" : ""}`}
                >
                  <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: SEASON_COLOURS[s.index % SEASON_COLOURS.length] }} />
                  <span>{niceDate(s.start)}{s.end !== s.start && ` – ${niceDate(s.end)}`}</span>
                  <span className="ml-auto text-slate-500">{s.frames} {s.frames === 1 ? "exposure" : "exposures"}</span>
                </button>
              </li>
            ))}
          </ul>
          {seasons.length > 1 && (
            <p className="mt-2 text-xs text-slate-500">
              {stacked
                ? "Each frame is one visit, with all its exposures combined into a deeper image. Anything that jumps from frame to frame has moved between visits."
                : "Anything that jumps when the colour changes has moved between visits. Stars that stay put are far away."}
            </p>
          )}
        </section>

        <section>
          <h2 className="heading">This frame</h2>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
            <dt className="text-slate-500">{stacked ? "Dates (UTC)" : "Time (UTC)"}</dt>
            <dd className="tabular-nums">
              {stacked && frame.time_start && frame.time_end
                ? `${frame.time_start.slice(0, 10)} to ${frame.time_end.slice(0, 10)}`
                : frame.time.replace("T", " ").slice(0, 19)}
            </dd>
            {stacked && (
              <>
                <dt className="text-slate-500">Combined</dt>
                <dd>{frame.n_exposures} exposures (median)</dd>
              </>
            )}
            <dt className="text-slate-500">Wavelength</dt>
            <dd>
              {stacked && frame.wavelength_min_um != null && frame.wavelength_max_um != null
                ? `${frame.wavelength_min_um.toFixed(2)} to ${frame.wavelength_max_um.toFixed(2)} µm`
                : frame.wavelength_um != null
                  ? `${frame.wavelength_um.toFixed(3)} µm`
                  : "not available"}
              {!stacked && frame.bandwidth_um != null && <span className="text-slate-500"> (width {frame.bandwidth_um.toFixed(3)} µm)</span>}
            </dd>
            <dt className="text-slate-500">Detector</dt>
            <dd>{frame.detector}</dd>
            <dt className="text-slate-500">Flags at centre</dt>
            <dd>{frame.target_flags.length ? frame.target_flags.join(", ").toLowerCase().replaceAll("_", " ") : "none"}</dd>
            <dt className="text-slate-500">Repaired pixels</dt>
            <dd>{(frame.bad_fraction * 100).toFixed(1)}% of the field</dd>
            <dt className="text-slate-500">{stacked ? "Source files" : "Source file"}</dt>
            <dd className="min-w-0">
              <a href={frame.source_url} className="break-all text-cyan-400 hover:underline" target="_blank" rel="noreferrer">
                {stacked ? `first of ${frame.n_exposures} exposures` : frame.id}
              </a>
            </dd>
          </dl>
          <p className="mt-2 text-xs text-slate-500">
            {stacked
              ? "The exposures in a visit are at different wavelengths within this detector's range, so a combined frame is a broad-band image."
              : "Each exposure sees this spot through a different part of the filter, so the wavelength changes from frame to frame and stars change brightness."}
          </p>
        </section>
      </div>
    </div>
  );
}
