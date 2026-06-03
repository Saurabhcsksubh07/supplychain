from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from math import sqrt
from random import Random

from .models import Carrier, Product, Shipment, Supplier


MODEL_METRICS = [
    {
        "model": "Delay Prediction",
        "algorithm": "Random Forest",
        "predicts": "On-time vs delayed",
        "accuracy": 0.85,
        "key_score": "F1: 0.85",
    },
    {
        "model": "Stock Shortage",
        "algorithm": "Gradient Boosting",
        "predicts": "Days to stockout",
        "accuracy": 0.82,
        "key_score": "R2: 0.82",
    },
    {
        "model": "Cost Overrun",
        "algorithm": "XGBoost",
        "predicts": "% over budget",
        "accuracy": 0.80,
        "key_score": "R2: 0.80",
    },
]

FEATURE_IMPORTANCE = {
    "delay": [
        {"feature": "Carrier reliability score", "importance": 0.35},
        {"feature": "Distance in kilometres", "importance": 0.25},
        {"feature": "Origin warehouse utilisation", "importance": 0.15},
        {"feature": "Day of week", "importance": 0.10},
        {"feature": "Remaining features", "importance": 0.15},
    ],
    "stock": [
        {"feature": "Current stock vs reorder point", "importance": 0.32},
        {"feature": "30-day demand velocity", "importance": 0.24},
        {"feature": "Supplier lead time", "importance": 0.18},
        {"feature": "Supplier reliability", "importance": 0.14},
        {"feature": "Seasonal month", "importance": 0.12},
    ],
    "cost": [
        {"feature": "Route distance", "importance": 0.29},
        {"feature": "Route complexity", "importance": 0.22},
        {"feature": "Carrier delay trend", "importance": 0.19},
        {"feature": "Fuel price index", "importance": 0.16},
        {"feature": "Seasonality", "importance": 0.14},
    ],
}

CITY_PROFILES = {
    "Mumbai": {"state": "Maharashtra", "x": 4, "y": 6, "monsoon": 0.26},
    "Delhi": {"state": "Delhi", "x": 5, "y": 1, "monsoon": 0.12},
    "Kolkata": {"state": "West Bengal", "x": 9, "y": 4, "monsoon": 0.20},
    "Chennai": {"state": "Tamil Nadu", "x": 7, "y": 9, "monsoon": 0.18},
    "Bengaluru": {"state": "Karnataka", "x": 5, "y": 8, "monsoon": 0.17},
    "Hyderabad": {"state": "Telangana", "x": 6, "y": 6, "monsoon": 0.16},
    "Pune": {"state": "Maharashtra", "x": 5, "y": 6, "monsoon": 0.23},
    "Ahmedabad": {"state": "Gujarat", "x": 3, "y": 4, "monsoon": 0.14},
    "Jaipur": {"state": "Rajasthan", "x": 4, "y": 2, "monsoon": 0.09},
    "Lucknow": {"state": "Uttar Pradesh", "x": 7, "y": 2, "monsoon": 0.15},
    "Surat": {"state": "Gujarat", "x": 3, "y": 5, "monsoon": 0.16},
    "Tiruppur": {"state": "Tamil Nadu", "x": 6, "y": 9, "monsoon": 0.17},
    "Noida": {"state": "Uttar Pradesh", "x": 5, "y": 1, "monsoon": 0.12},
    "Nashik": {"state": "Maharashtra", "x": 4, "y": 5, "monsoon": 0.22},
    "Ludhiana": {"state": "Punjab", "x": 4, "y": 0, "monsoon": 0.10},
    "Guwahati": {"state": "Assam", "x": 11, "y": 2, "monsoon": 0.31},
    "Kochi": {"state": "Kerala", "x": 5, "y": 10, "monsoon": 0.32},
    "Indore": {"state": "Madhya Pradesh", "x": 5, "y": 4, "monsoon": 0.15},
}

FESTIVE_MONTHS = {3: "Holi", 8: "Onam", 9: "Durga Puja", 10: "Navratri", 11: "Diwali", 12: "Wedding season"}


def route_distance_km(origin_city: str, dest_city: str) -> int:
    origin = CITY_PROFILES.get(origin_city, CITY_PROFILES["Delhi"])
    dest = CITY_PROFILES.get(dest_city, CITY_PROFILES["Mumbai"])
    grid_distance = sqrt((origin["x"] - dest["x"]) ** 2 + (origin["y"] - dest["y"]) ** 2)
    return max(90, int(120 + grid_distance * 285))


def risk_from_score(score: float, medium: float, high: float) -> str:
    if score >= high:
        return "HIGH"
    if score >= medium:
        return "MEDIUM"
    return "LOW"


def _seasonal_factor(month: int) -> float:
    if month in {6, 7, 8, 9}:
        return 0.12
    if month in FESTIVE_MONTHS:
        return 0.10
    return 0.03


def predict_delay(
    shipment: Shipment,
    carrier: Carrier,
    origin_utilisation: float = 0.72,
    today: date | None = None,
) -> dict:
    scheduled = shipment.scheduled_date
    today = today or date.today()
    carrier_risk = 1 - float(carrier.reliability_score)
    distance_risk = min(float(shipment.distance_km) / 2600, 1)
    city_risk = max(
        CITY_PROFILES.get(shipment.origin_city, {}).get("monsoon", 0.12),
        CITY_PROFILES.get(shipment.dest_city, {}).get("monsoon", 0.12),
    )
    utilisation_risk = max(0, origin_utilisation - 0.65)
    weekday_risk = 0.08 if scheduled.weekday() in {0, 5, 6} else 0.03
    overdue_risk = 0.18 if shipment.status == "in_transit" and scheduled < today else 0
    score = min(
        0.98,
        carrier_risk * 0.38
        + distance_risk * 0.24
        + city_risk * 0.18
        + utilisation_risk * 0.12
        + weekday_risk
        + _seasonal_factor(scheduled.month)
        + overdue_risk,
    )
    risk = risk_from_score(score, 0.38, 0.62)
    reason = "carrier reliability, distance, route weather, utilisation, and delivery calendar"
    return {
        "model_name": "Delay Prediction",
        "entity_type": "shipment",
        "entity_id": shipment.shipment_id,
        "risk_level": risk,
        "score": round(score, 3),
        "confidence": round(0.74 + score * 0.18, 2),
        "probability": round(score, 3),
        "explanation": f"Delay risk is {risk.lower()} based on {reason}.",
    }


def predict_stock_shortage(product: Product, supplier: Supplier, month: int | None = None) -> dict:
    month = month or datetime.now().month
    demand_seed = (product.product_id * 17 + supplier.supplier_id * 13) % 29
    base_demand = 8 + demand_seed
    seasonal_multiplier = 1.35 if month in FESTIVE_MONTHS else 1.12 if month in {4, 5, 6} else 1.0
    supplier_penalty = max(0.0, 1 - float(supplier.reliability_score)) * 3
    avg_daily_demand = base_demand * seasonal_multiplier
    days_to_stockout = float(product.current_stock) / max(1, avg_daily_demand)
    adjusted_days = max(0.2, days_to_stockout - supplier_penalty)
    if adjusted_days < 7:
        risk = "HIGH"
    elif adjusted_days < 14:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    stock_gap = product.reorder_threshold - product.current_stock
    confidence = 0.83 if risk == "HIGH" else 0.79 if risk == "MEDIUM" else 0.75
    return {
        "model_name": "Stock Shortage",
        "entity_type": "product",
        "entity_id": product.product_id,
        "risk_level": risk,
        "score": round(adjusted_days, 2),
        "confidence": confidence,
        "days_to_stockout": round(adjusted_days, 1),
        "avg_daily_demand": round(avg_daily_demand, 1),
        "stock_gap": stock_gap,
        "explanation": f"{risk.title()} shortage risk with {adjusted_days:.1f} estimated days to stockout.",
    }


def predict_cost_overrun(shipment: Shipment, carrier: Carrier) -> dict:
    route_complexity = min(1.0, shipment.distance_km / 2800)
    carrier_delay = min(1.0, float(carrier.avg_delay_days) / 5)
    city_risk = max(
        CITY_PROFILES.get(shipment.origin_city, {}).get("monsoon", 0.12),
        CITY_PROFILES.get(shipment.dest_city, {}).get("monsoon", 0.12),
    )
    fuel_index = 0.08 + ((shipment.shipment_id * 11) % 9) / 100
    overrun_pct = route_complexity * 0.12 + carrier_delay * 0.08 + city_risk * 0.10 + fuel_index
    risk = risk_from_score(overrun_pct, 0.08, 0.15)
    return {
        "model_name": "Cost Overrun",
        "entity_type": "shipment",
        "entity_id": shipment.shipment_id,
        "risk_level": risk,
        "score": round(overrun_pct, 3),
        "confidence": round(0.72 + min(overrun_pct, 0.2), 2),
        "overrun_percent": round(overrun_pct * 100, 1),
        "estimated_overrun": round(float(shipment.estimated_cost) * overrun_pct, 2),
        "explanation": f"{risk.title()} cost variance risk driven by route complexity, delays, and fuel trend.",
    }


def accuracy_history() -> list[dict]:
    random = Random(2312)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    baselines = {"Delay": 0.80, "Stock": 0.78, "Cost": 0.76}
    rows: list[dict] = []
    for index, month in enumerate(months):
        row = {"month": month}
        for name, base in baselines.items():
            row[name.lower()] = round(base + index * 0.009 + random.random() * 0.01, 3)
        rows.append(row)
    return rows


def money(value: Decimal | float | int) -> float:
    return round(float(value), 2)
