"use client";
import { useEffect, useRef, useState } from "react";
import { FileAudio, Image as ImageIcon, Loader2, Play, Search, UploadCloud, Video, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Asset, AssetType, TranscriptMoment } from "@/types";
import { useToast } from "@/components/shared/ui";

const iconFor = { video: Video, image: ImageIcon, audio: FileAudio };

export function AssetLibrary() {
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [filter, setFilter] = useState<AssetType | "all">("all");
  const [items, setItems] = useState<Asset[]>([]);
  const [query, setQuery] = useState("");
  const [moments, setMoments] = useState<TranscriptMoment[]>([]);
  const [searching, setSearching] = useState(false);
  const [upload, setUpload] = useState(0);
  const [preview, setPreview] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setItems(await api.getAssets()); } finally { setLoading(false); }
    })();
  }, []);

  const runSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setMoments(await api.searchMoments(query));
    setSearching(false);
  };

  const addFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setUpload(12);
    let p = 12;
    const timer = setInterval(() => { p += 14; setUpload(Math.min(p, 92)); }, 120);
    const next = await api.uploadAsset({ name: files[0].name, type: files[0].type });
    clearInterval(timer);
    setUpload(100);
    setItems(v => [next, ...v]);
    toast("Asset uploaded and auto-tagged");
    setTimeout(() => setUpload(0), 900);
  };

  const shown = items.filter(a => filter === "all" || a.type === filter);

  if (loading) return <div style={{ display: "grid", placeItems: "center", minHeight: 300 }}><Loader2 className="animate-spin" size={28} color="#8b5cf6" /></div>;

  return <>
    <div className="asset-tools">
      <form className="nl-search" onSubmit={runSearch}><Search /><input value={query} onChange={e => setQuery(e.target.value)} placeholder='Try "find where I talk about pricing"' /><button>{searching ? "Searching…" : "Search moments"}</button></form>
      <div className="type-filters">{(["all", "video", "image", "audio"] as const).map(f => <button className={filter === f ? "active" : ""} onClick={() => setFilter(f)} key={f}>{f}</button>)}</div>
    </div>
    {moments.length > 0 && <div className="moment-results"><div><Search /><span>Found in your transcript</span><button onClick={() => setMoments([])}><X /></button></div>{moments.map(m => <button key={m.start} onClick={() => setPreview(items.find(a => a.id === m.assetId) ?? items[0])}><span>{Math.floor(m.start / 60)}:{String(Math.floor(m.start % 60)).padStart(2, "0")}</span><p>"{m.text}"</p><Play /></button>)}</div>}
    <div className="upload-zone" onClick={() => inputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); void addFiles(e.dataTransfer.files) }}><input ref={inputRef} type="file" hidden onChange={e => void addFiles(e.target.files)} /><span><UploadCloud /></span><div><strong>Drop raw footage here</strong><small>or click to browse · MP4, MOV, WAV, JPG up to 5 GB</small></div>{upload > 0 && <div className="upload-progress"><i style={{ width: `${upload}%` }} /><em>{upload}%</em></div>}</div>
    <div className="asset-grid">{shown.map((a, i) => { const Icon = iconFor[a.type]; return <button className="asset-card" key={a.id} onClick={() => setPreview(a)}><div className={`asset-visual asset-bg-${i % 6}`}><Icon /><span>{a.duration ? `${Math.floor(a.duration / 60)}:${String(Math.floor(a.duration % 60)).padStart(2, "0")}` : a.type}</span><i><Play fill="currentColor" /></i></div><div className="asset-info"><strong>{a.name}</strong><small>{a.createdAt}</small><div>{a.tags.map(t => <em key={t}>{t}</em>)}</div></div></button>; })}</div>
    {preview && <div className="modal-backdrop" onMouseDown={() => setPreview(null)}><div className="preview-modal" onMouseDown={e => e.stopPropagation()}><button className="modal-close" onClick={() => setPreview(null)}><X /></button><div className="preview-stage">{preview.type === "video" ? <video controls src={preview.src} /> : preview.type === "audio" ? <audio controls src={preview.src} /> : <ImageIcon />}</div><h3>{preview.name}</h3><div className="tag-row">{preview.tags.map(t => <span key={t}>{t}</span>)}</div></div></div>}
  </>;
}
