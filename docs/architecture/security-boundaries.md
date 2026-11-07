# Security boundaries

Treat endpoint telemetry, credentials, deployment secrets and CI tokens as separate trust domains. CORS is not authentication. A hidden URL is not access control. A browser-delivered secret is public to anyone who can inspect the bundle or network requests.

Before real telemetry is connected, protect read endpoints with authenticated sessions or an access gateway and enforce role-based authorization on every request.