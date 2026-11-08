# API error behavior

- 400: invalid query combination such as a reversed time window.
- 401: missing or incorrect API key on a protected write operation.
- 404: alert ID does not exist.
- 422: request body or query parameter validation failure, including unsupported workflow transition.
- 503: protected write operations disabled because the backend key is not configured.

Clients should show concise, actionable errors and avoid displaying secret values or full internal tracebacks.