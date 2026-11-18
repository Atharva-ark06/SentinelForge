"""Seed a local development database with synthetic authentication events.

Usage: python -m scripts.seed --db ./demo.sqlite3
Never point this at production data; pass --force to seed a nonempty database.
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinelforge.db import connection, init_db, insert_event


def seed(path: Path, *, force: bool = False) -> int:
    init_db(path)
    with connection(path) as conn:
        existing = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if existing and not force:
        raise ValueError("Database already contains events; use --force to append demo events")
    start = datetime.now(timezone.utc) - timedelta(minutes=12)
    for index in range(12):
        insert_event({
            "timestamp": (start + timedelta(minutes=index)).isoformat(),
            "event_type": "login_failure" if index % 3 else "login_success",
            "username": ("demo-alice", "demo-bob", "demo-charlie")[index % 3],
            "source_ip": f"192.0.2.{10 + index % 4}",
            "host": "demo-lab-01",
        }, path)
    return 12


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("sentinelforge-demo.sqlite3"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(f"Seeded {seed(args.db, force=args.force)} synthetic events into {args.db}")


if __name__ == "__main__":
    main()
