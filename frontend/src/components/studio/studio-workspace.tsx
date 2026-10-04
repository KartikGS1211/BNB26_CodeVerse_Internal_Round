"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Download, Edit3, Loader2, Pause, Play, Sparkles, WandSparkles, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { Clip, HookVariant, Mapping, Project, Script } from "@/types";
import { AiBadge, ExplainPopover, useToast } from "@/components/shared/ui";
import { TimelineEditor } from "@/components/timeline/timeline-editor";

const tabs = ["Script", "Mapping", "Clips", "Editor", "Export"] as const;
type Tab = typeof tabs[number];
const time = (n: number) => `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, "0")}`;

export function StudioWorkspace({ projectId }: { projectId: string }) {
  const toast = useToast();
  const video = useRef<HTMLVideoElement>(null);
  const [tab, setTab] = useState<Tab>("Editor");
  const [project, setProject] = useState<Project | null>(null);
  const [script, setScript] = useState<Script | null>(null);
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [hooks, setHooks] = useState<HookVariant[]>([]);
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
  const [playing, setPlaying] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [render, setRender] = useState(0);
  const [done, setDone] = useState(false);
  const [renderJobs, setRenderJobs] = useState<{ id: string; platform: string; status: string; progress: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [platforms, setPlatforms] = useState(["YouTube Shorts", "Instagram Reels"]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getProject(projectId);
        if (cancelled) return;
        setProject(data.project);
        setScript(data.script);
        setMappings(data.mappings);
        setClips(data.clips);
        setSelectedClip(data.clips[0] ?? null);
        const hookList = await api.generateHooks(data.script.id);
        if (!cancelled) setHooks(hookList);
      } catch {
        if (!cancelled) toast("Failed to load project");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [projectId]);

  const fullText = useMemo(() => script?.lines.map(l => l.text).join("\n\n") ?? "", [script]);

  const generate = async () => {
    if (!script) return;
    setGenerating(true);
    try {
      const fresh = await api.generateScript(script);
      setScript(fresh);
      toast("Fresh script generated");
    } finally { setGenerating(false); }
  };

  const applyHook = (text: string) => {
    setScript(s => s ? { ...s, lines: [{ ...s.lines[0], text }, ...s.lines.slice(1)] } : s);
    toast("Hook added to the opening line");
  };

  const seek = (m: Mapping) => {
    setTab("Mapping");
    if (video.current) { video.current.currentTime = m.start; void video.current.play(); }
  };

  const preview = (clip: Clip) => {
    setSelectedClip(clip);
    setPlaying(true);
    setTimeout(() => {
      if (video.current) {
        video.current.currentTime = clip.start;
        void video.current.play();
        const tick = () => {
          if (video.current && video.current.currentTime >= clip.end) { video.current.pause(); setPlaying(false); }
          else requestAnimationFrame(tick);
        };
        tick();
      }
    }, 50);
  };

  const startRender = async () => {
    if (!selectedClip) return;
    setDone(false);
    setRender(8);
    const jobs = await Promise.all(platforms.map(async p => {
      const r = await api.renderTimeline(`timeline-${selectedClip.id}`, p);
      return { id: r.renderId, platform: p, status: r.status, progress: 0 };
    }));
    setRenderJobs(jobs);
    for (const p of [24, 43, 66, 84]) { await new Promise(r => setTimeout(r, 250)); setRender(p); }
    const poll = async () => {
      const updated = await Promise.all(jobs.map(async j => {
        const s = await api.getRenderStatus(j.id);
        return { ...j, status: s.status, progress: s.progress };
      }));
      setRenderJobs(updated);
      const allDone = updated.every(j => j.status === "done" || j.status === "failed");
      if (!allDone) setTimeout(poll, 1000);
      else { setRender(100); setDone(true); toast("Render complete — your exports are ready"); }
    };
    poll();
  };

  if (loading) return <div className="studio"><div style={{ display: "grid", placeItems: "center", minHeight: 300 }}><Loader2 className="animate-spin" size={28} color="#8b5cf6" /></div></div>;
  if (!project || !script) return <div className="studio"><p style={{ padding: 24, color: "#788096" }}>Project not found.</p></div>;

  return <div className="studio">
    <div className="studio-heading">
      <div><span>PROJECT / AI STUDIO</span><h1>{project.title}</h1><p><i />Autosaved just now · Source: creator-growth-master.mp4</p></div>
      <button onClick={() => toast("Project saved")}><Check /> Saved</button>
    </div>
    <div className="studio-tabs">{tabs.map((t, i) => <button className={tab === t ? "active" : ""} onClick={() => setTab(t)} key={t}><span>{i + 1}</span>{t}{t === "Clips" && <em>{clips.length}</em>}</button>)}</div>

    {tab === "Script" && <div className="script-layout">
      <section className="panel">
        <div className="section-heading"><div><span>AI SCRIPT LAB</span><h3>Shape the core idea</h3></div><AiBadge /></div>
        <div className="form-grid">
          <label>Topic<input value={script.topic} onChange={e => setScript({ ...script, topic: e.target.value })} /></label>
          <label>Niche<input value={script.niche} onChange={e => setScript({ ...script, niche: e.target.value })} /></label>
          <label>Tone<select value={script.tone} onChange={e => setScript({ ...script, tone: e.target.value })}><option>Warm & direct</option><option>Bold</option><option>Educational</option></select></label>
          <label>Platform<select value={script.platform} onChange={e => setScript({ ...script, platform: e.target.value })}><option>YouTube</option><option>TikTok</option><option>LinkedIn</option></select></label>
        </div>
        <button className="primary-button" onClick={() => void generate()}><WandSparkles />{generating ? "Writing…" : "Generate script"}</button>
        <textarea className="script-editor" value={fullText} onChange={e => setScript({ ...script, lines: e.target.value.split("\n\n").map((text, i) => ({ id: `line-${i + 1}`, text, order: i })) })} />
      </section>
      <aside className="panel hooks-panel">
        <div className="section-heading"><div><span>A/B HOOK LAB</span><h3>5 opening variants</h3></div><Zap /></div>
        {hooks.map((h, i) => <div className="hook-row" key={h.id}><div><span>0{i + 1}</span><p>{h.text}</p></div><div className="score-bar"><i style={{ width: `${h.score}%` }} /><span>{h.score}</span></div><button onClick={() => applyHook(h.text)}>Use this hook</button></div>)}
      </aside>
    </div>}

    {tab === "Mapping" && <div className="mapping-layout">
      <section className="panel mapping-lines">
        <div className="section-heading"><div><span>SCRIPT → FOOTAGE</span><h3>Click a line to find its moment</h3></div><AiBadge>{mappings.length} lines mapped</AiBadge></div>
        {script.lines.map((line, i) => {
          const m = mappings[i];
          if (!m) return null;
          const level = m.confidence > .85 ? "high" : m.confidence > .73 ? "medium" : "low";
          return <button key={line.id} onClick={() => seek(m)}><span>{String(i + 1).padStart(2, "0")}</span><p>{line.text}</p><div><em className={level}>{Math.round(m.confidence * 100)}%</em><small>{time(m.start)}–{time(m.end)}</small></div></button>;
        })}
      </section>
      <section className="mapping-video">
        <div className="video-stage"><video ref={video} controls src="/demo/sample.mp4" /></div>
        <div className="mapping-adjust"><strong>Manual re-map</strong>
          <label>Start<input type="number" step=".1" value={mappings[0]?.start ?? 0} onChange={e => setMappings(v => v.map((m, i) => i ? m : { ...m, start: +e.target.value }))} /></label>
          <label>End<input type="number" step=".1" value={mappings[0]?.end ?? 0} onChange={e => setMappings(v => v.map((m, i) => i ? m : { ...m, end: +e.target.value }))} /></label>
        </div>
        <div className="footage-bar">{mappings.map((m, i) => <button title={`Line ${i + 1}`} onClick={() => seek(m)} key={m.scriptLineId} style={{ left: `${m.start / 1.2}%`, width: `${(m.end - m.start) / 1.2}%`, background: i % 3 === 0 ? "#8b5cf6" : i % 3 === 1 ? "#33d8e5" : "#f5b94c" }} />)}</div>
        <div className="confidence-key"><span><i className="high" />High</span><span><i className="medium" />Needs review</span><span><i className="low" />Low</span></div>
      </section>
    </div>}

    {tab === "Clips" && <>
      <div className="clips-summary"><div><Sparkles /><span><strong>{clips.length} clips found</strong><small>AI ranked these by hook strength, completeness, and predicted retention.</small></span></div><button onClick={() => toast("Clips regenerated from the latest mapping")}><WandSparkles /> Regenerate clips</button></div>
      <div className="clips-grid">{clips.map((clip, i) => <article className="clip-card" key={clip.id}>
        <div className={`clip-preview clip-bg-${i}`}><div className="score-ring" style={{ "--score": `${clip.score * 3.6}deg` } as React.CSSProperties}><span>{clip.score}</span></div><button onClick={() => preview(clip)}>{playing && selectedClip?.id === clip.id ? <Pause /> : <Play fill="currentColor" />}</button><span>{time(clip.end - clip.start)}</span></div>
        <div className="clip-copy"><small>CLIP {i + 1} · {time(clip.start)}–{time(clip.end)}</small><h3>{clip.title}</h3><p>"{clip.hook}"</p><button className="why" onClick={() => setExpanded(expanded === clip.id ? null : clip.id)}>Why this clip? <ChevronDown /></button>{expanded === clip.id && <ul>{clip.reasons.map(r => <li key={r}><Check />{r}</li>)}</ul>}<div><ExplainPopover reasons={clip.reasons} /><button className="ghost-button" onClick={() => preview(clip)}><Play /> Preview</button><button className="primary-button" onClick={() => { setSelectedClip(clip); setTab("Editor"); }}><Edit3 /> Edit</button></div></div>
      </article>)}</div>
      <video ref={video} className="clip-floating-video" src="/demo/sample.mp4" controls={playing} />
    </>}

    {tab === "Editor" && <TimelineEditor />}

    {tab === "Export" && <div className="export-layout">
      <section className="panel export-options">
        <div className="section-heading"><div><span>EXPORT PACKAGE</span><h3>Choose destinations</h3></div><AiBadge>Captions adapted</AiBadge></div>
        {["YouTube Shorts", "Instagram Reels", "TikTok", "LinkedIn", "X"].map(p => <label className="platform-option" key={p}><input type="checkbox" checked={platforms.includes(p)} onChange={e => setPlatforms(v => e.target.checked ? [...v, p] : v.filter(x => x !== p))} /><span>{p.slice(0, 2)}</span><div><strong>{p}</strong><small>{p === "X" && selectedClip && selectedClip.end - selectedClip.start > 140 ? "Duration warning: keep video under 2:20" : "Ready for export"}</small></div><Check /></label>)}
      </section>
      <section className="panel caption-export">
        <div className="section-heading"><div><span>PLATFORM COPY</span><h3>Review captions</h3></div></div>
        {platforms.map(p => <label key={p}><span>{p}</span><textarea defaultValue={selectedClip?.platformCaptions[p] ?? ""} /><small>{selectedClip?.platformCaptions[p]?.length ?? 0} characters</small></label>)}
        <button className="render-button" onClick={() => void startRender()} disabled={!platforms.length || render > 0 && render < 100}>{done ? <><Download /> Download {platforms.length} exports</> : <><Sparkles /> Render {platforms.length} versions</>}</button>
        {render > 0 && <div className="render-progress"><i style={{ width: `${render}%` }} /><span>{done ? "Render complete" : `Rendering ${render}%`}</span></div>}
        {renderJobs.length > 0 && <div style={{ marginTop: 12, display: "grid", gap: 8 }}>{renderJobs.map(j => <div key={j.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#788096" }}><span style={{ flex: 1 }}>{j.platform}</span><span style={{ color: j.status === "done" ? "#4ade80" : "#f5b94c" }}>{j.status} {j.progress}%</span>{j.status === "done" && j.id && <a href={`/renders/${j.id}`} style={{ color: "#7657dd" }}>Download</a>}</div>)}</div>}
      </section>
    </div>}
  </div>;
}
