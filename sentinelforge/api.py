from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hmac
import os

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .db import init_db, insert_event, insert_alert, list_events, list_alerts
from .detection import evaluate_new_event
from .models import SecurityEventIn

DB_PATH = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))
DASHBOARD_PATH = Path(__file__).resolve().parent.parent / "dashboard.html"
API_KEY = os.environ.get("SENTINELFORGE_API_KEY", "").strip()
ALLOWED_ORIGINS = [x.strip() for x in os.environ.get("SENTINELFORGE_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if x.strip()]
ALLOWED_HOSTS = [x.strip() for x in os.environ.get("SENTINELFORGE_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if x.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DB_PATH)
    yield

app = FastAPI(title="SentinelForge API", description="Educational defensive event ingestion and explainable detection API.",
    version="0.3.0", lifespan=lifespan,
    docs_url="/docs" if os.environ.get("SENTINELFORGE_ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key"])

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response

def require_ingest_key(request: Request) -> None:
    """Require a configured shared key for write endpoints; fail closed if absent."""
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Ingestion is disabled until SENTINELFORGE_API_KEY is configured.")
    supplied = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_PATH)

@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinelforge-api", "time": datetime.now(timezone.utc)}

@app.post("/events", status_code=201)
def ingest_event(payload: SecurityEventIn, request: Request):
    require_ingest_key(request)
    event = payload.model_dump()
    event["timestamp"] = event["timestamp"].isoformat()
    event_id = insert_event(event, DB_PATH)
    generated = evaluate_new_event(event_id, DB_PATH)
    created_alerts = sum(1 for alert in generated if insert_alert(alert, DB_PATH))
    return {"accepted": True, "event_id": event_id, "new_alerts": created_alerts,
        "detections": [{"rule_id": a["rule_id"], "title": a["title"], "severity": a["severity"],
        "evidence": a["evidence"], "description": a["description"]} for a in generated]}

@app.post("/demo/run")
def run_demo(request: Request):
    require_ingest_key(request)
    start = datetime.now(timezone.utc) - timedelta(minutes=8)
    samples = [{"timestamp": (start + timedelta(minutes=i)).isoformat(), "event_type": "login_failure",
        "username": "demo-admin", "source_ip": "192.0.2.10", "host": "lab-win01"} for i in range(5)]
    samples.extend({"timestamp": (start + timedelta(minutes=5+i)).isoformat(), "event_type": "login_failure",
        "username": username, "source_ip": "198.51.100.25", "host": "lab-linux01"}
        for i, username in enumerate(["alice", "bob", "charlie"]))
    created_alerts = 0
    for event in samples:
        event_id = insert_event(event, DB_PATH)
        created_alerts += sum(1 for alert in evaluate_new_event(event_id, DB_PATH) if insert_alert(alert, DB_PATH))
    return {"accepted": len(samples), "new_alerts": created_alerts, "message": "Synthetic demo events processed."}

@app.get("/events")
def get_events(limit: int = Query(default=100, ge=1, le=1000)):
    return list_events(limit, DB_PATH)

@app.get("/alerts")
def get_alerts(limit: int = Query(default=100, ge=1, le=1000), severity: str | None = None):
    rows = list_alerts(limit, DB_PATH)
    if severity is not None:
        allowed = {"low", "medium", "high", "critical"}
        if severity not in allowed:
            raise HTTPException(status_code=400, detail=f"severity must be one of {sorted(allowed)}")
        rows = [row for row in rows if row["severity"] == severity]
    return rows
