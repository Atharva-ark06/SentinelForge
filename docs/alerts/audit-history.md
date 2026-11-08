# Alert audit history

Every accepted status update creates one row in `alert_activity`. The row stores alert ID, previous and new status, actor label, optional note and creation time. History is returned newest-first by `GET /alerts/{id}/activity`.

The current actor value is supplied by the trusted API client; it is not an authenticated human identity. Do not treat this field as proof of individual attribution until user authentication and RBAC are implemented. Protect the API key and audit database.