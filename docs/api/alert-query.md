# Alert query parameters

`GET /alerts` accepts `limit`, `offset`, `severity`, `status`, and exact `source_ip`. Severity is low, medium, high or critical. Status is new, acknowledged, investigating, resolved or false_positive. Filters are applied in SQLite before pagination so page boundaries remain correct.