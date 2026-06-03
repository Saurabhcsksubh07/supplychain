from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ShipmentCreate(BaseModel):
    product_id: int
    carrier_id: int
    origin_city: str = Field(min_length=2)
    dest_city: str = Field(min_length=2)
    scheduled_date: date
    estimated_cost: Decimal = Field(gt=0)


class ShipmentUpdate(BaseModel):
    status: str = Field(pattern="^(pending|in_transit|delayed|delivered|cancelled)$")


class PredictionInput(BaseModel):
    shipment_id: int | None = None
    product_id: int | None = None
