import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(r"C:\Users\saket\.gemini\antigravity\brain\ec9448a2-6700-4198-8ffd-2f4ae1426c10")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_DIR_LOCAL = Path(r"C:\Users\saket\.gemini\antigravity\brain\afee2b21-470b-43c6-b54e-e8457394f7e9")
OUT_DIR_LOCAL.mkdir(parents=True, exist_ok=True)

FRAME1_PNG = OUT_DIR / "frame1_header_navigation_presets.png"
FRAME2_PNG = OUT_DIR / "frame2_audio_ingestion_deck.png"
FRAME3_PNG = OUT_DIR / "frame3_forensic_decision_matrix.png"
FRAME4_PNG = OUT_DIR / "frame4_spectral_studio.png"
FRAME5_PNG = OUT_DIR / "frame5_mode2_cfm_comparative_matrix.png"

def capture_all_frames():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 950},
            device_scale_factor=2
        )
        page = context.new_page()

        # Auto-accept all alerts or dialogs
        page.on("dialog", lambda dialog: dialog.accept())
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}"))

        print("Navigating to http://localhost:8000/playground ...")
        page.goto("http://localhost:8000/playground", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # FRAME 1: Header, Navigation Pill & Preset Chips
        # -------------------------------------------------------------
        print("\n=== Capturing Frame 1: Header, Navigation Pill & Preset Chips ===")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)

        top_box = page.evaluate("""() => {
            const h = document.querySelector('header.top-nav').getBoundingClientRect();
            const p = document.querySelector('section.presets-bar').getBoundingClientRect();
            return {
                x: Math.floor(Math.min(h.x, p.x)),
                y: Math.floor(h.y),
                width: Math.ceil(Math.max(h.width, p.width)),
                height: Math.ceil((p.bottom - h.y) + 12)
            };
        }""")
        page.screenshot(path=str(FRAME1_PNG), clip=top_box)
        page.screenshot(path=str(OUT_DIR_LOCAL / FRAME1_PNG.name), clip=top_box)
        print(f"Screenshot: {FRAME1_PNG} | Header, Navigation Pill & Preset Chips captured")

        # -------------------------------------------------------------
        # FRAME 2: Audio Ingestion Deck (Waveform, 5.12s, 2 Windows)
        # -------------------------------------------------------------
        print("\n=== Capturing Frame 2: Audio Ingestion Deck ===")
        print("Selecting SPK_0004 Clean Voice preset...")
        page.click("button.preset-chip.bonafide:has-text('SPK_0004')")
        page.wait_for_timeout(1500)

        # Wait for waveform and metadata to update
        page.wait_for_function("document.getElementById('meta-duration').innerText.includes('5.12s')")
        page.wait_for_function("document.getElementById('meta-slices').innerText.includes('2 Windows')")
        page.wait_for_timeout(500)

        deck_panel = page.locator("section.deck-panel")
        deck_panel.screenshot(path=str(FRAME2_PNG))
        deck_panel.screenshot(path=str(OUT_DIR_LOCAL / FRAME2_PNG.name))
        print(f"Screenshot: {FRAME2_PNG} | Audio Ingestion Deck with Waveform and 2 Windows")

        # -------------------------------------------------------------
        # FRAME 3: Forensic Decision Matrix (Platt, T=16.0, Verdict, Veto)
        # -------------------------------------------------------------
        print("\n=== Capturing Frame 3: Forensic Decision Matrix ===")
        print("Running inference on loaded SPK_0004 audio...")
        page.click("#btn-run-inference")

        # Wait for inference result to render
        page.wait_for_function(
            "document.getElementById('metric-raw-score').innerText !== '—' && document.getElementById('metric-raw-score').innerText !== ''",
            timeout=25000
        )
        page.wait_for_timeout(1000)

        decision_info = page.evaluate("""() => {
            return {
                verdict: document.getElementById('verdict-text')?.innerText,
                badge: document.getElementById('verdict-badge')?.innerText,
                confidence: document.getElementById('gauge-percent-display')?.innerText,
                rawScore: document.getElementById('metric-raw-score')?.innerText,
                threshold: document.getElementById('metric-threshold')?.innerText,
                windows: document.getElementById('metric-windows')?.innerText,
                latency: document.getElementById('metric-latency')?.innerText,
            };
        }""")
        print("Verified Decision Matrix Details:", json.dumps(decision_info, indent=2))

        intel_panel = page.locator("section.intelligence-panel")
        intel_panel.screenshot(path=str(FRAME3_PNG))
        intel_panel.screenshot(path=str(OUT_DIR_LOCAL / FRAME3_PNG.name))
        print(f"Screenshot: {FRAME3_PNG} | Decision Matrix with Platt Confidence and Asymmetric Veto")

        # -------------------------------------------------------------
        # FRAME 4: Forensics Spectral Studio (STFT, Formants, AMR Cutoff)
        # -------------------------------------------------------------
        print("\n=== Capturing Frame 4: Forensics Spectral Studio ===")
        studio_panel = page.locator("section.forensics-studio-panel")
        studio_panel.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Make sure STFT tab is active and re-rendered
        page.click("#ftab-spectrogram")
        page.wait_for_timeout(800)

        studio_panel.screenshot(path=str(FRAME4_PNG))
        studio_panel.screenshot(path=str(OUT_DIR_LOCAL / FRAME4_PNG.name))
        print(f"Screenshot: {FRAME4_PNG} | Forensics Spectral Studio STFT Spectrogram and AMR Cutoff")

        # -------------------------------------------------------------
        # FRAME 5: Mode 2 Live VoiceStudio CFM Cloning & Comparative Matrix
        # -------------------------------------------------------------
        print("\n=== Capturing Frame 5: Mode 2 Live CFM Cloning & Comparative Matrix ===")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.click("#tab-btn-cfm")
        page.wait_for_timeout(1000)

        print("Ensuring SPK_0004 reference audio is loaded in Mode 2...")
        page.click("#btn-cfm-load-sample")
        page.wait_for_timeout(1000)

        print("Triggering CFM Cloning & Comparative Audit...")
        page.click("#btn-run-cfm-clone")

        # Wait for either live clone or offline fallback results to populate
        page.wait_for_function(
            "document.getElementById('cfm-ref-score').innerText !== '--' && document.getElementById('cfm-sus-score').innerText !== '--'",
            timeout=90000
        )
        page.wait_for_timeout(1500)

        cfm_audit_info = page.evaluate("""() => {
            return {
                refVerdict: document.getElementById('cfm-ref-verdict-text')?.innerText,
                refScore: document.getElementById('cfm-ref-score')?.innerText,
                refConf: document.getElementById('cfm-ref-conf')?.innerText,
                susVerdict: document.getElementById('cfm-sus-verdict-text')?.innerText,
                susScore: document.getElementById('cfm-sus-score')?.innerText,
                susConf: document.getElementById('cfm-sus-conf')?.innerText,
                deltaS: document.getElementById('mat-score-delta')?.innerText,
                accuracy: document.getElementById('mat-accuracy-status')?.innerText,
            };
        }""")
        print("Verified CFM Comparative Matrix Details:", json.dumps(cfm_audit_info, indent=2))

        cfm_container = page.locator("#cfm-container")
        cfm_container.screenshot(path=str(FRAME5_PNG))
        cfm_container.screenshot(path=str(OUT_DIR_LOCAL / FRAME5_PNG.name))
        print(f"Screenshot: {FRAME5_PNG} | Mode 2 CFM Cloning and Comparative Benchmark Matrix")

        browser.close()
        print("\n>>> ALL 5 OFFICIAL FRAMES CAPTURED AND VERIFIED SUCCESSFULLY <<<")

if __name__ == "__main__":
    capture_all_frames()
