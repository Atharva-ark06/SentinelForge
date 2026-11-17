# Contributing to SentinelForge

SentinelForge is a defensive, local-first educational security project.

## Getting started
1. Fork and branch from `main`.
2. Copy `.env.example` to `.env` and replace all placeholders. Never commit secrets or real telemetry.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Run `python -m pytest -q`, `python -m compileall -q sentinelforge scripts`, and `cd frontend && npm ci && npm run build`.
5. Submit a focused PR explaining changes, tests, and any security implications.

## Reporting security bugs
Do not post working exploit details, secrets, or sensitive telemetry in public issues. Contact the maintainer privately through GitHub's security advisory reporting when available. Include affected version, reproduction in an authorized lab, and impact.

## Code review
Prefer small changes, type hints, bounded inputs, regression tests, and explicit documentation of residual risks. Do not add live customer data or credentials to fixtures.
