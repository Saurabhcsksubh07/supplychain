from app.main import app
from fastapi.testclient import TestClient


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary():
    with TestClient(app) as client:
        response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["active_shipments"] > 0
    assert body["kpis"]["low_stock_products"] > 0


def test_shipments_list():
    with TestClient(app) as client:
        response = client.get("/api/shipments/?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 5
    assert len(body["items"]) == 5


def test_products_list():
    with TestClient(app) as client:
        response = client.get("/api/products/?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 5
    assert len(body["items"]) == 5
