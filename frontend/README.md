# SentinelForge frontend

React + TypeScript + Vite frontend for the local SentinelForge FastAPI API.

## Run locally

From the repository root, start the backend in one terminal:

```powershell
python -m uvicorn sentinelforge.api:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally http://127.0.0.1:5173). The Vite development server proxies `/health`, `/events`, `/alerts`, and `/demo/run` to FastAPI on port 8000. No production API URL is hardcoded.

## Notes

- Dashboard metrics and charts are calculated from event/alert records returned by the existing API; the chart does not invent historical samples.
- The Run demo button calls the real `POST /demo/run` endpoint. Its events are synthetic and use documentation IP ranges.
- Detection rule cards describe the two rules in `sentinelforge/detection.py`; the current backend does not expose a rules endpoint.
- The existing backend and SQLite schema are not changed by this frontend.
- Frontend build and browser behavior should be verified locally with `npm install` and `npm run build`.
