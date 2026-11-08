# Alert lifecycle test matrix

Cover each permitted transition, each rejected transition, same-state rejection, missing alert IDs, wrong/missing API keys, absent server key, blank actor, oversized notes, activity ordering, persistence after reconnect, and legacy database migration. Tests must use temporary SQLite files and synthetic records.