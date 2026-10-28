"""Read Windows Security logon events and forward eligible events to SentinelForge.

Run from an elevated PowerShell session. This sensor is read-only: it never
blocks logons or changes Windows audit policy.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

DEFAULT_API_URL = "http://127.0.0.1:8000/events"
DEFAULT_INTERVAL = 10
MAX_EVENTS = 250
DEFAULT_STATE_FILE = Path(__file__).resolve().parent / ".sentinelforge_sensor_state.json"
NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}


def powershell_query(max_events: int = MAX_EVENTS) -> str:
    # Explicitly return a non-zero exit code on access/query errors so the
    # Python process cannot mistake a permission failure for an empty log.
    return rf"""
$ErrorActionPreference = 'Stop'
try {{
    $items = @(
        Get-WinEvent -FilterHashtable @{{LogName='Security'; Id=@(4624,4625)}} `
            -MaxEvents {max_events} -ErrorAction Stop |
        ForEach-Object {{ $_.ToXml() }}
    )
    ConvertTo-Json -InputObject $items -Compress -Depth 3
}} catch {{
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}}
"""


def load_checkpoint(state_file: Path) -> int | None:
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        value = int(data["last_record_id"])
        if value < 0:
            raise ValueError("last_record_id cannot be negative")
        return value
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read sensor checkpoint {state_file}: {exc}") from exc


def save_checkpoint(state_file: Path, record_id: int) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(state_file.suffix + ".tmp")
    temp_file.write_text(json.dumps({"last_record_id": record_id}, indent=2), encoding="utf-8")
    temp_file.replace(state_file)


def parse_event(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    system = root.find("e:System", NS)
    if system is None:
        raise ValueError("Windows event is missing its System element")

    event_id_node = system.find("e:EventID", NS)
    record_node = system.find("e:EventRecordID", NS)
    time_node = system.find("e:TimeCreated", NS)
    computer_node = system.find("e:Computer", NS)
    if any(node is None for node in (event_id_node, record_node, time_node, computer_node)):
        raise ValueError("Windows event is missing required system fields")

    event_id = int(event_id_node.text or "0")
    if event_id not in (4624, 4625):
        raise ValueError(f"Unsupported event ID: {event_id}")

    fields: dict[str, str] = {}
    event_data = root.find("e:EventData", NS)
    if event_data is not None:
        for item in event_data.findall("e:Data", NS):
            name = item.attrib.get("Name")
            if name:
                fields[name] = item.text or ""

    username = (fields.get("TargetUserName") or fields.get("SubjectUserName") or "").strip()
    return {
        "record_id": int(record_node.text or "0"),
        "event_id": event_id,
        "timestamp": (time_node.attrib.get("SystemTime") or "").strip(),
        "username": username,
        "source_ip": fields.get("IpAddress", "").strip(),
        "host": (computer_node.text or "").strip(),
        "logon_type": fields.get("LogonType", "").strip(),
    }


def fetch_security_events(max_events: int = MAX_EVENTS) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", powershell_query(max_events)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    output = result.stdout.strip()
    if not output:
        return []
    parsed = json.loads(output)
    if parsed is None:
        return []
    if isinstance(parsed, str):  # PowerShell can serialize one result as a scalar string.
        parsed = [parsed]
    if not isinstance(parsed, list):
        raise ValueError("Unexpected PowerShell event query output")
    events = [parse_event(item) for item in parsed]
    return sorted(events, key=lambda event: event["record_id"])


def eligible_event(event: dict[str, Any]) -> tuple[bool, str]:
    username = event["username"]
    if not username or username == "-" or username.upper() == "ANONYMOUS LOGON" or username.endswith("$"):
        return False, "no useful account name (often a machine/service account)"
    try:
        ipaddress.ip_address(event["source_ip"])
    except ValueError:
        return False, f"no usable source IP ({event['source_ip']!r}); local logons are not sent"
    if not event["timestamp"] or not event["host"]:
        return False, "missing timestamp or host"
    return True, "eligible"


def send_event(event: dict[str, Any], api_url: str) -> bool:
    payload = {
        "timestamp": event["timestamp"],
        "event_type": "login_success" if event["event_id"] == 4624 else "login_failure",
        "username": event["username"],
        "source_ip": event["source_ip"],
        "host": event["host"],
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status != 201:
                print(f"[ERROR] API returned HTTP {response.status}; event will be retried.")
                return False
            body = response.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(body) if body else {}
        except json.JSONDecodeError:
            result = {}
        print(
            f"[SENT] Record {event['record_id']} | {payload['event_type']} | "
            f"user={payload['username']} | source={payload['source_ip']} | "
            f"new_alerts={result.get('new_alerts', 'unknown')}"
        )
        return True
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"[ERROR] API rejected record {event['record_id']}: HTTP {exc.code}: {details}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"[ERROR] Cannot reach SentinelForge API: {exc}")
    return False


def process_events(last_record_id: int, events: list[dict[str, Any]], state_file: Path, api_url: str) -> tuple[int, int, int]:
    current_id = last_record_id
    sent = skipped = new_count = 0
    for event in events:
        record_id = event["record_id"]
        if record_id <= current_id:
            continue
        new_count += 1
        ok, reason = eligible_event(event)
        if not ok:
            print(f"[SKIP] Record {record_id}: {reason}")
            current_id = record_id
            save_checkpoint(state_file, current_id)
            skipped += 1
            continue
        if not send_event(event, api_url):
            # Do not advance beyond a failed send: retry this record next poll.
            return current_id, sent, skipped
        current_id = record_id
        save_checkpoint(state_file, current_id)
        sent += 1
    return current_id, sent, skipped


def poll_once(last_record_id: int | None, state_file: Path, api_url: str, max_events: int = MAX_EVENTS) -> int:
    events = fetch_security_events(max_events)
    if not events:
        print("[POLL] No matching Windows logon events returned.")
        return last_record_id if last_record_id is not None else 0
    newest_id = max(event["record_id"] for event in events)
    if last_record_id is None:
        save_checkpoint(state_file, newest_id)
        print(f"[READY] Baseline set to record {newest_id}; historical events were not ingested.")
        print("[POLL] Waiting for newer eligible events. Local logons without source IPs are skipped.")
        return newest_id
    current_id, sent, skipped = process_events(last_record_id, events, state_file, api_url)
    if sent == 0 and skipped == 0 and current_id == last_record_id:
        print(f"[POLL] No new events. Checkpoint remains at {last_record_id}; latest visible record is {newest_id}.")
    else:
        print(f"[POLL] processed={sent + skipped}, sent={sent}, skipped={skipped}, checkpoint={current_id}.")
    return current_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Read Windows logon events into SentinelForge (read-only).")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Polling interval in seconds (default: 10)")
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"Event endpoint (default: {DEFAULT_API_URL})")
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE, help="Checkpoint file path")
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval must be at least 1 second")

    try:
        last_record_id = load_checkpoint(args.state_file)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    print(f"[INFO] Sending Windows events to {args.api_url}")
    print("[INFO] Monitoring Security event IDs 4624 (success) and 4625 (failure).")
    print("[INFO] Read-only sensor: it does not block logons or change audit policy.")
    print("[INFO] Run this process from an elevated PowerShell window to read the Security log.")

    while True:
        try:
            last_record_id = poll_once(last_record_id, args.state_file, args.api_url)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            print(f"[ERROR] Could not query Windows Security log: {detail}")
        except subprocess.TimeoutExpired:
            print("[ERROR] Windows event query timed out.")
        except (ET.ParseError, json.JSONDecodeError, ValueError) as exc:
            print(f"[ERROR] Could not parse Windows event data: {exc}")
        except KeyboardInterrupt:
            print("\n[INFO] Sensor stopped.")
            return 0
        if args.once:
            return 0
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[INFO] Sensor stopped.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
