from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Alert, Carrier, Prediction, Product, Shipment, StockMovement, Supplier, User, Warehouse
from .services import CITY_PROFILES, predict_cost_overrun, predict_delay, predict_stock_shortage, route_distance_km


PRODUCT_FAMILIES = {
    "Textiles": ["Cotton shirting fabric", "Denim roll", "Knitted garment bundle", "Dyed yarn cone"],
    "Electronics": ["Smart meter board", "Router module", "LED driver unit", "Power adapter"],
    "Pharmaceuticals": ["API batch", "Blister packaging", "OTC medicine carton", "Cold-chain vial pack"],
    "FMCG": ["Cooking oil carton", "Personal care case", "Packaged snack box", "Detergent pouch bale"],
    "Agriculture": ["Fresh grape crate", "Basmati sack", "Seed packet carton", "Dairy input pack"],
}

CARRIER_NAMES = [
    "Blue Dart Surface",
    "Delhivery Freight",
    "TCI Express",
    "VRL Logistics",
    "Gati KWE",
    "Rivigo Relay",
    "Mahindra Logistics",
    "Ecom Express Cargo",
]

USER_ROLES = [
    ("Priya Nair", "Logistics Coordinator", "Mumbai"),
    ("Rohit Singh", "Warehouse Supervisor", "Delhi"),
    ("Ananya Iyer", "Procurement Manager", "Chennai"),
    ("Kabir Mehta", "Supply Chain Analyst", "Bengaluru"),
    ("Farah Khan", "Operations Director", "Hyderabad"),
]


def seed_demo_data(db: Session) -> None:
    has_data = db.scalar(select(Supplier.supplier_id).limit(1))
    if has_data:
        return

    rng = Random(106)
    cities = list(CITY_PROFILES.keys())
    categories = list(PRODUCT_FAMILIES.keys())

    suppliers: list[Supplier] = []
    for index in range(50):
        city = cities[index % len(cities)]
        category = categories[index % len(categories)]
        supplier = Supplier(
            name=f"{city} {category} Works {index + 1:02d}",
            city=city,
            state=CITY_PROFILES[city]["state"],
            category_focus=category,
            avg_lead_time=rng.randint(3, 18),
            reliability_score=round(rng.uniform(0.68, 0.96), 2),
        )
        db.add(supplier)
        suppliers.append(supplier)
    db.flush()

    products: list[Product] = []
    for index in range(500):
        supplier = suppliers[index % len(suppliers)]
        category = supplier.category_focus
        family = PRODUCT_FAMILIES[category][index % len(PRODUCT_FAMILIES[category])]
        threshold = rng.randint(80, 420)
        optimal = threshold + rng.randint(260, 1100)
        if index % 11 == 0:
            current_stock = rng.randint(10, threshold - 5)
        elif index % 7 == 0:
            current_stock = rng.randint(threshold, threshold + 90)
        else:
            current_stock = rng.randint(threshold + 60, optimal)
        product = Product(
            supplier_id=supplier.supplier_id,
            sku=f"IN-{category[:3].upper()}-{index + 1:04d}",
            name=f"{family} {index + 1}",
            category=category,
            current_stock=current_stock,
            reorder_threshold=threshold,
            optimal_stock=optimal,
            unit_cost=Decimal(str(round(rng.uniform(95, 3400), 2))),
        )
        db.add(product)
        products.append(product)
    db.flush()

    warehouses: list[Warehouse] = []
    for index in range(200):
        city = cities[index % len(cities)]
        utilisation = round(rng.uniform(0.42, 0.93), 2)
        warehouse = Warehouse(
            name=f"{city} DC {index + 1:03d}",
            city=city,
            state=CITY_PROFILES[city]["state"],
            total_capacity=rng.randint(8000, 65000),
            current_utilisation=utilisation,
        )
        db.add(warehouse)
        warehouses.append(warehouse)
    db.flush()

    carriers: list[Carrier] = []
    for index, name in enumerate(CARRIER_NAMES):
        reliability = round(0.72 + (index % 5) * 0.045 + rng.uniform(0.0, 0.035), 2)
        carrier = Carrier(
            name=name,
            avg_delay_days=round(max(0.2, 4.2 - reliability * 3.6 + rng.uniform(-0.3, 0.8)), 2),
            reliability_score=min(0.96, reliability),
            route_performance_json=json.dumps(
                {
                    "golden_quadrilateral": round(rng.uniform(0.72, 0.93), 2),
                    "north_east": round(rng.uniform(0.58, 0.84), 2),
                    "monsoon_readiness": round(rng.uniform(0.61, 0.92), 2),
                }
            ),
        )
        db.add(carrier)
        carriers.append(carrier)
    db.flush()

    today = date.today()
    statuses = ["delivered"] * 400 + ["in_transit"] * 350 + ["delayed"] * 150 + ["pending"] * 100
    shipments: list[Shipment] = []
    for index, status in enumerate(statuses):
        product = products[rng.randrange(len(products))]
        carrier = carriers[rng.randrange(len(carriers))]
        origin = cities[rng.randrange(len(cities))]
        destination = cities[rng.randrange(len(cities))]
        while destination == origin:
            destination = cities[rng.randrange(len(cities))]
        distance = route_distance_km(origin, destination)
        scheduled = today + timedelta(days=rng.randint(-15, 24))
        delivered = None
        actual_cost = None
        base_cost = Decimal(str(round(1500 + distance * rng.uniform(7.5, 13.5), 2)))
        if status == "delivered":
            delivered = scheduled + timedelta(days=rng.choice([-1, 0, 0, 1, 2]))
            actual_cost = Decimal(str(round(float(base_cost) * rng.uniform(0.96, 1.12), 2)))
        elif status == "delayed":
            scheduled = today - timedelta(days=rng.randint(1, 10))
            actual_cost = Decimal(str(round(float(base_cost) * rng.uniform(1.08, 1.28), 2)))
        shipment = Shipment(
            product_id=product.product_id,
            carrier_id=carrier.carrier_id,
            origin_city=origin,
            dest_city=destination,
            status=status,
            distance_km=distance,
            scheduled_date=scheduled,
            delivered_date=delivered,
            estimated_cost=base_cost,
            actual_cost=actual_cost,
        )
        db.add(shipment)
        shipments.append(shipment)
    db.flush()

    movement_types = ["IN", "OUT", "OUT", "OUT", "ADJUSTMENT"]
    now = datetime.now(timezone.utc)
    for index in range(10_000):
        product = products[rng.randrange(len(products))]
        warehouse = warehouses[rng.randrange(len(warehouses))]
        movement_type = movement_types[rng.randrange(len(movement_types))]
        seasonal_boost = 1.45 if (now - timedelta(days=index % 365)).month in {3, 10, 11} else 1
        quantity = int(rng.randint(4, 85) * seasonal_boost)
        if movement_type == "OUT":
            quantity *= -1
        db.add(
            StockMovement(
                product_id=product.product_id,
                warehouse_id=warehouse.warehouse_id,
                quantity=quantity,
                movement_type=movement_type,
                timestamp=now - timedelta(days=rng.randint(0, 365), hours=rng.randint(0, 23)),
            )
        )

    for name, role, city in USER_ROLES:
        db.add(User(name=name, role=role, location_city=city))

    for shipment in shipments[:240]:
        carrier = carriers[shipment.carrier_id - 1]
        for result in (predict_delay(shipment, carrier), predict_cost_overrun(shipment, carrier)):
            db.add(
                Prediction(
                    entity_type=result["entity_type"],
                    entity_id=result["entity_id"],
                    model_name=result["model_name"],
                    risk_level=result["risk_level"],
                    score=result["score"],
                    confidence=result["confidence"],
                    explanation=result["explanation"],
                )
            )
            if result["risk_level"] == "HIGH":
                db.add(
                    Alert(
                        entity_type="shipment",
                        entity_id=shipment.shipment_id,
                        severity="HIGH",
                        title=f"{result['model_name']} risk on shipment #{shipment.shipment_id}",
                        message=result["explanation"],
                    )
                )

    for product in products[:220]:
        supplier = suppliers[product.supplier_id - 1]
        result = predict_stock_shortage(product, supplier)
        db.add(
            Prediction(
                entity_type=result["entity_type"],
                entity_id=result["entity_id"],
                model_name=result["model_name"],
                risk_level=result["risk_level"],
                score=result["score"],
                confidence=result["confidence"],
                explanation=result["explanation"],
            )
        )
        if product.current_stock < product.reorder_threshold or result["risk_level"] == "HIGH":
            db.add(
                Alert(
                    entity_type="product",
                    entity_id=product.product_id,
                    severity=result["risk_level"],
                    title=f"Low stock risk for {product.sku}",
                    message=result["explanation"],
                )
            )

    db.commit()
