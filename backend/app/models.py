from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    category_focus: Mapped[str] = mapped_column(String(80), nullable=False)
    avg_lead_time: Mapped[int] = mapped_column(Integer, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.supplier_id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    optimal_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    supplier: Mapped[Supplier] = relationship(back_populates="products")
    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="product")


class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_utilisation: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="warehouse")


class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    avg_delay_days: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    reliability_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    route_performance_json: Mapped[str] = mapped_column(Text, nullable=False)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="carrier")


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    carrier_id: Mapped[int] = mapped_column(ForeignKey("carriers.carrier_id"), nullable=False)
    origin_city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    dest_city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    distance_km: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivered_date: Mapped[date | None] = mapped_column(Date)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship(back_populates="shipments")
    carrier: Mapped[Carrier] = relationship(back_populates="shipments")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    movement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.warehouse_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    product: Mapped[Product] = relationship(back_populates="stock_movements")
    warehouse: Mapped[Warehouse] = relationship(back_populates="stock_movements")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    location_city: Mapped[str] = mapped_column(String(80), nullable=False)


Index("ix_shipments_schedule_delivery", Shipment.scheduled_date, Shipment.delivered_date)
Index("ix_predictions_entity", Prediction.entity_type, Prediction.entity_id)
Index("ix_stock_movements_product_timestamp", StockMovement.product_id, StockMovement.timestamp)
