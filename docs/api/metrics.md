# Metrics API

`GET /metrics` returns database-wide totals, not counts limited by the dashboard's event/alert page size. The `events` object contains total, counts by event type and latest timestamp. The `alerts` object contains total, counts by severity, counts by workflow status and latest timestamp.

A category with no records may be omitted from its count map; clients should treat a missing key as zero.