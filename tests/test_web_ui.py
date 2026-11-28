"""Contract & hygiene tests for the Brutalist WebGL Forensics Web UI assets."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "src" / "app" / "static"

REQUIRED_STATIC_FILES = (
    "index.html",
    "css/app.css",
    "js/webgl-orb.js",
    "js/audio-recorder.js",
    "js/charts.js",
    "js/app.js",
    "assets/card_01_zalo_opus.png",
    "assets/card_02_amrnb_cutoff.png",
    "assets/card_03_cfm_comparison.png",
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_required_web_ui_assets_exist_and_pngs_valid():
    """All static HTML/CSS/JS modules and the 3 forensic PNG cards exist on disk."""
    for rel_path in REQUIRED_STATIC_FILES:
        full_path = STATIC_DIR / rel_path
        assert full_path.is_file(), f"Missing required static Web UI asset: {rel_path}"
        assert full_path.stat().st_size > 0, f"Empty static Web UI asset: {rel_path}"

    for png_name in (
        "assets/card_01_zalo_opus.png",
        "assets/card_02_amrnb_cutoff.png",
        "assets/card_03_cfm_comparison.png",
    ):
        header = (STATIC_DIR / png_name).read_bytes()[:8]
        assert header == PNG_SIGNATURE, f"Invalid PNG header in {png_name}"


def test_gradio_and_legacy_playground_completely_removed():
    """Legacy Gradio UI, playground.html, and gradio dependency must be absent."""
    assert not (ROOT / "src" / "app" / "ui.py").exists()
    assert not (STATIC_DIR / "playground.html").exists()

    req_lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    active_reqs = [
        line.strip().lower()
        for line in req_lines
        if line.strip() and not line.strip().startswith("#")
    ]
    assert not any("gradio" in line for line in active_reqs), (
        "gradio dependency must be removed from requirements.txt"
    )


def test_web_ui_wires_both_real_endpoints_and_has_zero_mocks():
    """Web UI wires Feature 1 & Feature 2 real APIs with zero mock/external placeholder assets."""
    index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (STATIC_DIR / "js" / "app.js").read_text(encoding="utf-8")
    combined_ui = f"{index_html}\n{app_js}"

    assert "<!DOCTYPE html>" in index_html
    assert "XÁC THỰC GIỌNG NÓI" in index_html
    for script_name in ("webgl-orb.js", "audio-recorder.js", "charts.js", "app.js"):
        assert script_name in index_html, f"index.html must load {script_name}"

    # Both Feature 1 (predict) and Feature 2 (clone-and-audit) must be wired
    assert "/api/v1/predict" in combined_ui
    assert "/api/v1/clone-and-audit" in combined_ui

    # Zero mock functions or leftover Google placeholder image URLs across frontend sources
    frontend_files = [
        STATIC_DIR / "index.html",
        STATIC_DIR / "css" / "app.css",
        STATIC_DIR / "js" / "webgl-orb.js",
        STATIC_DIR / "js" / "audio-recorder.js",
        STATIC_DIR / "js" / "charts.js",
        STATIC_DIR / "js" / "app.js",
    ]
    for path in frontend_files:
        text = path.read_text(encoding="utf-8")
        assert "mockAnalyzeAudio" not in text, f"Found mockAnalyzeAudio in {path.name}"
        assert "lh3.googleusercontent.com" not in text, (
            f"Found external placeholder image URL in {path.name}"
        )
