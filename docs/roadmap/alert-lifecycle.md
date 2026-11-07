# Roadmap: alert lifecycle

Proposed alert states: new, acknowledged, investigating, resolved and false-positive. Each transition should record actor, UTC timestamp, previous state, new state and rationale. Enforce authorization server-side and retain immutable audit history. This feature is proposed, not currently implemented.