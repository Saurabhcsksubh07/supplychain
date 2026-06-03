from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Carrier, Prediction, Product, Shipment, Supplier
from ..services import (
    FEATURE_IMPORTANCE,
    MODEL_METRICS,
    accuracy_history,
    predict_cost_overrun,
    predict_delay,
    predict_stock_shortage,
)

router = APIRouter()


@router.get("/")
def prediction_overview(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(Prediction).order_by(Prediction.created_at.desc()).limit(100)).scalars().all()
    risk_counter = Counter(row.risk_level for row in rows)
    model_counter = Counter(row.model_name for row in rows)
    return {
        "metrics": MODEL_METRICS,
        "risk_distribution": [
            {"risk": "HIGH", "count": risk_counter.get("HIGH", 0)},
            {"risk": "MEDIUM", "count": risk_counter.get("MEDIUM", 0)},
            {"risk": "LOW", "count": risk_counter.get("LOW", 0)},
        ],
        "model_volume": [{"model": model, "count": count} for model, count in model_counter.items()],
        "feature_importance": FEATURE_IMPORTANCE,
        "accuracy_history": accuracy_history(),
        "latest": [
            {
                "prediction_id": row.prediction_id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "model_name": row.model_name,
                "risk_level": row.risk_level,
                "score": float(row.score),
                "confidence": float(row.confidence),
                "explanation": row.explanation,
                "created_at": row.created_at,
            }
            for row in rows[:30]
        ],
    }


@router.post("/delay/{shipment_id}")
def run_delay_prediction(shipment_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        select(Shipment, Carrier).join(Carrier).where(Shipment.shipment_id == shipment_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment, carrier = row
    return predict_delay(shipment, carrier)


@router.post("/cost/{shipment_id}")
def run_cost_prediction(shipment_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        select(Shipment, Carrier).join(Carrier).where(Shipment.shipment_id == shipment_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment, carrier = row
    return predict_cost_overrun(shipment, carrier)


@router.post("/stock/{product_id}")
def run_stock_prediction(product_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        select(Product, Supplier).join(Supplier).where(Product.product_id == product_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product, supplier = row
    return predict_stock_shortage(product, supplier)
