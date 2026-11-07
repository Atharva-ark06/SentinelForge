# Deployment and dashboard connectivity

## Why GitHub Pages can show an empty dashboard

GitHub Pages serves the built React application as static files. It does not run FastAPI, persist SQLite data, or execute the Windows sensor. The frontend must call a separately deployed API over HTTPS.

The dashboard reads these endpoints:

- `GET /health`
- `GET /events?limit=250`
- `GET /alerts?limit=250`

If the frontend is built without an API base URL, it falls back to same-origin paths. On GitHub Pages those paths point to the static Pages host, not the FastAPI service.

## Configure the frontend

1. Deploy the FastAPI application and SQLite database to a trusted backend host. Use persistent storage for the SQLite database; an ephemeral filesystem will lose records on restart or redeploy.
2. In the repository, open **Settings → Secrets and variables → Actions → Variables**.
3. Create a repository variable named `VITE_API_BASE_URL`, with the API origin only, such as `https://api.example.com`. Do not include a path or trailing slash.
4. Re-run **Deploy GitHub Pages** from the Actions tab (or push a frontend change).

The Pages workflow passes this variable to Vite at build time. This URL is public configuration, not a secret.

## Configure the backend

Set these values in the backend host's environment/secret manager:

- `SENTINELFORGE_API_KEY`: generate a unique, high-entropy key. Never commit it.
- `SENTINELFORGE_ALLOWED_ORIGINS`: exact browser origin, for example `https://atharva-ark06.github.io` (origin only; no repository path).
- `SENTINELFORGE_ALLOWED_HOSTS`: API hostname plus any platform-required hostnames.
- `SENTINELFORGE_ENABLE_DOCS=false`: disable interactive API docs in production.
- `SENTINELFORGE_DB`: path to a persistent database volume/file.

The API key is for trusted ingestion clients (the Windows sensor and demo loader). **Do not put it in `VITE_API_BASE_URL`, any `VITE_*` variable, React code, browser storage, or a GitHub Pages secret that gets embedded into the frontend.** A browser-delivered application cannot keep a shared secret private.

The Windows sensor reads `SENTINELFORGE_API_KEY` from its process environment and sends it in the `X-API-Key` header. The synthetic demo loader uses the same environment variable.

## Important data exposure warning

The current `GET /events` and `GET /alerts` endpoints are read-only but do not require authentication. CORS is a browser policy, not API access control; it does not stop direct HTTP clients from requesting data. **Do not connect this public Pages dashboard to real employee, customer, or organizational telemetry on an internet-accessible API in its current form.** Use synthetic/demo data only, or put the API behind an authenticated access gateway and implement user-level authorization before exposing real telemetry. Keep the database private.

## Local development

From the repository root, configure a local key and start the API:

```powershell
$env:SENTINELFORGE_API_KEY = "your-generated-local-key"
python -m uvicorn sentinelforge.api:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite proxies API paths to `http://127.0.0.1:8000` during local development. To load synthetic records, return to the repository root and run:

```powershell
python .\scripts\load_demo.py
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Dashboard says API disconnected | Confirm the backend is running and `VITE_API_BASE_URL` is set to the HTTPS API origin. |
| Browser reports a CORS error | Add the exact Pages origin to `SENTINELFORGE_ALLOWED_ORIGINS`, then restart/redeploy the API. |
| API returns HTTP 400/404 | Confirm the base URL is the API origin, not the Pages URL or a dashboard path. |
| API returns HTTP 502/503 | Check the backend host logs, health endpoint, startup command, and database volume. |
| Data disappears after redeploy | Move SQLite to persistent storage; many free hosting filesystems are ephemeral. |
| Sensor returns HTTP 401/503 | Set the same `SENTINELFORGE_API_KEY` on the API and sensor process. |
| Demo ingestion fails | Set the key in the shell running `scripts/load_demo.py`; never move it into frontend configuration. |
