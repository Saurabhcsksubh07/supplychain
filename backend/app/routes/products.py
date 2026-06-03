from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Supplier
from ..services import money, predict_stock_shortage

router = APIRouter()


def _product_payload(product: Product, supplier: Supplier) -> dict:
    prediction = predict_stock_shortage(product, supplier)
    if product.current_stock < product.reorder_threshold:
        health = "critical"
    elif product.current_stock < product.reorder_threshold * 1.25:
        health = "watch"
    else:
        health = "healthy"
    return {
        "product_id": product.product_id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "supplier_id": supplier.supplier_id,
        "supplier_name": supplier.name,
        "supplier_city": supplier.city,
        "supplier_reliability": float(supplier.reliability_score),
        "current_stock": product.current_stock,
        "reorder_threshold": product.reorder_threshold,
        "optimal_stock": product.optimal_stock,
        "unit_cost": money(product.unit_cost),
        "health": health,
        "shortage_prediction": prediction,
    }


@router.get("/")
def list_products(
    category: str | None = None,
    health: str | None = None,
    search: str | None = None,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    filters = []
    if category:
        filters.append(Product.category == category)
    if search:
        search_like = f"%{search}%"
        filters.append((Product.name.ilike(search_like)) | (Product.sku.ilike(search_like)))
    if health == "critical":
        filters.append(Product.current_stock < Product.reorder_threshold)
    elif health == "watch":
        filters.append((Product.current_stock >= Product.reorder_threshold) & (Product.current_stock < Product.reorder_threshold * 1.25))
    elif health == "healthy":
        filters.append(Product.current_stock >= Product.reorder_threshold * 1.25)

    base = select(Product, Supplier).join(Supplier)
    count_query = select(func.count(Product.product_id)).join(Supplier)
    if filters:
        base = base.where(*filters)
        count_query = count_query.where(*filters)

    rows = db.execute(base.order_by(Product.current_stock.asc()).offset(offset).limit(limit)).all()
    total = db.scalar(count_query) or 0
    categories = db.execute(select(Product.category).distinct().order_by(Product.category)).scalars().all()

    return {
        "items": [_product_payload(product, supplier) for product, supplier in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "categories": categories,
            "health": ["critical", "watch", "healthy"],
        },
    }
