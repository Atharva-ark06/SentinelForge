"""Static frontend regression checks for Pages and synthetic preview integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_build_defaults_to_explicit_synthetic_preview():
    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "import.meta.env.PROD && !API_BASE_URL" in app
    assert "makeSyntheticPreview()" in app
    assert "SYNTHETIC PREVIEW" in app
    assert "Exit synthetic preview" in app


def test_demo_generator_uses_only_reserved_test_ips():
    demo = (ROOT / "frontend/src/demo.ts").read_text(encoding="utf-8")
    assert "192.0.2." in demo
    assert "198.51.100." in demo
    assert "203.0.113." in demo
    assert "length: 36" in demo
    assert "length: 8" in demo
    assert "fetch(" not in demo
    assert "localStorage" not in demo


def test_local_dev_proxy_covers_all_dashboard_reads():
    config = (ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")
    for route in ('"/health"', '"/events"', '"/alerts"', '"/metrics"'):
        assert route in config


def test_visual_accessibility_styling():
    css = (ROOT / "frontend/src/styles.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert ".metric:hover" in css
