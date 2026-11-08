# Event query parameters

`GET /events` accepts `limit` (1–1000), `offset` (0–100000), `event_type`, partial `username`, exact `source_ip`, and ISO-8601 `start` / `end` timestamps. Results are ordered newest-first by timestamp and then ID. Invalid event types and malformed IP addresses are rejected; start must not be later than end.