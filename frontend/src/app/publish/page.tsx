"use client";
import { useEffect, useState } from "react";
import { CalendarDays, Check, Clock3, Loader2, Plus, Send } from "lucide-react";
import { api } from "@/lib/api";
import type { Clip, ScheduledPost } from "@/types";
import { PageIntro, useToast } from "@/components/shared/ui";

export default function PublishPage() {
  const toast = useToast();
  const [clips, setClips] = useState<Clip[]>([]);
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [clip, setClip] = useState("");
  const [platform, setPlatform] = useState("Instagram Reels");
  const [date, setDate] = useState("2026-10-05T20:00");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [project, scheduled] = await Promise.all([
          api.getProject("grow-creator"),
          api.getScheduledPosts(),
        ]);
        setClips(project.clips);
        setClip(project.clips[0]?.id ?? "");
        setPosts(scheduled);
      } finally { setLoading(false); }
    })();
  }, []);

  const schedule = async () => {
    const c = clips.find(x => x.id === clip);
    if (!c) return;
    const p = await api.schedulePost({ clipId: c.id, clipTitle: c.title, platform, scheduledAt: date });
    setPosts(v => [...v, p]);
    toast("Post added to your schedule");
  };

  if (loading) return <div style={{ display: "grid", placeItems: "center", minHeight: 300 }}><Loader2 className="animate-spin" size={28} color="#8b5cf6" /></div>;

  return <div>
    <PageIntro eyebrow="PUBLISHING" title="Package once. Show up everywhere." copy="Schedule edited clips with platform-native captions and a clear view of what goes live next." />
    <div className="publish-layout">
      <section className="panel schedule-form">
        <div className="section-heading"><div><span>NEW POST</span><h3>Schedule a clip</h3></div><Plus /></div>
        <label>Clip<select value={clip} onChange={e => setClip(e.target.value)}>{clips.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
        <label>Platform<select value={platform} onChange={e => setPlatform(e.target.value)}>{["YouTube Shorts", "Instagram Reels", "TikTok", "LinkedIn", "X"].map(p => <option key={p}>{p}</option>)}</select></label>
        <label>Date & time<input type="datetime-local" value={date} onChange={e => setDate(e.target.value)} /></label>
        <button className="primary-button" onClick={() => void schedule()}><Send /> Schedule post</button>
      </section>
      <section className="panel calendar-panel">
        <div className="calendar-head"><button>‹</button><strong>October 2026</strong><button>›</button></div>
        <div className="calendar-grid">
          {["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"].map(d => <small key={d}>{d}</small>)}
          {Array.from({ length: 35 }, (_, i) => {
            const day = i - 2;
            const dayPosts = posts.filter(p => new Date(p.scheduledAt).getDate() === day);
            return <div className={day === 3 ? "today" : ""} key={i}><span>{day > 0 && day <= 31 ? day : ""}</span>{dayPosts.map(p => <button key={p.id}><i />{p.platform.replace("Instagram ", "")}<em>{new Date(p.scheduledAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</em></button>)}</div>;
          })}
        </div>
      </section>
      <section className="panel queue-panel">
        <div className="section-heading"><div><span>QUEUE</span><h3>Up next</h3></div><Clock3 /></div>
        {posts.length === 0 ? <p style={{ color: "#788096", padding: 12 }}>No posts scheduled yet.</p> : posts.map(p => <article key={p.id}><span>{p.platform}</span><div><strong>{p.clipTitle}</strong><small>{new Date(p.scheduledAt).toLocaleString()}</small></div><em className={p.status === "published" ? "published" : ""}>{p.status}</em></article>)}
      </section>
    </div>
  </div>;
}
