from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import SessionLocal, create_tables
from .routes import alerts, dashboard, predictions, products, shipments
from .seed import seed_demo_data

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    with SessionLocal() as db:
        seed_demo_data(db)
    yield


app = FastAPI(
    title="Supply Chain Command Centre API",
    description="FastAPI backend for the predictive supply-chain platform described in the capstone report.",
    version="1.0.0",
    lifespan=lifespan,
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "supply-chain-command-centre"}


app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["shipments"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
