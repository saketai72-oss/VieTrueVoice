"""Download all screens, screenshots, and HTML from Stitch project."""

from __future__ import annotations
import base64
import json
from pathlib import Path
import requests

API_KEY = "REDACTED_API_KEY"
HEADERS = {"X-Goog-Api-Key": API_KEY}
PROJECT_ID = "15978844079297582735"
OUT_DIR = Path("stitch_design")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# List of screens from list_screens tool
SCREENS = [
    {
        "id": "13408603679021679436",
        "title": "poster.jpg",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/13408603679021679903:download",
        "html_url": None,
    },
    {
        "id": "13408603679021681664",
        "title": "bonafide.jpg",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/13408603679021682131:download",
        "html_url": None,
    },
    {
        "id": "13408603679021682598",
        "title": "spoof.jpg",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/13408603679021678969:download",
        "html_url": None,
    },
    {
        "id": "c984b657d8da44648d8cbfa41180e7b3",
        "title": "01_Kiem_Tra_Giong_Noi_Tieng_Viet_Light",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc02365861501a63eb559353482:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/c984b657d8da44648d8cbfa41180e7b3:download",
    },
    {
        "id": "9e6180009e9447eb86ccdcc23227f9e4",
        "title": "02_Phan_Tich_Mel_Spectrogram_Light",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc034510f11022d42bd083a6a18:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/9e6180009e9447eb86ccdcc23227f9e4:download",
    },
    {
        "id": "95b8ff206c88483dae948daf24ff13e7",
        "title": "03_Kiem_Tra_Giong_Noi_Lab_Dark",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc03c1d3efc057600821c0de884:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/95b8ff206c88483dae948daf24ff13e7:download",
    },
    {
        "id": "6e76cc07628744288c86371aff9e3068",
        "title": "04_Phan_Tich_Mel_Spectrogram_Lab_Dark",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc043fd2f6201a63eb559353482:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/6e76cc07628744288c86371aff9e3068:download",
    },
    {
        "id": "8ada7b1cb86441f4ba1715ed47489637",
        "title": "05_Phan_Tich_GradCAM_Lab_Dark",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc047a69cd307c4d730141a1eb8:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/8ada7b1cb86441f4ba1715ed47489637:download",
    },
    {
        "id": "70fe3cdfe41649dabfd7ae185caf939e",
        "title": "06_Phan_Tich_GradCAM_Light",
        "img_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/screenshot_00065fc04df37bcf02079bdaca19064f:download",
        "html_url": "https://stitch.googleapis.com/v1/projects/15978844079297582735/files/70fe3cdfe41649dabfd7ae185caf939e:download",
    },
]

def main() -> None:
    for idx, screen in enumerate(SCREENS, 1):
        name = screen["title"]
        print(f"[{idx}/{len(SCREENS)}] Processing {name} ({screen['id']})...")
        
        # Download screenshot / image
        if screen["img_url"]:
            r = requests.get(screen["img_url"], headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                data_str = data.get("dataString", "")
                meta = data.get("imageMetadata", {})
                mime = meta.get("mimeType", "image/png")
                ext = ".jpg" if "jpeg" in mime or name.endswith(".jpg") else ".png"
                img_path = OUT_DIR / f"{name}{ext}" if not name.endswith((".jpg", ".png")) else OUT_DIR / name
                try:
                    img_bytes = base64.b64decode(data_str)
                    img_path.write_bytes(img_bytes)
                    print(f"  Saved image: {img_path} ({len(img_bytes)} bytes)")
                except Exception as e:
                    print(f"  Failed to decode image {name}: {e}")
            else:
                print(f"  Error downloading image: {r.status_code}")

        # Download HTML if present
        if screen["html_url"]:
            r = requests.get(screen["html_url"], headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                html_str = data.get("dataString", "")
                html_path = OUT_DIR / f"{name}.html"
                html_path.write_text(html_str, encoding="utf-8")
                print(f"  Saved HTML: {html_path} ({len(html_str)} chars)")
            else:
                print(f"  Error downloading HTML: {r.status_code}")

if __name__ == "__main__":
    main()
