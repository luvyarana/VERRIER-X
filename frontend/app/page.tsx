"use client";

import { useEffect, useState } from "react";
import Viewer from "@/components/Viewer";
import { DETECTORS, getFrames, resolveName, type Mode, type Query, type Result, type Working } from "@/lib/api";
import { formatDec, formatRa, parseDec, parseRa } from "@/lib/coords";

// Positions of the challenge's test targets at epoch 2026.0 (catalogue position moved by proper motion; see docs/targets.md).
const TARGETS: { name: string; ra: number; dec: number; band: number }[] = [
  { name: "Barnard's Star", ra: 269.44627, dec: 4.76819, band: 2 },
  { name: "Epsilon Indi B", ra: 331.09636, dec: -56.80058, band: 3 },
  { name: "WISE 0855", ra: 133.75969, dec: -7.24223, band: 6 },
  { name: "RW Aurigae", ra: 76.9563, dec: 30.4014, band: 2 },
  { name: "R Draconis", ra: 248.1675, dec: 66.755, band: 2 },
];
const FOVS = [5, 10, 20, 30, 60];

type State =
  | { kind: "idle" }
  | { kind: "working"; progress: Working | null }
  | { kind: "done"; result: Result }
  | { kind: "error"; message: string };

function readUrl(): Query | null {
  const p = new URLSearchParams(window.location.search);
  const ra = parseRa(p.get("ra") ?? ""), dec = parseDec(p.get("dec") ?? "");
  if (ra == null || dec == null) return null;
  const fov = Number(p.get("fov")), band = Number(p.get("band"));
  const m = p.get("mode");
  const mode: Mode = m === "exposures" || m === "difference" ? m : "seasons";
  return { ra, dec, fov: fov >= 2 && fov <= 60 ? fov : 10, band: band >= 1 && band <= 6 ? Math.round(band) : 2, mode };
}

export default function Home() {
  const [raText, setRaText] = useState("");
  const [decText, setDecText] = useState("");
  const [fov, setFov] = useState(10);
  const [query, setQuery] = useState<Query | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<State>({ kind: "idle" });
  const [formError, setFormError] = useState("");
  const [nameText, setNameText] = useState("");
  const [nameNote, setNameNote] = useState("");
  const [looking, setLooking] = useState(false);

  const lookUp = async () => {
    const name = nameText.trim();
    if (!name || looking) return;
    setLooking(true);
    setNameNote("");
    setFormError("");
    const found = await resolveName(name);
    setLooking(false);
    if (typeof found === "string") return setFormError(found);
    setNameNote(
      found.moved_arcsec >= 1
        ? `${found.name}: moved ${found.moved_arcsec.toFixed(0)}″ from its year-2000 catalogue position to where it was at the start of 2026, using its known motion.`
        : `${found.name}: found.`,
    );
    run({ ra: found.ra, dec: found.dec, fov, band: query?.band ?? 2, mode: query?.mode ?? "seasons" });
  };

  const run = (q: Query, push = true) => {
    setRaText(String(q.ra));
    setDecText(String(q.dec));
    setFov(q.fov);
    setFormError("");
    setQuery(q);
    setState({ kind: "working", progress: null });
    setAttempt((n) => n + 1);
    if (push) {
      const url = `?ra=${q.ra}&dec=${q.dec}&fov=${q.fov}&band=${q.band}&mode=${q.mode}`;
      window.history.pushState(null, "", url);
    }
  };

  // Open straight from a link such as /?ra=269.45&dec=4.77&fov=10, and follow back/forward.
  useEffect(() => {
    const sync = () => {
      const q = readUrl();
      if (q) return run(q, false);
      setQuery(null);
      setState({ kind: "idle" });
    };
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  // Ask the server, then keep asking until the frames are ready.
  useEffect(() => {
    if (!query) return;
    const abort = new AbortController();
    (async () => {
      try {
        for (;;) {
          const r = await getFrames(query, abort.signal);
          if (r.status === "done") return setState({ kind: "done", result: r });
          if (r.status === "error") return setState({ kind: "error", message: r.message });
          setState({ kind: "working", progress: r });
          await new Promise((ok) => setTimeout(ok, 1200));
          if (abort.signal.aborted) return;
        }
      } catch {
        if (!abort.signal.aborted) setState({ kind: "error", message: "The VERRIER-X server could not be reached." });
      }
    })();
    return () => abort.abort();
  }, [query, attempt]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const ra = parseRa(raText), dec = parseDec(decText);
    if (ra == null) return setFormError("Right ascension should be 0 to 360 degrees, or hours like 17h 57m 48s.");
    if (dec == null) return setFormError("Declination should be −90 to +90 degrees, like −7d 14m 42s.");
    run({ ra: Number(ra.toFixed(5)), dec: Number(dec.toFixed(5)), fov, band: query?.band ?? 2, mode: query?.mode ?? "seasons" });
  };

  const result = state.kind === "done" ? state.result : null;
  const progress = state.kind === "working" ? state.progress : null;

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
      <header className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">
          VERRIER<span className="text-cyan-400">-X</span>
        </h1>
        <p className="mt-1 max-w-2xl text-slate-400">
          Pick a spot on the sky and play every SPHEREx image of it as a short movie. Things that move between visits stand out.
        </p>
      </header>

      <form onSubmit={submit} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="mb-3 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <label className="text-sm text-slate-400">
            Object name
            <input
              className="field mt-1"
              value={nameText}
              onChange={(e) => setNameText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  lookUp();
                }
              }}
              placeholder="for example Proxima Centauri, M31, Wolf 359"
            />
          </label>
          <button type="button" onClick={lookUp} disabled={looking || !nameText.trim()} className="btn !py-2">
            {looking ? "Looking up…" : "Find by name"}
          </button>
        </div>
        {nameNote && <p className="-mt-1 mb-3 text-sm text-emerald-300">{nameNote}</p>}
        <p className="mb-2 text-xs text-slate-500">Or enter coordinates:</p>
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
          <label className="text-sm text-slate-400">
            Right ascension
            <input className="field mt-1" value={raText} onChange={(e) => setRaText(e.target.value)} placeholder="269.4486 or 17h 57m 48s" />
          </label>
          <label className="text-sm text-slate-400">
            Declination
            <input className="field mt-1" value={decText} onChange={(e) => setDecText(e.target.value)} placeholder="4.7685 or +04d 46m 07s" />
          </label>
          <label className="text-sm text-slate-400">
            Field of view
            <select className="field mt-1" value={fov} onChange={(e) => setFov(Number(e.target.value))}>
              {FOVS.map((f) => (
                <option key={f} value={f}>{f} arcminutes</option>
              ))}
            </select>
          </label>
          <button className="rounded-md bg-cyan-500 px-5 py-2 font-semibold text-slate-950 hover:bg-cyan-400">Show images</button>
        </div>
        {formError && <p className="mt-2 text-sm text-rose-400" role="alert">{formError}</p>}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">Try:</span>
          {TARGETS.map((t) => (
            <button key={t.name} type="button" onClick={() => run({ ra: t.ra, dec: t.dec, fov, band: t.band, mode: query?.mode ?? "seasons" })} className="btn !py-1">
              {t.name}
            </button>
          ))}
        </div>
      </form>

      {query && (
        <div className="mt-6">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <p className="text-sm text-slate-400">
              <span className="font-mono text-slate-200">{formatRa(query.ra)}</span>{" "}
              <span className="font-mono text-slate-200">{formatDec(query.dec)}</span> · {query.fov}′ across
            </p>
            <div>
              <div className="heading !mb-1">View</div>
              <div className="flex gap-1">
                {(
                  [
                    ["seasons", "Visits combined"],
                    ["difference", "Difference"],
                    ["exposures", "Every exposure"],
                  ] as [Mode, string][]
                ).map(([m, label]) => (
                  <button
                    key={m}
                    onClick={() => run({ ...query, mode: m })}
                    aria-pressed={query.mode === m}
                    className={`rounded-md border px-2.5 py-1 text-sm ${query.mode === m ? "border-cyan-400 bg-cyan-500/15 text-cyan-300" : "border-slate-700 text-slate-300 hover:bg-slate-800"}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="heading !mb-1">Detector (wavelength in microns)</div>
              <div className="flex flex-wrap gap-1">
                {DETECTORS.map((d) => {
                  const count = result?.exposures_per_detector[String(d.id)];
                  return (
                    <button
                      key={d.id}
                      onClick={() => run({ ...query, band: d.id })}
                      aria-pressed={query.band === d.id}
                      className={`rounded-md border px-2.5 py-1 text-sm ${query.band === d.id ? "border-cyan-400 bg-cyan-500/15 text-cyan-300" : "border-slate-700 text-slate-300 hover:bg-slate-800"}`}
                    >
                      {d.range}
                      {count != null && <span className="ml-1.5 text-xs text-slate-500">{count}</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {state.kind === "working" && (
            <div className="rounded-lg border border-slate-800 p-8 text-center" role="status">
              <p className="text-slate-300">{progress?.message ?? "Starting"}…</p>
              <div className="mx-auto mt-4 h-2 max-w-md overflow-hidden rounded bg-slate-800">
                <div
                  className={`h-full bg-cyan-500 transition-all ${progress?.total ? "" : "w-1/4 animate-pulse"}`}
                  style={progress?.total ? { width: `${(100 * progress.done) / progress.total}%` } : undefined}
                />
              </div>
              <p className="mt-4 text-xs text-slate-500">A new position can take up to a minute. After that it loads at once.</p>
            </div>
          )}

          {state.kind === "error" && (
            <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-6 text-center" role="alert">
              <p className="text-rose-200">{state.message}</p>
              <button onClick={() => run(query, false)} className="btn mt-4">Try again</button>
            </div>
          )}

          {result && result.frames.length === 0 && (
            <div className="rounded-lg border border-slate-800 p-8 text-center text-slate-300">
              {result.exposures_in_band === 0 && Object.values(result.exposures_per_detector).every((n) => n === 0)
                ? "SPHEREx has no public images of this position yet."
                : result.request.mode === "difference" && result.exposures_in_band > 0
                  ? "Only one visit covers this position with this detector, so there is nothing to subtract yet. Try another view or detector."
                  : "This detector has no usable images of this position. Try another detector."}
            </div>
          )}

          {result && result.frames.length > 0 && (
            <>
              {result.warnings.map((w) => (
                <p key={w} className="mb-3 rounded border border-amber-900/60 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">{w}</p>
              ))}
              <Viewer key={result.key} result={result} />
            </>
          )}
        </div>
      )}

      <footer className="mt-12 border-t border-slate-800 pt-4 text-xs text-slate-500">
        Images: NASA SPHEREx mission, from the NASA/IPAC Infrared Science Archive (IRSA). Built for the NASA Space Apps Challenge 2026,
        &ldquo;Planet X and SPHEREx&rdquo;.
      </footer>
    </main>
  );
}
