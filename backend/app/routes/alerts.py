from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert

router = APIRouter()


@router.get("/")
def list_alerts(
    resolved: bool = False,
    severity: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    query = select(Alert).where(Alert.resolved.is_(resolved))
    if severity:
        query = query.where(Alert.severity == severity)
    rows = db.execute(query.order_by(Alert.created_at.desc()).limit(limit)).scalars().all()
    return {
        "items": [
            {
                "alert_id": row.alert_id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "severity": row.severity,
                "title": row.title,
                "message": row.message,
                "resolved": row.resolved,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)) -> dict:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return {
        "alert_id": alert.alert_id,
        "resolved": alert.resolved,
        "title": alert.title,
    }
