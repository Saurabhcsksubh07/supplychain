from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Prediction, Product, Shipment, StockMovement
from ..services import MODEL_METRICS, money

router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    total_shipments = db.scalar(select(func.count(Shipment.shipment_id))) or 0
    active_shipments = db.scalar(
        select(func.count(Shipment.shipment_id)).where(Shipment.status.in_(["pending", "in_transit", "delayed"]))
    ) or 0
    high_risk_shipments = db.scalar(
        select(func.count(func.distinct(Prediction.entity_id))).where(
            Prediction.entity_type == "shipment",
            Prediction.risk_level == "HIGH",
        )
    ) or 0
    low_stock_products = db.scalar(
        select(func.count(Product.product_id)).where(Product.current_stock < Product.reorder_threshold)
    ) or 0
    open_alerts = db.scalar(select(func.count(Alert.alert_id)).where(Alert.resolved.is_(False))) or 0
    avg_accuracy = round(sum(model["accuracy"] for model in MODEL_METRICS) / len(MODEL_METRICS), 3)

    status_rows = db.execute(select(Shipment.status, func.count()).group_by(Shipment.status)).all()
    status_distribution = [{"status": status.replace("_", " ").title(), "count": count} for status, count in status_rows]

    category_rows = db.execute(
        select(Product.category, func.avg(Product.current_stock), func.avg(Product.reorder_threshold))
        .group_by(Product.category)
        .order_by(Product.category)
    ).all()
    category_stock = [
        {
            "category": category,
            "avg_stock": round(float(avg_stock), 1),
            "avg_threshold": round(float(avg_threshold), 1),
        }
        for category, avg_stock, avg_threshold in category_rows
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    movement_rows = db.execute(
        select(StockMovement.timestamp, StockMovement.quantity).where(StockMovement.timestamp >= cutoff)
    ).all()
    daily_volume: dict[str, int] = defaultdict(int)
    for timestamp, quantity in movement_rows:
        key = timestamp.date().isoformat()
        daily_volume[key] += abs(quantity)
    stock_trend = [
        {"date": (date.today() - timedelta(days=days)).isoformat(), "movement": daily_volume.get((date.today() - timedelta(days=days)).isoformat(), 0)}
        for days in range(29, -1, -1)
    ]

    route_rows = db.execute(
        select(Shipment.origin_city, Shipment.dest_city, Shipment.status, Shipment.estimated_cost)
        .where(Shipment.status.in_(["delayed", "in_transit"]))
        .limit(300)
    ).all()
    route_counts: dict[str, Counter] = defaultdict(Counter)
    route_costs: dict[str, float] = defaultdict(float)
    for origin, dest, status, estimated_cost in route_rows:
        key = f"{origin} -> {dest}"
        route_counts[key][status] += 1
        route_costs[key] += float(estimated_cost)
    route_risks = []
    for route, counts in route_counts.items():
        delayed = counts.get("delayed", 0)
        total = sum(counts.values())
        if total:
            route_risks.append(
                {
                    "route": route,
                    "delayed": delayed,
                    "active": total,
                    "delay_rate": round(delayed / total, 2),
                    "estimated_cost": money(route_costs[route]),
                }
            )
    route_risks.sort(key=lambda item: (item["delay_rate"], item["active"]), reverse=True)

    alerts = db.execute(
        select(Alert)
        .where(Alert.resolved.is_(False))
        .order_by(Alert.severity.desc(), Alert.created_at.desc())
        .limit(8)
    ).scalars()

    return {
        "kpis": {
            "total_shipments": total_shipments,
            "active_shipments": active_shipments,
            "high_risk_shipments": high_risk_shipments,
            "low_stock_products": low_stock_products,
            "open_alerts": open_alerts,
            "average_model_accuracy": avg_accuracy,
            "seeded_records": "11,700+",
        },
        "status_distribution": status_distribution,
        "stock_trend": stock_trend,
        "category_stock": category_stock,
        "route_risks": route_risks[:6],
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "entity_type": alert.entity_type,
                "entity_id": alert.entity_id,
                "created_at": alert.created_at,
            }
            for alert in alerts
        ],
        "report_context": {
            "project": "Supply Chain Command Centre with Predictive Intelligence",
            "market": "Indian logistics, warehouse, supplier, and shipment operations",
            "stack": "FastAPI, Vue.js 3, Chart.js, SQLAlchemy, SQLite demo/PostgreSQL-ready",
        },
    }
