"""Manage an alert lifecycle through the authenticated SentinelForge API."""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


STATUSES = ("new", "acknowledged", "investigating", "resolved", "false_positive")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alert-id", type=int, required=True, help="Alert database ID")
    parser.add_argument("--status", choices=STATUSES, required=True)
    parser.add_argument("--actor", required=True, help="Analyst identifier for the audit record")
    parser.add_argument("--note", default="", help="Optional investigation note (max 1000 chars)")
    parser.add_argument("--api-url", default=os.environ.get(
        "SENTINELFORGE_API_URL", "http://127.0.0.1:8000"
    ))
    args = parser.parse_args()

    api_key = os.environ.get("SENTINELFORGE_API_KEY", "").strip()
    if not api_key:
        parser.error("Set SENTINELFORGE_API_KEY in the process environment.")
    if not args.actor.strip():
        parser.error("--actor cannot be blank")
    if len(args.note) > 1000:
        parser.error("--note must be 1000 characters or fewer")

    url = args.api_url.rstrip("/") + f"/alerts/{args.alert_id}/status"
    body = json.dumps({
        "status": args.status,
        "actor": args.actor.strip(),
        "note": args.note.strip(),
    }).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="PATCH",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"API returned HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError) as exc:
        print(f"Could not reach SentinelForge API: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
