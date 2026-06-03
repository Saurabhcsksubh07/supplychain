from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Carrier, Product, Shipment
from ..schemas import ShipmentCreate, ShipmentUpdate
from ..services import money, predict_cost_overrun, predict_delay, route_distance_km

router = APIRouter()


def _shipment_payload(shipment: Shipment, product: Product, carrier: Carrier) -> dict:
    delay = predict_delay(shipment, carrier)
    cost = predict_cost_overrun(shipment, carrier)
    return {
        "shipment_id": shipment.shipment_id,
        "product_id": product.product_id,
        "product_name": product.name,
        "sku": product.sku,
        "carrier_id": carrier.carrier_id,
        "carrier_name": carrier.name,
        "carrier_reliability": float(carrier.reliability_score),
        "origin_city": shipment.origin_city,
        "dest_city": shipment.dest_city,
        "status": shipment.status,
        "distance_km": shipment.distance_km,
        "scheduled_date": shipment.scheduled_date,
        "delivered_date": shipment.delivered_date,
        "estimated_cost": money(shipment.estimated_cost),
        "actual_cost": money(shipment.actual_cost) if shipment.actual_cost is not None else None,
        "delay_prediction": delay,
        "cost_prediction": cost,
    }


@router.get("/")
def list_shipments(
    status: str | None = None,
    city: str | None = None,
    carrier_id: int | None = None,
    search: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    filters = []
    if status:
        filters.append(Shipment.status == status)
    if city:
        filters.append((Shipment.origin_city == city) | (Shipment.dest_city == city))
    if carrier_id:
        filters.append(Shipment.carrier_id == carrier_id)
    if search:
        search_like = f"%{search}%"
        filters.append((Product.name.ilike(search_like)) | (Product.sku.ilike(search_like)))

    base = select(Shipment, Product, Carrier).join(Product).join(Carrier)
    count_query = select(func.count(Shipment.shipment_id)).join(Product).join(Carrier)
    if filters:
        base = base.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    rows = db.execute(
        base.order_by(Shipment.scheduled_date.desc(), Shipment.shipment_id.desc()).offset(offset).limit(limit)
    ).all()

    carriers = db.execute(select(Carrier).order_by(Carrier.name)).scalars().all()
    cities = db.execute(select(Shipment.origin_city).union(select(Shipment.dest_city)).order_by(Shipment.origin_city)).all()

    return {
        "items": [_shipment_payload(shipment, product, carrier) for shipment, product, carrier in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "statuses": ["pending", "in_transit", "delayed", "delivered", "cancelled"],
            "cities": [row[0] for row in cities],
            "carriers": [{"carrier_id": carrier.carrier_id, "name": carrier.name} for carrier in carriers],
        },
    }


@router.get("/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        select(Shipment, Product, Carrier)
        .join(Product)
        .join(Carrier)
        .where(Shipment.shipment_id == shipment_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment, product, carrier = row
    return _shipment_payload(shipment, product, carrier)


@router.post("/", status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, payload.product_id)
    carrier = db.get(Carrier, payload.carrier_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    shipment = Shipment(
        product_id=payload.product_id,
        carrier_id=payload.carrier_id,
        origin_city=payload.origin_city,
        dest_city=payload.dest_city,
        status="pending",
        distance_km=route_distance_km(payload.origin_city, payload.dest_city),
        scheduled_date=payload.scheduled_date,
        estimated_cost=payload.estimated_cost,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return _shipment_payload(shipment, product, carrier)


@router.patch("/{shipment_id}")
def update_shipment(shipment_id: int, payload: ShipmentUpdate, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        select(Shipment, Product, Carrier)
        .join(Product)
        .join(Carrier)
        .where(Shipment.shipment_id == shipment_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment, product, carrier = row
    shipment.status = payload.status
    db.commit()
    db.refresh(shipment)
    return _shipment_payload(shipment, product, carrier)
