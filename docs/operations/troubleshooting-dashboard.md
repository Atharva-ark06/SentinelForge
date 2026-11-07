# Dashboard troubleshooting

- API disconnected: inspect the built `VITE_API_BASE_URL`, API health and browser network panel.
- CORS blocked: allow the exact Pages origin on the backend.
- Empty event list: confirm ingestion succeeded and frontend points at the same database/API.
- Data disappears: check whether the host filesystem is ephemeral.
- 401 on ingestion: verify the sensor and API use the same current key.
- 502/503: inspect backend startup, host logs and database volume permissions.