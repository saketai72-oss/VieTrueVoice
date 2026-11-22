import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(r"C:\Users\saket\.gemini\antigravity\brain\ec9448a2-6700-4198-8ffd-2f4ae1426c10")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_forensics_qa():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
        page = context.new_page()

        # Capture console messages
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE {msg.type.upper()}] {msg.text}"))

        print("Navigating to http://localhost:8000/playground ...")
        page.goto("http://localhost:8000/playground", wait_until="networkidle")
        page.wait_for_timeout(1000)

        forensics_section = page.locator(".forensics-studio-panel")
        forensics_section.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # 1. Standby screenshot
        standby_png = OUT_DIR / "forensics_standby.png"
        forensics_section.screenshot(path=str(standby_png))
        print(f"Captured: {standby_png}")

        # 2. Click Preset SPK_0004 (Clean Voice)
        print("Clicking preset SPK_0004...")
        page.click("button.preset-chip.bonafide:has-text('SPK_0004')")
        page.wait_for_timeout(1500)

        # Run inference
        print("Running inference...")
        page.click("#btn-run-inference")
        page.wait_for_timeout(2000)

        forensics_section.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Capture Tab 1: Spectrogram SPK_0004
        page.click("#ftab-spectrogram")
        page.wait_for_timeout(600)
        spec_spk0004_png = OUT_DIR / "forensics_spectrogram_spk0004.png"
        forensics_section.screenshot(path=str(spec_spk0004_png))
        print(f"Captured: {spec_spk0004_png}")

        # Capture Tab 2: Waveform SPK_0004
        page.click("#ftab-waveform")
        page.wait_for_timeout(600)
        wave_spk0004_png = OUT_DIR / "forensics_waveform_spk0004.png"
        forensics_section.screenshot(path=str(wave_spk0004_png))
        print(f"Captured: {wave_spk0004_png}")

        # Capture Tab 3: Saliency SPK_0004
        page.click("#ftab-saliency")
        page.wait_for_timeout(600)
        sal_spk0004_png = OUT_DIR / "forensics_saliency_spk0004.png"
        forensics_section.screenshot(path=str(sal_spk0004_png))
        print(f"Captured: {sal_spk0004_png}")

        # Capture Tab 4: Codec Audit SPK_0004
        page.click("#ftab-codec")
        page.wait_for_timeout(600)
        codec_spk0004_png = OUT_DIR / "forensics_codec_spk0004.png"
        forensics_section.screenshot(path=str(codec_spk0004_png))
        print(f"Captured: {codec_spk0004_png}")

        # 3. Test AMR-NB Telephony Cutoff Preset
        print("Testing AMR-NB Telephony preset...")
        page.click("button.preset-chip:has-text('AMR-NB')")
        page.wait_for_timeout(1500)

        forensics_section.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Switch back to Spectrogram for AMR-NB
        page.click("#ftab-spectrogram")
        page.wait_for_timeout(600)
        spec_amrnb_png = OUT_DIR / "forensics_spectrogram_amrnb.png"
        forensics_section.screenshot(path=str(spec_amrnb_png))
        print(f"Captured: {spec_amrnb_png}")

        # Switch to Codec Audit for AMR-NB
        page.click("#ftab-codec")
        page.wait_for_timeout(600)
        codec_amrnb_png = OUT_DIR / "forensics_codec_amrnb.png"
        forensics_section.screenshot(path=str(codec_amrnb_png))
        print(f"Captured: {codec_amrnb_png}")

        # Also capture a full-page view for complete overview
        fullpage_png = OUT_DIR / "playground_v091_fullpage_amrnb.png"
        page.screenshot(path=str(fullpage_png), full_page=True)
        print(f"Captured fullpage: {fullpage_png}")

        browser.close()
        print("Forensics QA completed successfully!")

if __name__ == "__main__":
    run_forensics_qa()
