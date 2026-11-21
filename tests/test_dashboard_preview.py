"""Regression checks for the static synthetic dashboard preview.

These assertions protect against accidental changes that make demo data look live,
expose an API credential, or write demo records to the backend.
"""
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard.html"


def test_synthetic_preview_is_explicit_and_reversible():
    html = DASHBOARD.read_text(encoding="utf-8")
    assert 'id="previewDemo"' in html
    assert "Preview synthetic data" in html
    assert "Exit synthetic preview" in html
    assert "setPreviewMode(!previewMode)" in html


def test_preview_uses_reserved_addresses_and_disclosure():
    html = DASHBOARD.read_text(encoding="utf-8")
    assert "192.0.2.10" in html
    assert "198.51.100.25" in html
    assert "not live" in html
    assert "No API data was changed." in html


def test_preview_never_posts_data():
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index("function syntheticPreview()")
    end = html.index("function setPreviewMode(", start)
    preview = html[start:end]
    assert "fetch(" not in preview
    assert "localStorage" not in preview
    assert "SENTINELFORGE_API_KEY" not in preview


def test_theme_toggle_has_accessibility_state():
    html = DASHBOARD.read_text(encoding="utf-8")
    assert 'id="themeToggle"' in html
    assert 'aria-pressed="false"' in html
    assert "setAttribute('aria-pressed',String(light))" in html
