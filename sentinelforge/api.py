from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
import hmac
import os

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .db import (
    get_metrics,
    init_db,
    insert_alert,
    insert_event,
    list_alert_activity,
    list_alerts,
    list_events,
    update_alert_status,
)
from .detection import evaluate_new_event
from .models import AlertStatusUpdate, SecurityEventIn

DB_PATH = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))
DASHBOARD_PATH = Path(__file__).resolve().parent.parent / "dashboard.html"
API_KEY = os.environ.get("SENTINELFORGE_API_KEY", "").strip()
ALLOWED_ORIGINS = [
    value.strip()
    for value in os.environ.get(
        "SENTINELFORGE_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if value.strip()
]
ALLOWED_HOSTS = [
    value.strip()
    for value in os.environ.get(
        "SENTINELFORGE_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver"
    ).split(",")
    if value.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DB_PATH)
    yield


app = FastAPI(
    title="SentinelForge API",
    description="Educational defensive event ingestion and explainable detection API.",
    version="0.4.0",
    lifespan=lifespan,
    docs_url="/docs" if os.environ.get("SENTINELFORGE_ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url=None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
        "form-action 'self'; object-src 'none'"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def require_ingest_key(request: Request) -> None:
    """Require a configured shared key for trusted write operations."""
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Write operations are disabled until SENTINELFORGE_API_KEY is configured.",
        )
    supplied = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_PATH)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sentinelforge-api",
        "time": datetime.now(timezone.utc),
    }


@app.post("/events", status_code=201)
def ingest_event(payload: SecurityEventIn, request: Request):
    require_ingest_key(request)
    event = payload.model_dump()
    event["timestamp"] = event["timestamp"].isoformat()
    event_id = insert_event(event, DB_PATH)
    generated = evaluate_new_event(event_id, DB_PATH)
    created_alerts = sum(1 for alert in generated if insert_alert(alert, DB_PATH))
    return {
        "accepted": True,
        "event_id": event_id,
        "new_alerts": created_alerts,
        "detections": [
            {
                "rule_id": alert["rule_id"],
                "title": alert["title"],
                "severity": alert["severity"],
                "evidence": alert["evidence"],
                "description": alert["description"],
            }
            for alert in generated
        ],
    }


@app.post("/demo/run")
def run_demo(request: Request):
    require_ingest_key(request)
    start = datetime.now(timezone.utc) - timedelta(minutes=8)
    samples = [
        {
            "timestamp": (start + timedelta(minutes=index)).isoformat(),
            "event_type": "login_failure",
            "username": "demo-admin",
            "source_ip": "192.0.2.10",
            "host": "lab-win01",
        }
        for index in range(5)
    ]
    samples.extend(
        {
            "timestamp": (start + timedelta(minutes=5 + index)).isoformat(),
            "event_type": "login_failure",
            "username": username,
            "source_ip": "198.51.100.25",
            "host": "lab-linux01",
        }
        for index, username in enumerate(["alice", "bob", "charlie"])
    )
    created_alerts = 0
    for event in samples:
        event_id = insert_event(event, DB_PATH)
        created_alerts += sum(
            1
            for alert in evaluate_new_event(event_id, DB_PATH)
            if insert_alert(alert, DB_PATH)
        )
    return {
        "accepted": len(samples),
        "new_alerts": created_alerts,
        "message": "Synthetic demo events processed.",
    }


@app.get("/events")
def get_events(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0, le=100000),
    event_type: str | None = Query(default=None, pattern="^(login_success|login_failure)$"),
    username: str | None = Query(default=None, min_length=1, max_length=128),
    source_ip: str | None = Query(default=None, min_length=1, max_length=64),
    start: datetime | None = None,
    end: datetime | None = None,
):
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start must be earlier than or equal to end")
    if source_ip:
        try:
            source_ip = str(ip_address(source_ip))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="source_ip must be a valid IP address") from exc
    return list_events(
        limit,
        DB_PATH,
        offset=offset,
        event_type=event_type,
        username=username,
        source_ip=source_ip,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )


@app.get("/alerts")
def get_alerts(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0, le=100000),
    severity: str | None = Query(default=None, pattern="^(low|medium|high|critical)$"),
    status: str | None = Query(
        default=None,
        pattern="^(new|acknowledged|investigating|resolved|false_positive)$",
    ),
    source_ip: str | None = Query(default=None, min_length=1, max_length=64),
):
    if source_ip:
        try:
            source_ip = str(ip_address(source_ip))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="source_ip must be a valid IP address") from exc
    return list_alerts(
        limit,
        DB_PATH,
        offset=offset,
        severity=severity,
        status=status,
        source_ip=source_ip,
    )


@app.get("/metrics")
def metrics():
    """Return database-wide totals, independent of dashboard page limits."""
    return get_metrics(DB_PATH)


@app.patch("/alerts/{alert_id}/status")
def change_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    request: Request,
):
    require_ingest_key(request)
    try:
        updated = update_alert_status(
            alert_id,
            payload.status,
            payload.actor,
            payload.note,
            DB_PATH,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated


@app.get("/alerts/{alert_id}/activity")
def alert_activity(alert_id: int):
    history = list_alert_activity(alert_id, DB_PATH)
    if not history:
        from .db import connection

        with connection(DB_PATH) as conn:
            exists = conn.execute(
                "SELECT 1 FROM alerts WHERE id = ?", (alert_id,)
            ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Alert not found")
    return history
