# Full-stack security review

This document defines acceptance criteria, not completed audit findings.

- Verify authentication and authorization on every protected endpoint, including negative tests.
- Validate OAuth issuer, audience, expiration, callback allowlists and role mapping if OAuth is configured.
- Audit dependencies, secrets, input validation, SQL parameterization and browser security controls.
- Verify dashboard demo data is clearly labeled and isolated from real telemetry.
- Test theme persistence, contrast, keyboard navigation and API failure states.
- Require passing CI and record unresolved deployment-specific checks before release.
