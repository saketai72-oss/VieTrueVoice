"""Interactive Web Survey for Blind Listening Test (Phép đo 1).

Enables respondents to listen to all 12 compressed audio samples with inline audio players
and submit predictions directly into benchmarks/human_blind_responses.csv.

Usage:
    python scripts/survey_app.py
"""

import os
import sys
import datetime
import pandas as pd
import gradio as gr

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.evaluation.human_metrics import evaluate_human_responses

AUDIO_DIR = "benchmarks/blind_test_audio"
RESPONSES_CSV = "benchmarks/human_blind_responses.csv"
KEY_CSV = "benchmarks/blind_key_private.csv"


def save_responses(participant_id: str, *predictions):
    if not participant_id or not participant_id.strip():
        return "⚠️ Vui lòng nhập Mã định danh người tham gia (ví dụ: P01, P02...) trước khi gửi!"

    pid = participant_id.strip().upper()
    now_str = datetime.datetime.now().isoformat()

    new_rows = []
    for idx, pred in enumerate(predictions, start=1):
        sample_id = f"s{idx:02d}"
        if not pred:
            return f"⚠️ Bạn chưa chọn nhận định cho đoạn âm thanh {sample_id}. Vui lòng trả lời đủ 12 câu!"

        # Normalize label to 'bonafide' or 'spoof'
        std_label = "bonafide" if "Thật" in pred else "spoof"
        new_rows.append({
            "participant_id": pid,
            "sample_id": sample_id,
            "predicted_label": std_label,
            "timestamp": now_str,
        })

    # Append to CSV
    os.makedirs(os.path.dirname(RESPONSES_CSV), exist_ok=True)
    if os.path.exists(RESPONSES_CSV) and os.path.getsize(RESPONSES_CSV) > 0:
        df = pd.read_csv(RESPONSES_CSV)
        updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    else:
        updated_df = pd.DataFrame(new_rows)

    updated_df.to_csv(RESPONSES_CSV, index=False, encoding="utf-8")

    # Calculate real-time stats
    stats_msg = ""
    if os.path.exists(KEY_CSV):
        key_df = pd.read_csv(KEY_CSV)
        metrics = evaluate_human_responses(updated_df, key_df)
        stats_msg = (
            f"\n\n📊 Thống kê tổng hợp hiện tại ({metrics['total_trials']} lượt nghe):\n"
            f"- Tỷ lệ nhận diện sai của tai người: {metrics['error_rate'] * 100:.1f}%\n"
            f"- Khoảng tin cậy 95% Wilson CI: [{metrics['wilson_95_lower'] * 100:.1f}%, {metrics['wilson_95_upper'] * 100:.1f}%]"
        )

    return f"✅ Đã lưu thành công 12 câu trả lời của mã {pid}! Cảm ơn bạn.{stats_msg}"


def build_survey_ui():
    with gr.Blocks(title="ViTrueVoice - Khảo sát nhận diện giọng nói Thật / Giả") as demo:
        gr.Markdown(
            """
            # 🎙️ ViTrueVoice - Khảo Sát Nhận Diện Giọng Nói Thật / Giả (Phép Đo 1)
            **Mục tiêu**: Đánh giá khả năng phân biệt giọng người thật và giọng deepfake AI qua chất lượng thoại nén viễn thông.
            
            - **Cách làm**: Bấm nút **Play** để nghe từng đoạn thoại (3–4 giây) và chọn nhận định: **Thật** hoặc **Giả**.
            - **Ẩn danh**: Không thu thập tên hay email, chỉ dùng mã (ví dụ: `P01`, `P02`...).
            """
        )

        with gr.Row():
            pid_input = gr.Textbox(
                label="Mã định danh người tham gia (Participant ID)",
                placeholder="Ví dụ: P01, P02, P03...",
                scale=2,
            )

        radio_list = []
        gr.Markdown("### Danh sách 12 đoạn âm thanh")

        # Display in 2 columns for compact, clean layout
        for i in range(1, 13, 2):
            with gr.Row():
                for j in (i, i + 1):
                    if j <= 12:
                        sample_id = f"s{j:02d}"
                        audio_path = os.path.join(AUDIO_DIR, f"{sample_id}.wav")
                        with gr.Column():
                            gr.Markdown(f"#### Đoạn {sample_id}")
                            gr.Audio(value=audio_path, label=None, interactive=False, type="filepath")
                            r = gr.Radio(
                                choices=["Thật (Bona fide)", "Giả (Deepfake / AI)"],
                                label=f"Nhận định cho {sample_id}",
                                value=None,
                            )
                            radio_list.append(r)

        with gr.Row():
            submit_btn = gr.Button("🚀 Gửi Kết Quả Khảo Sát", variant="primary", size="lg")

        status_output = gr.Markdown()

        submit_btn.click(
            fn=save_responses,
            inputs=[pid_input] + radio_list,
            outputs=status_output,
        )

    return demo


if __name__ == "__main__":
    demo = build_survey_ui()
    # server_name="0.0.0.0" allows other devices on the same Wi-Fi (http://192.168.1.226:7860) to access
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, inbrowser=True)
