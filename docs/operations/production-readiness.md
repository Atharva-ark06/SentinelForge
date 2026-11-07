# Production readiness checklist

- [ ] Deploy FastAPI separately from GitHub Pages.
- [ ] Use HTTPS and a persistent database volume.
- [ ] Set a unique high-entropy ingestion key in the backend secret manager.
- [ ] Set exact CORS origins and trusted hostnames.
- [ ] Disable interactive API docs in production.
- [ ] Protect event and alert reads with authentication and authorization.
- [ ] Configure retention, backups, restore tests and log access auditing.
- [ ] Configure rate limits and request-size limits at the edge/API.
- [ ] Run dependency and secret scans; review findings.
- [ ] Verify health, ingestion, detection, and recovery with synthetic data.