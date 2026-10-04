from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WorkflowCard
from app.schemas import WorkflowCardOut

router = APIRouter()


@router.get("/workflow", response_model=list[WorkflowCardOut])
def list_workflow(db: Session = Depends(get_db)):
    return db.query(WorkflowCard).all()


@router.patch("/workflow/{card_id}", response_model=WorkflowCardOut)
def update_workflow_card(card_id: str, body: WorkflowCardOut, db: Session = Depends(get_db)):
    card = db.get(WorkflowCard, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    card.title = body.title
    card.column = body.column
    card.platform = body.platform
    card.dueDate = body.dueDate
    card.owner = body.owner
    db.commit()
    return card


@router.post("/workflow", response_model=WorkflowCardOut)
def create_workflow_card(body: WorkflowCardOut, db: Session = Depends(get_db)):
    card = WorkflowCard(
        id=body.id or f"w-{len(db.query(WorkflowCard).all()) + 1}",
        title=body.title,
        column=body.column,
        platform=body.platform,
        dueDate=body.dueDate,
        owner=body.owner,
    )
    db.add(card)
    db.commit()
    return card
