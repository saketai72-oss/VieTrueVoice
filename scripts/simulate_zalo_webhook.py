"""Kịch bản mô phỏng kiểm thử Zalo Official Account (OA) Webhook End-to-End.

Mô phỏng quy trình thực tế của Zalo for Developers:
1. Khởi động máy chủ tạm thời để cung cấp luồng âm thanh thử nghiệm.
2. Tạo bản tin Webhook chuẩn Zalo OA (sự kiện: user_send_audio).
3. Ký chữ ký HMAC-SHA256 hợp lệ với Zalo App Secret.
4. Gửi tới máy chủ ViTrueVoice (POST /api/v1/zalo/webhook).
5. In kết quả phân định, độ tin cậy Platt Scaling và nội dung phản hồi Zalo.
"""

from __future__ import annotations
import argparse
import http.server
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests

from src.app.zalo_webhook import generate_zalo_signature


class SingleFileHandler(http.server.BaseHTTPRequestHandler):
    file_bytes: bytes = b""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(self.file_bytes)))
        self.end_headers()
        self.wfile.write(self.file_bytes)

    def log_message(self, format, *args):
        pass  # Quiet logger


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def get_host_ip() -> str:
    """Detect LAN IP of the host machine so Docker container can access it."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="Mô phỏng gửi tin nhắn thoại Zalo Webhook tới ViTrueVoice")
    parser.add_argument(
        "--audio",
        default="data/bonafide_ref/SPK_0004/SPK_0004_01.wav",
        help="Đường dẫn file âm thanh kiểm định",
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/api/v1/zalo/webhook",
        help="URL Webhook của ViTrueVoice",
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("ZALO_APP_SECRET", "vitruevoice_zalo_secret_demo"),
        help="Zalo App Secret để ký HMAC",
    )
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"❌ Không tìm thấy file âm thanh: {audio_path}")
        return

    audio_bytes = audio_path.read_bytes()
    port = get_free_port()
    host_ip = get_host_ip()

    # Serve file on host IP
    SingleFileHandler.file_bytes = audio_bytes
    server = http.server.HTTPServer(("0.0.0.0", port), SingleFileHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # In Docker on Windows/Mac, host.docker.internal resolves to the host machine
    audio_download_url = f"http://host.docker.internal:{port}/voice_message.wav"

    print("=" * 65)
    print("🤖 BỘ MÔ PHỎNG SỰ KIỆN ZALO OFFICIAL ACCOUNT (OA) WEBHOOK")
    print("=" * 65)
    print(f"📦 Tệp âm thanh thử nghiệm : {audio_path.name} ({len(audio_bytes)/1024:.1f} KB)")
    print(f"🌐 Mock Zalo CDN Server   : http://0.0.0.0:{port}/voice_message.wav")
    print(f"🎯 Điểm tiếp nhận Webhook  : {args.endpoint}")
    print(f"🔑 Chữ ký bảo mật Zalo     : HMAC-SHA256 (Secret: {args.secret[:4]}***)")

    timestamp_str = str(int(time.time() * 1000))
    zalo_payload = {
        "app_id": "184920491823901",
        "sender": {
            "id": "zalo_user_demo_001"
        },
        "recipient": {
            "id": "oa_vitruevoice_official"
        },
        "event_name": "user_send_audio",
        "message": {
            "msg_id": f"msg_zalo_{int(time.time())}",
            "attachments": [
                {
                    "type": "audio",
                    "payload": {
                        "url": audio_download_url
                    }
                }
            ]
        },
        "timestamp": int(timestamp_str),
    }

    payload_bytes = json.dumps(zalo_payload).encode("utf-8")
    sig_header = generate_zalo_signature(payload_bytes, secret=args.secret, timestamp=timestamp_str)

    headers = {
        "Content-Type": "application/json",
        "X-ZEvent-Signature": sig_header,
        "X-ZEvent-Timestamp": timestamp_str,
    }

    print("\n🚀 Đang gửi sự kiện 'user_send_audio' tới Webhook...")
    t0 = time.perf_counter()
    try:
        resp = requests.post(args.endpoint, data=payload_bytes, headers=headers, timeout=15.0)
        total_time = time.perf_counter() - t0
    except Exception as exc:
        print(f"❌ Lỗi kết nối tới máy chủ Webhook: {exc}")
        server.shutdown()
        return

    print(f"⚡ Trạng thái HTTP: {resp.status_code} (Tổng thời gian: {total_time:.2f}s)")
    if resp.status_code == 200:
        res_json = resp.json()
        print("\n" + "=" * 65)
        print("📥 KẾT QUẢ PHẢN HỒI TỪ VITRUEVOICE ZALO WEBHOOK:")
        print("=" * 65)
        if res_json.get("error") == 0 and "data" in res_json:
            data = res_json["data"]
            print(f"• Mã yêu cầu (Request ID): {data['request_id']}")
            print(f"• Phán quyết AI          : {data['prediction']} (Nhãn: {data['label']})")
            print(f"• Điểm thô (Raw Score)   : {data['raw_score']:+.4f} (Ngưỡng: {data['threshold']:+.4f})")
            print(f"• Độ tin cậy Platt       : {data['confidence'] * 100:.1f}%")
            print(f"• Số cửa sổ gộp (Pooling): {data['n_windows']} cửa sổ trượt")
            print(f"• Thời gian suy luận AI  : {data['latency_sec']:.2f}s")
            print(f"• Mã băm âm thanh SHA-256: {data['audio_sha256'][:16]}...")
            print("\n💬 [Tin nhắn gửi lại người dùng Zalo]:")
            print("-" * 65)
            print(data["reply_text"])
            print("-" * 65)
        else:
            print(json.dumps(res_json, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Lỗi: {resp.text}")

    server.shutdown()
    print("\n✅ Hoàn tất chu trình mô phỏng Zalo Webhook thành công!\n")


if __name__ == "__main__":
    main()
