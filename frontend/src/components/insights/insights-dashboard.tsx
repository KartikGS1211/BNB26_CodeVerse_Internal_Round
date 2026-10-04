"use client";
import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowUpRight, Clock, Lightbulb, Loader2, Sparkles, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { InsightMetric } from "@/types";

const hookData = [{ name: "System problem", score: 96 }, { name: "One recording", score: 93 }, { name: "Burnout loop", score: 89 }, { name: "Stop starting", score: 86 }, { name: "Travel further", score: 82 }];
const times = [{ time: "8am", engagement: 46 }, { time: "11am", engagement: 58 }, { time: "2pm", engagement: 38 }, { time: "5pm", engagement: 72 }, { time: "8pm", engagement: 91 }, { time: "11pm", engagement: 53 }];
const scatter = [{ score: 60, views: 12 }, { score: 72, views: 29 }, { score: 76, views: 41 }, { score: 86, views: 58 }, { score: 91, views: 83 }, { score: 94, views: 102 }, { score: 98, views: 136 }];

export function InsightsDashboard() {
  const [metrics, setMetrics] = useState<InsightMetric[]>([]);
  const [series, setSeries] = useState<{ day: string; views: number }[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.getInsights();
        setMetrics(data.metrics);
        setSeries(data.series);
        setRecommendations(data.recommendations);
      } finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div style={{ display: "grid", placeItems: "center", minHeight: 300 }}><Loader2 className="animate-spin" size={28} color="#8b5cf6" /></div>;

  return <>
    <div className="insight-stats">{metrics.map(m => <div className="stat-card" key={m.id}><small>{m.label}</small><strong>{m.id === "views" ? "284.7K" : m.value.toLocaleString() + (m.unit ?? "")}</strong><p><ArrowUpRight /> {m.change}% this month</p></div>)}</div>
    <div className="insight-grid">
      <section className="panel wide-chart"><div className="section-heading"><div><span>REACH</span><h3>Views over time</h3></div><b>Sep 20 — Oct 1</b></div><ResponsiveContainer width="100%" height={270}><AreaChart data={series}><defs><linearGradient id="purple" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8b5cf6" stopOpacity=".5" /><stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" /></linearGradient></defs><CartesianGrid stroke="#202438" vertical={false} /><XAxis dataKey="day" tick={{ fill: "#737b91", fontSize: 9 }} axisLine={false} /><YAxis tick={{ fill: "#737b91", fontSize: 9 }} axisLine={false} /><Tooltip contentStyle={{ background: "#111425", border: "1px solid #30364c" }} /><Area dataKey="views" stroke="#a285ff" strokeWidth={3} fill="url(#purple)" /></AreaChart></ResponsiveContainer></section>
      <section className="panel"><div className="section-heading"><div><span>CREATIVE</span><h3>Best-performing hooks</h3></div><Zap /></div><ResponsiveContainer width="100%" height={270}><BarChart data={hookData} layout="vertical"><XAxis type="number" hide /><YAxis dataKey="name" type="category" width={90} tick={{ fill: "#8e95aa", fontSize: 9 }} axisLine={false} /><Tooltip contentStyle={{ background: "#111425", border: "1px solid #30364c" }} /><Bar dataKey="score" radius={[0, 5, 5, 0]}>{hookData.map((_, i) => <Cell key={i} fill={i === 0 ? "#9b7cff" : "#51447c"} />)}</Bar></BarChart></ResponsiveContainer></section>
      <section className="panel"><div className="section-heading"><div><span>TIMING</span><h3>Best posting times</h3></div><Clock /></div><ResponsiveContainer width="100%" height={230}><LineChart data={times}><CartesianGrid stroke="#202438" vertical={false} /><XAxis dataKey="time" tick={{ fill: "#737b91", fontSize: 9 }} axisLine={false} /><YAxis tick={{ fill: "#737b91", fontSize: 9 }} axisLine={false} /><Tooltip contentStyle={{ background: "#111425", border: "1px solid #30364c" }} /><Line type="monotone" dataKey="engagement" stroke="#33d8e5" strokeWidth={3} dot={{ fill: "#33d8e5", r: 4 }} /></LineChart></ResponsiveContainer></section>
      <section className="panel"><div className="section-heading"><div><span>QUALITY</span><h3>Score vs. views</h3></div><Sparkles /></div><ResponsiveContainer width="100%" height={230}><ScatterChart><CartesianGrid stroke="#202438" /><XAxis dataKey="score" name="Score" tick={{ fill: "#737b91", fontSize: 9 }} /><YAxis dataKey="views" name="Views (K)" tick={{ fill: "#737b91", fontSize: 9 }} /><Tooltip contentStyle={{ background: "#111425", border: "1px solid #30364c" }} /><Scatter data={scatter} fill="#8b5cf6" /></ScatterChart></ResponsiveContainer></section>
    </div>
    <section className="panel recommendations"><div className="section-heading"><div><span>AI RECOMMENDATIONS</span><h3>What to do next</h3></div><Lightbulb /></div>{recommendations.map((r, i) => <div key={i}><Sparkles size={14} /><p>{r}</p></div>)}</section>
  </>;
}
