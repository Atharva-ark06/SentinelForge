# SF-AUTH-001 — repeated authentication failures

The current rule looks for at least five failed logins for the same username and source address within ten minutes. Severity is medium. Validate expected user activity, shared egress/NAT behavior and source ownership before escalation. Thresholds are educational defaults, not universal production policy.