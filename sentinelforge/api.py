from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from .db import init_db, insert_event, insert_alert, list_events, list_alerts
from .detection import evaluate_new_event
from .models import SecurityEventIn

DB_PATH = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DB_PATH)
    yield


app = FastAPI(
    title="SentinelForge API",
    description="Educational defensive event ingestion and explainable detection API.",
    version="0.1.0",
    lifespan=lifespan,
)


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
