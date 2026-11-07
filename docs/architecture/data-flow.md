# Data flow

1. An authorized sensor or the synthetic loader submits a validated event to `POST /events`.
2. The API checks the ingestion key before storing the event.
3. Detection rules evaluate recent events for the source address.
4. New alerts are inserted with evidence references and a fingerprint.
5. The dashboard retrieves events and alerts from the separately deployed API.

GitHub Pages does not execute FastAPI or host the SQLite database.