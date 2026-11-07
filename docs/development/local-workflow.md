# Local development workflow

Start FastAPI with a local test key, then run the Vite development server. The Vite proxy forwards API requests to the local backend. Use synthetic demo events, inspect API responses, run pytest, and build the frontend before opening a PR. Keep the local SQLite database out of Git.