# Metrics and query test matrix

Verify database-wide counts are independent of list limits, missing categories are treated as zero by clients, offset pagination is deterministic, filters are applied before pagination, source IPs are validated, time windows reject reversed bounds, and empty databases return zero totals and null latest timestamps.