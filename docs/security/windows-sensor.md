# Windows sensor security and operations

## Transport protection

The sensor sends `SENTINELFORGE_API_KEY` in the `X-API-Key` request header. Remote HTTP is unsafe because it exposes the shared credential and telemetry to network observers. The client therefore accepts HTTPS for remote hosts and permits plain HTTP only for `localhost` or loopback IP addresses used during local development. Use a valid certificate for the remote API; do not disable TLS verification.

Prefer the `SENTINELFORGE_API_KEY` environment variable over `--api-key`. Command-line arguments may be visible to local process inspection tools, shell history, terminal recordings or monitoring agents. Never paste the key into source code, issue reports or screenshots.

## Checkpoint and backlog behavior

The first poll establishes a baseline from the newest visible matching records. This avoids replaying the entire historical Security log when the sensor is first installed. Subsequent polls filter for event record IDs greater than the persisted checkpoint and read oldest-first in batches. If more than one batch accumulates between polls, later polls continue from the last successfully sent or intentionally skipped record.

The checkpoint is stored in `scripts/.sentinelforge_sensor_state.json`. Keep it out of version control and protect it as local operational state. A failed API send does not advance the checkpoint, so the record is retried. Records without a useful account or valid remote source IP are intentionally skipped and checkpointed.

## Operational limitations

- The sensor reads only Windows Security logon events 4624 and 4625.
- The process needs permission to read the Security event log.
- A local log clear or record-ID reset can invalidate an old checkpoint; review the log and checkpoint before manually resetting it.
- The API must be reachable and configured with the matching shared key.
- This is a read-only educational collector, not an endpoint protection agent.

## Recovery checklist

1. Stop the sensor before changing its checkpoint.
2. Confirm the API URL uses HTTPS unless it is local loopback.
3. Verify the API key is configured on both the sensor process and backend.
4. Inspect the latest Windows event record ID and the saved checkpoint.
5. Preserve a copy of the checkpoint before any manual reset.
6. Restart with a bounded batch size, for example `--max-events 250`.
7. Confirm ingestion and detection behavior using synthetic or authorized lab events.

Never delete or reset the checkpoint simply to make a dashboard appear populated; doing so can replay historical telemetry or duplicate events.
