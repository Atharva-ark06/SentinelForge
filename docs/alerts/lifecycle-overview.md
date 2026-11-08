# Alert lifecycle overview

SentinelForge alerts now have five workflow states: `new`, `acknowledged`, `investigating`, `resolved`, and `false_positive`. The state is persisted in SQLite. Each successful transition writes an append-only activity row with previous state, new state, actor label, note and UTC timestamp.

The workflow is an investigation aid, not an automated containment mechanism. A state change never blocks an account, changes a password or modifies a host.