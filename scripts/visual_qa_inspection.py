import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(r"C:\Users\saket\.gemini\antigravity\brain\ec9448a2-6700-4198-8ffd-2f4ae1426c10")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODE1_PNG = OUT_DIR / "playground_v091_mode1.png"
MODE2_PNG = OUT_DIR / "playground_v091_mode2.png"

def run_qa():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()

        print("Navigating to http://localhost:8000/playground ...")
        page.goto("http://localhost:8000/playground", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Inspect Header elements
        brand_tag_text = page.locator(".brand-tag").first.inner_text()
        model_badge_text = page.locator("#model-badge").inner_text()
        print(f"Main Brand tag text: '{brand_tag_text}'")
        print(f"Model badge text: '{model_badge_text}'")

        # Check overflow for header and badges
        checks = page.evaluate("""() => {
            const brand = document.querySelector('.brand-tag');
            const badge = document.querySelector('#model-badge');
            
            function getInfo(el) {
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return {
                    text: el.innerText.trim(),
                    width: rect.width,
                    height: rect.height,
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth,
                    overflow: el.scrollWidth > el.clientWidth,
                    color: style.color,
                    background: style.backgroundColor,
                    fontSize: style.fontSize,
                    fontWeight: style.fontWeight
                };
            }

            // Inspect all brand tags and badges
            const brandTags = Array.from(document.querySelectorAll('.brand-tag')).map(getInfo);

            return {
                mainBrand: getInfo(brand),
                allBrandTags: brandTags,
                badge: getInfo(badge),
                bodyScrollWidth: document.body.scrollWidth,
                windowInnerWidth: window.innerWidth,
                hasHorizontalScroll: document.body.scrollWidth > window.innerWidth
            };
        }""")
        print("DOM Inspection Results:", json.dumps(checks, indent=2))

        # Capture Mode 1
        page.screenshot(path=str(MODE1_PNG), full_page=False)
        print(f"Captured Mode 1 screenshot to {MODE1_PNG}")

        # Switch to Mode 2: click #tab-btn-cfm
        print("Clicking #tab-btn-cfm...")
        cfm_btn = page.locator("#tab-btn-cfm")
        cfm_btn.click()
        page.wait_for_timeout(1000)

        # Capture Mode 2
        page.screenshot(path=str(MODE2_PNG), full_page=False)
        print(f"Captured Mode 2 screenshot to {MODE2_PNG}")

        browser.close()

if __name__ == "__main__":
    run_qa()
