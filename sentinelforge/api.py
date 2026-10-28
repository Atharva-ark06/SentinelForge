from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from .db import init_db, insert_event, insert_alert, list_events, list_alerts
from .detection import evaluate_new_event
from .models import SecurityEventIn

DB_PATH = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))
DASHBOARD_PATH = Path(__file__).resolve().parent.parent / "dashboard.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DB_PATH)
    yield


app = FastAPI(
    title="SentinelForge API",
    description="Educational defensive event ingestion and explainable detection API.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def dashboard():
    """Serve the human-readable security dashboard."""
    return FileResponse(DASHBOARD_PATH)


@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinelforge-api", "time": datetime.now(timezone.utc)}


@app.post("/events", status_code=201)
def ingest_event(payload: SecurityEventIn):
    event = payload.model_dump()
    event["timestamp"] = event["timestamp"].isoformat()
    event_id = insert_event(event, DB_PATH)
    generated = evaluate_new_event(event_id, DB_PATH)
    created_alerts = 0
    for alert in generated:
        if insert_alert(alert, DB_PATH):
            created_alerts += 1
    return {
        "accepted": True,
        "event_id": event_id,
        "new_alerts": created_alerts,
        "detections": [
            {"rule_id": a["rule_id"], "title": a["title"], "severity": a["severity"],
             "evidence": a["evidence"], "description": a["description"]}
            for a in generated
        ],
    }


@app.post("/demo/run")
def run_demo():
    """Insert clearly synthetic events for a safe, repeatable dashboard demonstration."""
    start = datetime.now(timezone.utc) - timedelta(minutes=8)
    samples = []
    for i in range(5):
        samples.append({
            "timestamp": (start + timedelta(minutes=i)).isoformat(),
            "event_type": "login_failure",
            "username": "demo-admin",
            "source_ip": "192.0.2.10",
            "host": "lab-win01",
        })
    for i, username in enumerate(["alice", "bob", "charlie"]):
        samples.append({
            "timestamp": (start + timedelta(minutes=5+i)).isoformat(),
            "event_type": "login_failure",
            "username": username,
            "source_ip": "198.51.100.25",
            "host": "lab-linux01",
        })

    created_alerts = 0
    for event in samples:
        event_id = insert_event(event, DB_PATH)
        for alert in evaluate_new_event(event_id, DB_PATH):
            if insert_alert(alert, DB_PATH):
                created_alerts += 1
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
