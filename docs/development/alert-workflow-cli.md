# Alert workflow CLI

Use `scripts/manage_alert.py` from the repository root. Set `SENTINELFORGE_API_KEY` in the process environment, then pass alert ID, new status, actor label and an optional note. `SENTINELFORGE_API_URL` can override the default local API origin. The CLI never stores or prints the key.