from pathlib import Path

import pytest

from sentinelforge import api


@pytest.fixture
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Give each API test an independent SQLite file and deterministic test key."""
    path = tmp_path / "sentinelforge-api-test.sqlite3"
    monkeypatch.setattr(api, "DB_PATH", path)
    monkeypatch.setattr(api, "API_KEY", "test-secret")
    yield path
