# Deployment smoke test

After deploying the API, check `GET /health` over HTTPS. Confirm the frontend is built with the API origin, browser CORS requests succeed, and the database points to persistent storage. Submit one synthetic event using an authorized client, confirm it appears in the event list, and verify expected detection output. Do not use real user telemetry for smoke tests.