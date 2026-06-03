# Supply Chain Command Centre

End-to-end demo implementation based on `FinalReport_SaurabhRai_2312RES854.docx`.

The report describes a predictive supply-chain platform for the Indian market with a FastAPI backend, Vue.js 3 frontend, PostgreSQL-ready data layer, Indian demo data, and three ML use cases: shipment delay prediction, stock shortage prediction, and cost overrun prediction. This workspace implements that as a runnable local demo.

## What Is Included

- FastAPI backend with endpoints for dashboard summaries, shipments, products, predictions, and alerts.
- SQLAlchemy data model covering the nine report tables: suppliers, products, warehouses, carriers, shipments, stock movements, predictions, alerts, and users.
- Deterministic seeded Indian logistics data: 50 suppliers, 500 products, 200 warehouses, 1,000 shipments, 10,000 stock movements, plus predictions and alerts.
- Vue 3 frontend with operational screens for dashboard, shipment control, inventory health, and model performance.
- Chart.js visualizations and prediction detail panels using the model metrics reported in the document.
- SQLite default database for quick local use, with `DATABASE_URL` support for PostgreSQL later.

## Run Locally

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Backend API docs are available at `http://127.0.0.1:8000/docs`.

## Report-Derived Requirements

- Dashboard KPIs: active shipments, high-risk shipments, low-stock warehouses/products, and average model accuracy.
- Shipment view: searchable and filterable table with status, route, carrier, ETA, cost, delay risk, and cost overrun risk.
- Inventory view: product stock health with reorder thresholds and days-to-stockout prediction.
- Prediction view: model accuracy, risk distribution, feature importance, and recent prediction history.
- Alert panel: unresolved HIGH/MEDIUM/LOW alerts from threshold breaches and prediction results.

## Database Notes

The local demo creates `backend/supply_chain_demo.db` on first backend start. Delete that file if you want to reseed from scratch.

To use PostgreSQL, set:

```powershell
$env:DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/supply_chain"
```

Then install the appropriate PostgreSQL driver and run the backend as above.
