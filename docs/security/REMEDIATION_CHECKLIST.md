# Security remediation implementation checklist

This file tracks the remediation work associated with [issue #17](../../issues/17). It is a **work plan, not evidence that controls are already implemented**. Each item must be verified against code, automated tests, and the actual deployment before being marked complete.

- [ ] Confirm the API rejects POST /events when X-API-Key is absent.
- [ ] Confirm the API rejects POST /demo/run when X-API-Key is absent.
- [ ] Confirm incorrect API keys return HTTP 401.
- [ ] Confirm API-key comparisons use constant-time comparison.
- [ ] Keep API secrets exclusively in server-side environment variables.
- [ ] Do not place private credentials in VITE_* variables or frontend bundles.
