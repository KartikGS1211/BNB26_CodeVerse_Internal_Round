from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Script
from app.schemas import HookGenerateRequest, HookVariant, ScriptGenerateRequest, ScriptOut
from app.services import generator

router = APIRouter()


@router.post("/scripts/generate", response_model=ScriptOut)
def generate_script(body: ScriptGenerateRequest, db: Session = Depends(get_db)):
    generated = generator.generate_script(body.topic, body.niche, body.tone, body.platform)
    script_id = body.model_extra.get("id") if body.model_extra else None
    project_id = body.model_extra.get("projectId") if body.model_extra else None
    if script_id:
        existing = db.get(Script, script_id)
        if existing is not None:
            existing.title = generated["title"]
            existing.topic = body.topic
            existing.niche = body.niche
            existing.tone = body.tone
            existing.platform = body.platform
            existing.lines = [
                {"id": f"line-{i + 1}", "text": text, "order": i}
                for i, text in enumerate(generated["lines"])
            ]
            db.commit()
            return existing
    return Script(
        id=script_id or f"script-{uuid.uuid4().hex[:8]}",
        projectId=project_id or "",
        title=generated["title"],
        topic=body.topic,
        niche=body.niche,
        tone=body.tone,
        platform=body.platform,
        lines=[{"id": f"line-{i + 1}", "text": text, "order": i}
               for i, text in enumerate(generated["lines"])],
    )


@router.post("/hooks/generate", response_model=list[HookVariant])
def generate_hooks(body: HookGenerateRequest, db: Session = Depends(get_db)):
    script_text = ""
    if body.scriptId:
        script = db.get(Script, body.scriptId)
        if script is not None and script.lines:
            script_text = "\n".join(
                line["text"] for line in script.lines if isinstance(line, dict)
            )
    hooks = generator.generate_hooks(script_text)
    return [HookVariant(**hook) for hook in hooks]
