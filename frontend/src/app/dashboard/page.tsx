"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Eye, FileText, FolderOpen, Loader2, Play, Plus, Scissors, Sparkles, TrendingUp, Users } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip } from "recharts";
import { api } from "@/lib/api";
import type { InsightMetric, Project } from "@/types";
import { PageIntro } from "@/components/shared/ui";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [metrics, setMetrics] = useState<InsightMetric[]>([]);
  const [series, setSeries] = useState<{ day: string; views: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [p, ins] = await Promise.all([api.getProjects(), api.getInsights()]);
        setProjects(p);
        setMetrics(ins.metrics);
        setSeries(ins.series);
      } finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div style={{ display: "grid", placeItems: "center", minHeight: 300 }}><Loader2 className="animate-spin" size={28} color="#8b5cf6" /></div>;

  const focus = projects[0];
  return <div>
    <PageIntro eyebrow="SATURDAY, OCTOBER 3" title="Good evening, Kunal." copy="Your creative engine is moving. Here's what deserves your attention next." action={<Link className="primary-button" href="/studio/grow-creator"><Plus size={17} /> New project</Link>} />
    <section className="hero-grid">
      {focus && <div className="focus-card"><div className="focus-glow" /><div className="focus-top"><span><i /> CONTINUE WHERE YOU LEFT OFF</span><span>{focus.progress}% complete</span></div><h2>{focus.title}</h2><p>6 AI clips generated · 2 need your review</p><div className="focus-meta"><div><small>NEXT STEP</small><strong>Review the strongest clip</strong></div><Link href={`/studio/${focus.id}`}><Play size={16} fill="currentColor" /> Open studio</Link></div></div>}
      <div className="quick-card"><div className="section-heading"><div><span>QUICK START</span><h3>Move an idea forward</h3></div></div><div className="quick-actions"><Link href="/studio/grow-creator"><span><FileText /></span><div><strong>Generate a script</strong><small>Start from a topic</small></div><ArrowUpRight /></Link><Link href="/assets"><span><FolderOpen /></span><div><strong>Upload footage</strong><small>Add raw source files</small></div><ArrowUpRight /></Link><Link href="/studio/grow-creator"><span><Scissors /></span><div><strong>Find best clips</strong><small>Score key moments</small></div><ArrowUpRight /></Link></div></div>
    </section>
    <section className="stats-grid">{metrics.map((m, i) => <div className="stat-card" key={m.id}><div><span>{[Eye, TrendingUp, Users, Sparkles].map((I, j) => j === i ? <I key={j} /> : null)}</span><small>{m.label}</small></div><strong>{m.id === "views" ? "284.7K" : m.value.toLocaleString() + (m.unit ?? "")}</strong><p><b>↗ {m.change}%</b> vs last period</p></div>)}</section>
    <section className="dashboard-lower">
      <div className="panel"><div className="section-heading"><div><span>ACTIVE WORK</span><h3>Recent projects</h3></div><Link href="/workflow">View workflow <ArrowUpRight size={15} /></Link></div><div className="project-list">{projects.map((p, i) => <Link href={`/studio/${p.id}`} key={p.id}><div className={`project-thumb gradient-${i + 1}`}><Play size={15} /></div><div><strong>{p.title}</strong><small>{p.status} · {p.updatedAt}</small></div><div className="mini-progress"><i style={{ width: `${p.progress}%` }} /></div><span>{p.progress}%</span><ArrowUpRight /></Link>)}</div></div>
      <div className="panel insights-mini"><div className="section-heading"><div><span>LAST 12 DAYS</span><h3>Audience momentum</h3></div><b>+18.4%</b></div><div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={series}><defs><linearGradient id="viewFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8b5cf6" stopOpacity={.45} /><stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} /></linearGradient></defs><Tooltip contentStyle={{ background: "#111425", border: "1px solid #262a40", borderRadius: 12 }} /><Area type="monotone" dataKey="views" stroke="#9b7cff" strokeWidth={3} fill="url(#viewFill)" /></AreaChart></ResponsiveContainer></div><p><Sparkles size={15} /> Your "system problem" hook is outperforming your average by 34%.</p></div>
    </section>
  </div>;
}
