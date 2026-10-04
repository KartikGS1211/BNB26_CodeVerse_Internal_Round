from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import InsightMetric
from app.schemas import InsightMetricOut, InsightsOut
from app.seed import VIEWS_SERIES

router = APIRouter()

RECOMMENDATIONS = [
    "Your 'system problem' hook is outperforming your average by 34% — reuse it as the opener on your next three videos.",
    "Clips under 45 seconds retain 22% more viewers. Try trimming clip 5 to its first 30 seconds.",
    "Your audience peaks at 8pm. Schedule tomorrow's export for 19:45 instead of 18:30.",
    "Karaoke-style captions lifted completion on your last two posts — apply them to the next upload.",
]


@router.get("/insights", response_model=InsightsOut)
def get_insights(db: Session = Depends(get_db)):
    metrics = db.query(InsightMetric).all()
    series = [
        {"day": f"Sep {20 + i}", "views": views * 1000}
        for i, views in enumerate(VIEWS_SERIES)
    ]
    return InsightsOut(
        metrics=[InsightMetricOut(
            id=m.id, label=m.label, value=m.value, change=m.change, unit=m.unit
        ) for m in metrics],
        series=series,
        recommendations=RECOMMENDATIONS,
    )
