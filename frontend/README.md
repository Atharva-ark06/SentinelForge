# SentinelForge frontend

React + TypeScript + Vite frontend for the SentinelForge FastAPI API.

## Run locally

From the repository root, start the backend in one terminal:

```powershell
$env:SENTINELFORGE_API_KEY = "your-local-generated-key"
python -m uvicorn sentinelforge.api:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally http://127.0.0.1:5173). The Vite development server proxies API routes to FastAPI on port 8000.

## GitHub Pages / remote API

GitHub Pages serves static files only. It does not host FastAPI, SQLite, or secrets. Deploy the API separately to a trusted HTTPS host, configure its database and `SENTINELFORGE_API_KEY` in that host's secret manager, and set:

- `SENTINELFORGE_ALLOWED_ORIGINS`: the exact Pages origin, e.g. `https://atharva-ark06.github.io` (no path)
- `SENTINELFORGE_ALLOWED_HOSTS`: the API host name and any hostnames required by the platform
- `SENTINELFORGE_ENABLE_DOCS=false` in production

Then add a GitHub Actions repository variable named `VITE_API_BASE_URL` with the API origin, e.g. `https://api.example.com` (no trailing slash). The Pages workflow injects this value at build time. Re-run the Pages workflow after changing the variable.

The frontend calls `{VITE_API_BASE_URL}/health`, `/events`, and `/alerts`. If the variable is unset, requests fall back to same-origin paths; this only works when a same-origin API proxy exists. The dashboard displays a connection error otherwise.

**Never** put `SENTINELFORGE_API_KEY` in a `VITE_*` variable, frontend source, browser storage, or GitHub Pages. Vite variables are public and embedded in downloaded JavaScript.

## Demo data

The dashboard does not send a shared API key from the browser. To load synthetic records, start the backend with the key configured and run from the repository root:

```powershell
python .\scripts\load_demo.py
```

## Data and behavior

- Metrics and charts are calculated only from API records; no fake historical samples are rendered.
- Detection rule cards describe the two implemented rules in `sentinelforge/detection.py`.
- The Windows sensor authenticates using `SENTINELFORGE_API_KEY` from its process environment.
- Verify frontend changes with `npm install` and `npm run build`.
