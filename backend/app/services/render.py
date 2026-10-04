"""Timeline rendering: turns a JSON timeline into a platform-specific file.

Uses FFmpeg when available (real cuts, aspect reframing, burned captions,
music mix). Falls back to a simulated job so the UI flow always works —
e.g. on a laptop without FFmpeg during a hackathon demo.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from app.config import DATA_DIR, RENDER_DIR
from app.db import SessionLocal
from app.models import RenderJob

ASPECT_SIZES = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}
PLATFORM_SLUG = {
    "YouTube Shorts": "youtube-shorts", "Instagram Reels": "instagram-reels",
    "TikTok": "tiktok", "LinkedIn": "linkedin", "X": "x",
}


FFMPEG_PATH = r"C:\Users\roder\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None or Path(FFMPEG_PATH).exists()


def ffmpeg_exe() -> str:
    return shutil.which("ffmpeg") or FFMPEG_PATH


def resolve_source(src: str) -> Path | None:
    """Resolve a timeline video src to a local file path.
    Handles URL paths like /demo/sample.mp4 and /media/sample.mp4."""
    if src.startswith("http://") or src.startswith("https://"):
        return None
    if src.startswith("/demo/") or src.startswith("/media/"):
        name = src.split("/")[-1]
        candidate = DATA_DIR / "demo" / name
        if candidate.exists():
            return candidate
    path = Path(src)
    return path if path.exists() else None


def _ass_path(job_id: str) -> Path:
    return RENDER_DIR / f"{job_id}.ass"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def _srt_time(seconds: float) -> str:
    centiseconds = int(round(seconds * 100))
    h, rem = divmod(centiseconds, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _write_ass(timeline: dict, path: Path, brand_color: str = "&H00FFFF00") -> None:
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,DejaVu Sans,64,{brand_color},&H00FFFFFF,&H00000000,"
        "&H64000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,180,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for track in timeline.get("tracks", []):
        if track["type"] != "caption":
            continue
        for item in track.get("items", []):
            text = _escape_ass(str(item.get("text") or ""))
            if not text:
                continue
            lines.append(
                f"Dialogue: 0,{_srt_time(item['start'])},{_srt_time(item['end'])},"
                f"Default,,0,0,0,,{text}"
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def _filter_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


def _video_filter_chain(timeline: dict, ass: Path, width: int, height: int) -> tuple[str, str]:
    """Return (filter_complex, output_label) for the video track."""
    video_items = [i for t in timeline.get("tracks", []) if t["type"] == "video" for i in t.get("items", [])]
    scale = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"
    parts: list[str] = []
    if len(video_items) == 1:
        parts.append(f"[0:v]{scale}[base]")
    else:
        for idx in range(len(video_items)):
            parts.append(f"[{idx}:v]{scale},setpts=PTS-STARTPTS[v{idx}]")
        parts.append("".join(f"[v{i}]" for i in range(len(video_items))) +
                     f"concat=n={len(video_items)}:v=1:a=0[base]")
    parts.append(f"[base]subtitles={_filter_path(ass)}[vout]")
    return ";".join(parts), "[vout]"


def _run_ffmpeg(timeline: dict, platform: str, output: Path) -> None:
    video_items = [i for t in timeline.get("tracks", []) if t["type"] == "video" for i in t.get("items", [])]
    if not video_items:
        raise RuntimeError("Timeline has no video track")

    resolved_items = []
    for item in video_items:
        local = resolve_source(str(item.get("src", "")))
        if local is None:
            raise RuntimeError(f"Source not found: {item.get('src')}")
        resolved_items.append({**item, "src": str(local)})

    width, height = ASPECT_SIZES.get(timeline.get("aspect", "9:16"), (1080, 1920))
    duration = max(i["end"] for t in timeline.get("tracks", []) for i in t.get("items", []))

    ass = _ass_path(output.stem)
    _write_ass(timeline, ass)

    filter_complex, video_label = _video_filter_chain(timeline, ass, width, height)

    inputs: list[str] = []
    for item in resolved_items:
        inputs += ["-ss", f"{item['start']:.3f}", "-to", f"{item['end']:.3f}", "-i", str(item.get("src", ""))]

    music_items = [i for t in timeline.get("tracks", []) if t["type"] == "music" for i in t.get("items", [])]
    real_music = [i for i in music_items if Path(str(i.get("src", ""))).exists()]

    cmd = [ffmpeg_exe(), "-y", *inputs]
    if real_music:
        item = real_music[0]
        volume = float(item.get("style", {}).get("volume", 0.18))
        music_index = len(video_items)
        cmd += ["-stream_loop", "-1", "-i", str(item["src"])]
        filter_complex += f";[{music_index}:a]atrim=0:{duration:.3f},volume={volume}[a]"
        cmd += ["-filter_complex", filter_complex, "-map", video_label, "-map", "[a]",
                "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(output)]
    else:
        cmd += ["-filter_complex", filter_complex, "-map", video_label,
                "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(output)]

    subprocess.run(cmd, check=True, capture_output=True, timeout=600)


def _simulate(job_id: str, total: float = 6.0) -> None:
    db = SessionLocal()
    try:
        job = db.get(RenderJob, job_id)
        if not job:
            return
        steps = 12
        for step in range(1, steps + 1):
            time.sleep(total / steps)
            job.progress = int(100 * step / steps)
            job.status = "processing"
            db.commit()
        job.status = "done"
        job.progress = 100
        job.note = "Simulated render (FFmpeg not available on this machine)"
        db.commit()
    finally:
        db.close()


def _render_worker(job_id: str) -> None:
    timeline = None
    platform = ""
    db = SessionLocal()
    try:
        job = db.get(RenderJob, job_id)
        if job is None:
            return
        timeline = job.payload or {}
        platform = job.platform
        job.status = "processing"
        job.progress = 5
        db.commit()
    finally:
        db.close()

    if not timeline:
        return

    slug = PLATFORM_SLUG.get(platform, platform.lower().replace(" ", "-"))
    output = RENDER_DIR / f"{job_id}_{slug}.mp4"

    has_real_source = any(
        resolve_source(str(i.get("src", ""))) is not None
        for t in timeline.get("tracks", []) if t["type"] == "video"
        for i in t.get("items", [])
    )

    if ffmpeg_available() and has_real_source:
        try:
            _run_ffmpeg(timeline, platform, output)
            db = SessionLocal()
            try:
                job = db.get(RenderJob, job_id)
                job.status = "done"
                job.progress = 100
                job.outputUrl = f"/renders/{output.name}"
                job.note = "Rendered with FFmpeg"
                db.commit()
            finally:
                db.close()
            return
        except Exception as exc:
            db = SessionLocal()
            try:
                job = db.get(RenderJob, job_id)
                job.error = str(exc)[:500]
                db.commit()
            finally:
                db.close()

    _simulate(job_id)


def queue_render(timeline: dict, platform: str) -> RenderJob:
    db = SessionLocal()
    try:
        job = RenderJob(
            id=f"render-{uuid.uuid4().hex[:12]}",
            timelineId=timeline.get("id", ""),
            platform=platform,
            status="queued",
            progress=0,
            payload=timeline,
        )
        db.add(job)
        db.commit()
        # Detached snapshot: the worker thread may flip status to
        # "processing" before we return, so hand back the created job
        # rather than re-querying it.
        result = RenderJob(
            id=job.id, timelineId=job.timelineId, platform=job.platform,
            status="queued", progress=0,
        )
    finally:
        db.close()

    threading.Thread(target=_render_worker, args=(result.id,), daemon=True).start()
    return result
