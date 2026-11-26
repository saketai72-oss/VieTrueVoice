# -*- coding: utf-8 -*-
"""
Chương 1, 2, 3: Bài toán Deepfake Tiếng Việt & Hệ đo lường chuẩn quốc tế,
Kiến trúc dữ liệu đối xứng v0.9.4 & Bộ lọc 4 cổng chống rò rỉ,
Tiền xử lý tín hiệu số (DSP), Repeat Padding, 5 Kênh Codec & RawBoost.
"""

from __future__ import annotations

from .styles import (
    add_bullet_item,
    add_callout_box,
    add_figure,
    add_foundation_primer,
    add_heading_chapter,
    add_heading_section,
    add_heading_subsection,
    add_omml_equation,
    add_styled_paragraph,
    add_styled_table,
    add_term_glossary,
    omml_delim,
    omml_frac,
    omml_r,
    omml_sqrt,
    omml_sub,
    omml_subsup,
    omml_sup,
)


def add_chapters_1_to_3(doc, figs: dict | None = None) -> None:
    """Render Chapters 1, 2, and 3 for the ViTrueVoice v0.9.4 Defense & Study Handbook."""

    # =========================================================================
    # CHƯƠNG 1: BÀI TOÁN DEEPFAKE TIẾNG VIỆT, GIẢ THUYẾT CH1/CH2 & HỆ ĐO LƯỜNG
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 1",
        "Bài Toán Deepfake Tiếng Việt, Giả Thuyết Khoa Học CH1/CH2 & Hệ Đo Lường Chuẩn Quốc Tế",
    )

    add_styled_paragraph(
        doc,
        "Chương 1 đặt nền móng khoa học cho toàn bộ đồ án: giải thích vì sao các cuộc tấn công mạo danh giọng nói "
        "trên ứng dụng nhắn tin OTT và mạng viễn thông Việt Nam lại vô hiệu hóa các bộ phát hiện phòng thí nghiệm truyền "
        "thống, cách thiết lập hệ thống giả thuyết định lượng tiên nghiệm (`CH1/H1`, `CH2/H2`, `NFR1`) và bản chất toán "
        "học tường minh của bộ chỉ số đánh giá sinh trắc học chuẩn quốc tế (`ISO/IEC 30107-3` & `ASVspoof`).",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 1.1 Bối cảnh lừa đảo OTT & Thách thức xóa mờ phổ cao tần
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "1.1 Bối Cảnh Lừa Đảo Giọng Nói Qua Kênh OTT/Viễn Thông Tại Việt Nam & Hiện Tượng Xóa Mờ Phổ Cao Tần",
    )

    add_foundation_primer(
        doc,
        process_name="Phân tích mối đe dọa Deepfake qua kênh thoại nén & Thiết kế giả thuyết khoa học",
        why_needed=(
            "Nếu không hiểu sự khác biệt vật lý giữa âm thanh phòng thu (WAV không nén) và âm thanh truyền qua Zalo hay "
            "mạng di động, sinh viên sẽ không giải thích được vì sao các mô hình quốc tế công bố sai số < 1% trên tập dữ "
            "liệu sạch nhưng lại sụp đổ nặng nề khi áp dụng vào tin nhắn thoại thực tế tại Việt Nam."
        ),
        real_analogy=(
            "Hãy tưởng tượng việc giám định chữ ký giả trên giấy tờ nhà đất: khi cầm tờ giấy gốc soi dưới kính lúp (tương "
            "đương tệp WAV phòng thu), chuyên gia thấy rõ từng hạt mực lem và độ ấn ngòi bút. Nhưng nếu kẻ gian chỉ gửi "
            "bản chụp qua máy Fax đen trắng mờ nhòe (tương đương tin nhắn thoại nén qua Zalo Opus 24kbps hoặc cuộc gọi "
            "GSM 8kHz), toàn bộ vết lem vi mô bị xóa sạch — chuyên gia buộc phải nhìn vào cấu trúc nhịp điệu nét chữ cốt lõi."
        ),
        core_points=[
            "Tấn công nhân bản giọng nói tức thời (Zero-Shot Voice Cloning) chỉ cần 3–10 giây âm thanh thu nhặt từ video mạng xã hội là đủ để tạo ra câu thoại mạo danh người thân vay tiền khẩn cấp.",
            "Tai người bình thường hoàn toàn không đủ khả năng phân biệt giọng nhân bản thế hệ mới qua loa điện thoại (thực nghiệm mù 72 lượt tại Tuần 2 ghi nhận tỷ lệ sai số tai người lên tới EER = 34,72%).",
            "Các bộ mã hóa nén âm thanh (Lossy Codecs) trên ứng dụng OTT và tổng đài viễn thông cắt bỏ dải tần số cao > 3,4 kHz (băng hẹp) hoặc > 7,5–7,8 kHz (băng rộng), vô tình tẩy xóa luôn các nhiễu kim loại cao tần của AI.",
            "Tiếng Việt là ngôn ngữ đơn lập có 6 thanh điệu (ngang, huyền, sắc, hỏi, ngã, nặng), đòi hỏi bộ trích xuất đặc trưng phải hiểu sâu đường cong cao độ bản địa thay vì bê nguyên mô hình huấn luyện trên tiếng Anh.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Tại Việt Nam, các kịch bản lừa đảo tài chính công nghệ cao đã dịch chuyển mạnh từ tin nhắn văn bản sang "
        "**mạo danh giọng nói nhân tạo (*Audio Deepfake Scam*)** trên các nền tảng nhắn tin OTT phổ biến (đặc biệt là "
        "Zalo, Telegram, Messenger) và mạng điện thoại di động. Chỉ với một đoạn giọng thật dài 3–7 giây lấy từ video "
        "TikTok, Facebook Reels hoặc một cuộc gọi nhá máy khảo sát trước đó, kẻ tấn công có thể dùng các công cụ nhân "
        "bản Zero-Shot thế hệ mới để tổng hợp những câu thoại khẩn cấp như *'Mẹ ơi chuyển gấp cho con 20 triệu viện phí'* "
        "hoặc giả danh nhân viên ngân hàng, cơ quan chức năng.",
    )

    add_styled_paragraph(
        doc,
        "Khảo sát đo lường cơ sở (*Human Baseline*) thực hiện tại Tuần 2 trên 72 lượt nghe thẩm định mù cho thấy: "
        "**người dùng bình thường mắc sai số cân bằng EER lên tới `34,72%`** (khoảng tin cậy 95% Wilson: `[24,75%, 46,24%]`), "
        "gần tương đương phán đoán cảm tính trong trạng thái hoảng loạn, đồng thời mất trung bình **`5,31 giây`** nghe lặp "
        "lại (hoặc 2–5 phút gọi điện xác minh chéo). Nguy hiểm hơn, khi âm thanh giả mạo đi qua đường truyền thực tế, nó "
        "chịu sự biến dạng vật lý nghiêm trọng gọi là **hiện tượng xóa mờ dấu vết cao tần (*High-Frequency Artifact Erasure*)**:",
    )

    add_bullet_item(
        doc,
        "Các bộ giải mã sóng âm (*Neural Vocoders*) thường để lộ sơ hở rõ nhất ở vùng tần số cao **từ `4,0 kHz` đến `8,0 kHz`** "
        "(hiện tượng nhiễu rít kim loại, phổ răng lược hoặc mờ nhòe phụ âm xát *s, x, kh, th*). Tuy nhiên, mạng điện thoại "
        "chuyển mạch kênh **`PSTN` (`G.711 A-law`)** và mạng di động **`2G/3G GSM` (`AMR-NB`)** thu hẹp tần số lấy mẫu "
        "xuống `8.000 Hz` kèm bộ lọc thông dải **`300 Hz – 3.400 Hz`**, xóa trắng 100% mọi thông tin trên `3,4 kHz`!",
        "1. Cắt cụt băng thông vật lý trên kênh thoại viễn thông (PSTN & GSM)",
    )
    add_bullet_item(
        doc,
        "Trên ứng dụng Zalo, tệp âm thanh đính kèm sử dụng chuẩn nén **`AAC-LC 76kbps`** (`.m4a`) và tin nhắn thoại trực "
        "tiếp sử dụng chuẩn **`Opus 24kbps`** (`.ogg`). Các thuật toán này áp dụng phép biến đổi cosin rời rạc sửa đổi "
        "(`MDCT`) kết hợp **mô hình che lấp tâm lý âm học (*Psychoacoustic Masking*)**: bất kỳ vi nhiễu phổ nào có năng "
        "lượng nhỏ nằm cạnh đỉnh nguyên âm lớn hoặc nằm trên ngưỡng **`7,5 – 7,8 kHz`** đều bị lượng tử hóa về 0 để tiết "
        "kiệm dung lượng truyền tải.",
        "2. Lượng tử hóa tâm lý âm học trên kênh nhắn tin OTT (Zalo AAC-LC & Opus)",
    )

    add_term_glossary(
        doc,
        [
            (
                "Deepfake Audio",
                "Âm thanh giả mạo sâu bằng AI",
                "Giọng nói được tổng hợp từ văn bản (TTS) hoặc chuyển đổi giọng (VC) bằng mạng nơ-ron sâu nhằm giả dạng một người thật.",
            ),
            (
                "OTT",
                "Over-The-Top Messaging",
                "Các ứng dụng nhắn tin và gọi thoại truyền qua mạng Internet như Zalo, Telegram, Messenger (khác với gọi SIM viễn thông truyền thống).",
            ),
            (
                "PSTN & GSM",
                "Public Switched Telephone Network & Global System for Mobile",
                "Mạng điện thoại cố định/tổng đài (PSTN) và mạng di động truyền thống (GSM), đặc trưng bởi băng thông hẹp 300–3.400 Hz ở tần số 8kHz.",
            ),
            (
                "Codec",
                "Coder-Decoder",
                "Thuật toán nén âm thanh ở đầu gửi và giải nén ở đầu nhận (ví dụ Opus, AAC-LC, G.711, AMR-NB) để giảm băng thông truyền dẫn.",
            ),
            (
                "MDCT",
                "Modified Discrete Cosine Transform",
                "Phép biến đổi toán học chuyển sóng âm sang miền tần số theo từng khối chồng lấp, là trái tim của các bộ nén AAC và Opus.",
            ),
            (
                "CM",
                "Countermeasure",
                "Hệ thống phòng vệ sinh trắc học đứng độc lập hoặc song song để phát hiện các cuộc tấn công giả mạo giọng nói.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 1.2 Câu hỏi nghiên cứu CH1/CH2, Giả thuyết H1/H2 và NFR1
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "1.2 Hệ Thống Câu Hỏi Nghiên Cứu (CH1, CH2), Giả Thuyết Định Lượng (H1, H2) & Chỉ Tiêu Độ Trễ (NFR1)",
    )

    add_styled_paragraph(
        doc,
        "Để đảm bảo tính khách quan khoa học nghiêm ngặt (tránh ngụy biện sửa mục tiêu sau khi đã biết kết quả), đồ án "
        "thiết lập ngay từ đầu **2 Câu hỏi nghiên cứu (`CH1`, `CH2`)**, **2 Giả thuyết khoa học định lượng (`H1`, `H2`)** "
        "và **Yêu cầu phi chức năng cốt lõi về thời gian thực (`NFR1`)**, đối chiếu trực tiếp với kết quả thực nghiệm của "
        "phiên bản phát hành **`ViTrueVoice v0.9.4`**:",
    )

    add_bullet_item(
        doc,
        "**Câu hỏi `CH1` (*Độ bền nén kênh thoại*)**: Mức độ suy giảm hiệu năng khi giọng nói đi qua kênh nén Zalo và viễn "
        "thông là bao nhiêu, và chiến lược huấn luyện tăng cường đa kênh nén kết hợp nhiễu `RawBoost` giúp cải thiện sức "
        "đề kháng như thế nào?\n"
        "→ **Giả thuyết `H1` & KPI Nội bộ**: Tăng cường nén kênh thoại trong quá trình huấn luyện giúp **giảm ít nhất "
        "`≥ 30%` tỷ lệ sai số EER tương đối** trên tập kiểm thử nén so với mô hình cơ sở không tăng cường, đồng thời đạt "
        "**In-domain EER `≤ 8,0%`** trên tập người nói độc lập.\n"
        "→ **Kết quả kiểm chứng `v0.9.4` (ĐẠT XUẤT SẮC)**: Đối chứng khoa học xác nhận giảm `40,46%` EER tương đối trên "
        "`AMR-NB` và `47,55%` trên `G.711`. Trên tập kiểm thử độc lập quy mô lớn **`15.980` mẫu** (`test_indomain_v8_f5_omni.csv`), "
        "mô hình `v0.9.4` đạt tổng thể **`5,63%` EER** (chặn `95,01%` mẫu giả), duy trì vững chắc dưới trần 8% trên cả "
        "5/5 kênh truyền (`Clean 16kHz`: `5,52%` | `Zalo AAC-LC 76k`: `5,79%` | `Zalo Opus 24k`: `6,02%` | `G.711`: `6,11%` | "
        "`AMR-NB`: **`4,88%`**).",
        "1. Trục Nghiên Cứu Kênh Thoại Nén (CH1 → Giả thuyết H1)",
    )
    add_bullet_item(
        doc,
        "**Câu hỏi `CH2` (*Khái quát hóa ngoài phân phối — OOD Generalization*)**: Khi xuất hiện một động cơ nhân bản giọng "
        "nói Zero-Shot có kiến trúc hoàn toàn mới chưa từng có mặt trong tập huấn luyện hay tập thẩm định Dev, mô hình có "
        "còn phát hiện được bản chất giả mạo hay không?\n"
        "→ **Giả thuyết `H2` (`NFR2`)**: Mô hình duy trì **tỷ lệ sai số cân bằng `EER ≤ 15,0%`** trên động cơ Zero-Shot "
        "TTS hoàn toàn chưa từng thấy (*Unseen TTS*).\n"
        "→ **Kết quả kiểm chứng `v0.9.4` (ĐẠT THUYẾT PHỤC)**: Đối mặt với động cơ Unseen Zero-Shot **`VieNeu-TTS v3 Turbo`** "
        "(kiến trúc `Qwen LLM + NeuCodec 48kHz` khác biệt hoàn toàn với họ Flow Matching dùng khi huấn luyện), mô hình "
        "`v0.9.4` đạt **`12,05%` EER** trên tập chuẩn **`955` mẫu** OOD Dev (`unseen_vieneu_benchmark.csv`, chặn thành công "
        "`79,6%`) và đạt **`6,90%` EER** trên **`375` mẫu** nhân bản của 5 tình nguyện viên nghiệm thu độc lập.",
        "2. Trục Nghiên Cứu Động Cơ Lạ Chưa Từng Thấy (CH2 → Giả thuyết H2)",
    )
    add_bullet_item(
        doc,
        "**Mục tiêu `NFR1` (*Độ trễ phản hồi thời gian thực*)**: Trung vị thời gian xử lý toàn trình từ lúc gửi đoạn thoại "
        "(3–10 giây) đến khi trả nhãn Thật/Giả và xác suất tin cậy phải đạt **`≤ 3,0 giây`** trên phần cứng tiêu chuẩn.\n"
        "→ **Kết quả kiểm chứng `v0.9.4` (NHANH GẤP ~3–4 LẦN MỤC TIÊU)**: Đạt trung vị **`1,101 giây`** trên bộ đo chuẩn "
        "30 lần lặp liên tiếp (`benchmarks/latency_benchmark.csv`) và **`0,705 giây`** trên 140 lượt suy luận thực tế ghi "
        "nhận ẩn danh (`benchmarks/latency_log.json`).",
        "3. Trục Yêu Cầu Phi Chức Năng Thời Gian Thực (NFR1 — Latency)",
    )

    add_styled_table(
        doc,
        headers=[
            "Mã Giả Thuyết / KPI",
            "Nội Dung Kiểm Định Khoa Học",
            "Ngưỡng Mục Tiêu",
            "Tập Đo Lường Độc Lập",
            "Kết Quả Chính Thức v0.9.4",
        ],
        rows=[
            (
                "H1 (Câu hỏi CH1)",
                "Độ bền nén 5 kênh thoại & giảm sai số tương đối nhờ tăng cường kênh truyền",
                "In-domain EER ≤ 8,0% (giảm ≥ 30% EER nén)",
                "15.980 mẫu Test In-domain (15 người nói VIVOS × 5 codecs)",
                "5,63% EER (chặn 95,01%; giảm 40,46%–47,55% lỗi kênh hẹp) — ĐẠT",
            ),
            (
                "H2 (Câu hỏi CH2 / NFR2)",
                "Tổng quát hóa trên động cơ Zero-Shot TTS lạ (VieNeu-TTS v3 Turbo)",
                "Unseen TTS EER ≤ 15,0%",
                "955 mẫu Unseen Dev & 375 mẫu Unseen 5-SPK nghiệm thu",
                "12,05% EER (955 mẫu Dev) & 6,90% EER (375 mẫu 5-SPK) — ĐẠT",
            ),
            (
                "NFR1 (Thời gian thực)",
                "Trung vị thời gian phản hồi suy luận toàn trình đa cửa sổ (5 windows)",
                "Trung vị ≤ 3,0 giây",
                "30 lượt bấm giờ chuẩn & 140 lượt truy vấn thực tế",
                "1,101 giây (benchmark 30 ca) & 0,705 giây (log thực tế) — ĐẠT",
            ),
            (
                "Đối chứng Tai người",
                "Khả năng phân biệt thật/giả bằng thính giác tự nhiên của con người",
                "Mốc cơ sở trước khi có AI",
                "72 lượt nghe mù độc lập (Tuần 2)",
                "EER = 34,72% | Thời gian nghe 5,31 giây (cải thiện > 6 lần nhờ v0.9.4)",
            ),
        ],
        col_widths=[1.20, 1.75, 1.15, 1.30, 1.30],
        highlight_row_pred=lambda idx, _: idx < 3,
    )

    add_term_glossary(
        doc,
        [
            (
                "CH1 & CH2",
                "Câu hỏi nghiên cứu 1 & 2 (Research Questions)",
                "Hai vấn đề khoa học trọng tâm mà đồ án đặt ra về độ bền kênh truyền nén (CH1) và khả năng bắt công cụ TTS mới (CH2).",
            ),
            (
                "H1 & H2",
                "Giả thuyết khoa học 1 & 2 (Hypotheses)",
                "Các mệnh đề dự đoán có ngưỡng con số cụ thể (EER ≤ 8% và EER ≤ 15%) để chứng minh thực nghiệm Đạt hoặc Không đạt.",
            ),
            (
                "NFR1 & NFR2",
                "Non-Functional Requirements",
                "Yêu cầu phi chức năng về chất lượng vận hành hệ thống: độ trễ phản hồi ≤ 3,0s (NFR1) và sức bền trước công cụ lạ (NFR2).",
            ),
            (
                "Seen TTS vs. Unseen TTS",
                "Công cụ TTS đã gặp vs. Chưa từng gặp",
                "Seen TTS có mặt trong tập Train (F5-TTS, OmniVoice CFM); Unseen TTS bị giấu kín 100% lúc học chỉ đem ra thi (VieNeu-TTS v3 Turbo).",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 1.3 Toán học các chỉ số đánh giá sinh trắc học chuẩn quốc tế
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "1.3 Toán Học Hệ Đo Lường Sinh Trắc Học Chuẩn Quốc Tế (Logit, APCER, BPCER, EER & minDCF)",
    )

    add_foundation_primer(
        doc,
        process_name="Đo lường sai số hệ thống chống giả mạo theo chuẩn ISO/IEC 30107-3 & ASVspoof",
        why_needed=(
            "Trong học máy nhập môn, sinh viên quen dùng Độ chính xác (Accuracy = số câu đoán đúng / tổng số câu). "
            "Tuy nhiên, đem Accuracy vào bài toán an ninh chống lừa đảo là một sai lầm nghiêm trọng có thể che giấu "
            "một hệ thống bỏ lọt 100% tội phạm! Mục này giúp sinh viên nắm chắc từng công thức chuẩn quốc tế."
        ),
        real_analogy=(
            "Hãy liên hệ với hệ thống chuông báo cháy tự động ở chung cư: "
            "(1) Báo động giả (BPCER): chỉ có hơi nước luộc rau mà còi hú ầm ĩ làm cư dân hoảng sợ chạy xuống sảnh — gây phiền toái nhưng tài sản vẫn còn nguyên; "
            "(2) Bỏ lọt đám cháy thật (APCER): lửa bùng lên trong phòng nhưng chuông im bặt — gây thiệt hại thảm khốc! "
            "Nếu vặn nút chỉnh độ nhạy (ngưỡng θ) quá cao, chuông bắt sạch đám cháy nhưng suốt ngày báo giả; nếu vặn quá thấp, cư dân ngủ ngon nhưng cháy thật lại không kêu. "
            "Điểm EER chính là vị trí vặn nút cân bằng nơi tỷ lệ báo giả bằng đúng tỷ lệ bỏ lọt cháy!"
        ),
        core_points=[
            "Nghịch lý Độ chính xác (Accuracy Paradox): Trên thực tế nếu 90% tin nhắn thoại là người thật (Bonafide) và chỉ 10% là lừa đảo (Spoof), một đoạn hàm rỗng luôn trả về 'Người thật' không cần học gì cả vẫn đạt Accuracy = 90%, dù nó để lọt lưới 100% kẻ lừa đảo (APCER = 100%).",
            "Quy ước trục số của điểm thô s(x): Mọi điểm s(x) ≥ 0,0 nghiêng về lớp Giọng Thật (Lớp 1 — Bonafide); mọi điểm s(x) < 0,0 nghiêng về lớp Giọng Giả (Lớp 0 — Spoof). Mốc θ = 0,0 là ranh giới tự nhiên nơi hai lớp cân bằng lực kéo.",
            "Tính bất biến tỷ lệ mẫu của EER: Vì APCER tính riêng trên tập mẫu giả và BPCER tính riêng trên tập mẫu thật, dù tỷ lệ thật/giả ngoài đời là 90:10 hay 50:50 thì giá trị EER vẫn giữ nguyên không đổi.",
            "Trọng số rủi ro bất đối xứng trong minDCF: Thiệt hại tài chính khi bỏ lọt một cuộc gọi lừa đảo lớn gấp nhiều lần sự bất tiện khi cảnh báo nhầm một cuộc gọi thật, nên chuẩn NIST/ASVspoof phạt lỗi bỏ lọt nặng gấp 10 lần.",
        ],
    )

    add_heading_subsection(
        doc,
        "1.3.1 Điểm Số Biên Logit Thô s(x) & Quy Tắc Quyết Định Tại Ngưỡng θ = 0,0",
    )
    add_styled_paragraph(
        doc,
        "Ở tầng đầu ra cuối cùng của mạng `SSL-AASIST`, với mỗi cửa sổ âm thanh đầu vào `x`, mô hình sinh ra một vector "
        "gồm 2 giá trị thực chưa chuẩn hóa xác suất gọi là **Logits**: `z₀(x)` biểu thị mức độ khớp với lớp **Giọng Giả "
        "(Spoof — nhãn `0`)** và `z₁(x)` biểu thị mức độ khớp với lớp **Giọng Thật (Bonafide — nhãn `1`)**. Điểm thẩm định "
        "thô `s(x)` được định nghĩa là hiệu số biên trực tiếp giữa hai logit này:",
    )

    logit_eq = (
        omml_r("s")
        + omml_delim(omml_r("x"))
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("z"), omml_r("1", normal=True))
        + omml_delim(omml_r("x"))
        + omml_r(" − ", normal=True)
        + omml_sub(omml_r("z"), omml_r("0", normal=True))
        + omml_delim(omml_r("x"))
    )
    add_omml_equation(
        doc,
        "Điểm biên Logit thô (Raw Logit Margin Score)",
        logit_eq,
        variables=[
            ("x", "Đoạn tín hiệu âm thanh đầu vào đã chuẩn hóa (hoặc từng cửa sổ 64.000 mẫu trong suy luận đa cửa sổ)."),
            ("z₁(x)", "Giá trị logit đầu ra tương ứng với lớp Giọng Người Thật (Bonafide, nhãn lớp c = 1)."),
            ("z₀(x)", "Giá trị logit đầu ra tương ứng với lớp Giọng Giả Mạo AI (Spoof, nhãn lớp c = 0)."),
            ("s(x)", "Điểm quyết định liên tục: nếu s(x) ≥ θ kết luận Bonafide; nếu s(x) < θ kết luận Spoof (ngưỡng vận hành mặc định θ = 0,0)."),
        ],
    )

    add_styled_paragraph(
        doc,
        "**Ví dụ thay số trực quan**: Giả sử một bản ghi giọng thật của tình nguyện viên đi qua mạng cho `z₁ = +14,20` và "
        "`z₀ = −13,80` → điểm thô `s(x) = 14,20 − (−13,80) = +28,00 ≥ 0,0` → Hệ thống kết luận **GIỌNG NGƯỜI THẬT**. Ngược "
        "lại, một mẫu nhân bản từ `OmniVoice CFM` cho `z₁ = −16,50` và `z₀ = +15,00` → điểm thô `s(x) = −16,50 − 15,00 = "
        "−31,50 < 0,0` → Hệ thống lập tức phát cảnh báo **GIỌNG GIẢ MẠO AI**.",
    )

    add_heading_subsection(
        doc,
        "1.3.2 Hai Tỷ Lệ Sai Số Sinh Trắc Học Chuẩn ISO/IEC 30107-3: APCER(θ) và BPCER(θ)",
    )
    add_styled_paragraph(
        doc,
        "Tiêu chuẩn quốc tế về chống giả mạo sinh trắc học **`ISO/IEC 30107-3`** định nghĩa hai tỷ lệ lỗi tách biệt hoàn "
        "toàn theo bản chất của mẫu kiểm tra tại một ngưỡng cắt `θ` bất kỳ:",
    )

    apcer_eq = (
        omml_r("APCER", normal=True)
        + omml_delim(omml_r("θ"))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("1", normal=True),
            omml_sub(omml_r("N"), omml_r("spoof", normal=True)),
        )
        + omml_r(" ", normal=True)
        + omml_subsup(
            omml_r("∑", normal=True),
            omml_r("i=1", normal=True),
            omml_sub(omml_r("N"), omml_r("spoof", normal=True)),
        )
        + omml_r(" 𝕀", normal=True)
        + omml_delim(
            omml_r("s")
            + omml_delim(omml_sub(omml_r("x"), omml_r("i")))
            + omml_r(" ≥ θ", normal=True),
            beg="(",
            end=")",
        )
    )
    add_omml_equation(
        doc,
        "Tỷ lệ lọt lưới tấn công giả mạo APCER(θ) — Tương đương FAR theo chuẩn ISO/IEC 30107-3",
        apcer_eq,
        variables=[
            ("APCER(θ)", "Attack Presentation Classification Error Rate tại ngưỡng θ: tỷ lệ mẫu giả mạo bị hệ thống chấm điểm ≥ θ nên lọt lưới thành người thật."),
            ("N_spoof", "Tổng số mẫu giọng giả mạo (Spoof) có mặt trong tập kiểm thử."),
            ("x_i", "Mẫu giọng giả mạo thứ i trong tập kiểm thử (i chạy từ 1 đến N_spoof)."),
            ("𝕀(s(x_i) ≥ θ)", "Hàm chỉ báo toán học: nhận giá trị bằng 1 nếu điều kiện bên trong đúng (bị lọt lưới), bằng 0 nếu sai (đã chặn thành công)."),
        ],
    )

    bpcer_eq = (
        omml_r("BPCER", normal=True)
        + omml_delim(omml_r("θ"))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("1", normal=True),
            omml_sub(omml_r("N"), omml_r("bona", normal=True)),
        )
        + omml_r(" ", normal=True)
        + omml_subsup(
            omml_r("∑", normal=True),
            omml_r("j=1", normal=True),
            omml_sub(omml_r("N"), omml_r("bona", normal=True)),
        )
        + omml_r(" 𝕀", normal=True)
        + omml_delim(
            omml_r("s")
            + omml_delim(omml_sub(omml_r("x"), omml_r("j")))
            + omml_r(" < θ", normal=True),
            beg="(",
            end=")",
        )
    )
    add_omml_equation(
        doc,
        "Tỷ lệ từ chối nhầm người thật BPCER(θ) — Tương đương FRR theo chuẩn ISO/IEC 30107-3",
        bpcer_eq,
        variables=[
            ("BPCER(θ)", "Bona Fide Presentation Classification Error Rate tại ngưỡng θ: tỷ lệ mẫu người thật bị chấm điểm < θ nên bị báo động giả là AI."),
            ("N_bona", "Tổng số mẫu giọng người thật (Bonafide) có mặt trong tập kiểm thử."),
            ("x_j", "Mẫu giọng người thật thứ j trong tập kiểm thử (j chạy từ 1 đến N_bona)."),
            ("𝕀(s(x_j) < θ)", "Hàm chỉ báo: bằng 1 nếu người thật bị báo nhầm là giả mạo, bằng 0 nếu được nhận diện đúng là người thật."),
        ],
    )

    add_styled_paragraph(
        doc,
        "Từ `APCER(θ)` ở ngưỡng vận hành `θ = 0,0`, ta suy ra trực tiếp **Tỷ lệ chặn đứng giả mạo (*Spoof Block Rate*)** "
        "= `100% − APCER(0,0)` (ví dụ trên tập kiểm thử nội bộ `15.980` mẫu, `v0.9.4` đạt tỷ lệ chặn **`95,01%`**, tức "
        "`APCER(0,0) = 4,99%`), và **Tỷ lệ vượt qua của giọng thật (*Bonafide Pass Rate*)** = `100% − BPCER(0,0)`.",
    )

    add_heading_subsection(
        doc,
        "1.3.3 Tỷ Lệ Sai Số Cân Bằng EER (Equal Error Rate) & Đường Cong DET",
    )
    add_styled_paragraph(
        doc,
        "Khi ta tăng dần ngưỡng `θ` từ âm vô cùng lên dương vô cùng: điều kiện để được công nhận là người thật ngày càng "
        "khắt khe hơn, nên tỷ lệ lọt lưới giả mạo `APCER(θ)` giảm dần về `0%`, nhưng ngược lại tỷ lệ báo nhầm người thật "
        "`BPCER(θ)` lại tăng dần lên `100%`. Hai đường cong đơn điệu ngược chiều này giao nhau tại một ngưỡng duy nhất "
        "gọi là **`θ_EER`**, xác định **Tỷ lệ sai số cân bằng `EER`**:",
    )

    eer_eq = (
        omml_r("EER", normal=True)
        + omml_r(" = ", normal=True)
        + omml_r("APCER", normal=True)
        + omml_delim(omml_sub(omml_r("θ"), omml_r("EER", normal=True)))
        + omml_r(" = ", normal=True)
        + omml_r("BPCER", normal=True)
        + omml_delim(omml_sub(omml_r("θ"), omml_r("EER", normal=True)))
    )
    add_omml_equation(
        doc,
        "Tỷ lệ sai số cân bằng EER (Equal Error Rate)",
        eer_eq,
        variables=[
            ("θ_EER", "Ngưỡng cắt cân bằng lý thuyết nơi hai loại sai số trái ngược nhau đạt giá trị bằng nhau."),
            ("EER", "Chỉ số tổng quát độc lập ngưỡng đo độ chồng lấn giữa hai phân phối Thật và Giả (EER càng tiến gần 0% thì hai phân phối càng tách rời hoàn hảo)."),
        ],
    )

    add_heading_subsection(
        doc,
        "1.3.4 Hàm Chi Phí Phát Hiện Tối Thiểu minDCF (Chuẩn ASVspoof & NIST)",
    )
    add_styled_paragraph(
        doc,
        "`EER` coi trọng số của hai lỗi `APCER` và `BPCER` là ngang nhau (`1 : 1`). Tuy nhiên, trong bối cảnh phòng chống "
        "tội phạm lừa đảo ngân hàng và tin nhắn thoại khẩn cấp, hậu quả của việc bỏ lọt một cuộc gọi giả mạo nghiêm trọng "
        "gấp nhiều lần việc hiện cảnh báo thận trọng trên một cuộc gọi thật. Do đó, hiệp hội **`ASVspoof` và Viện `NIST`** "
        "quy định sử dụng **Hàm chi phí phát hiện tối thiểu chuẩn hóa (`minDCF`)** dựa trên Lý thuyết quyết định Bayes:",
    )

    dcf_num = (
        omml_sub(omml_r("C"), omml_r("miss", normal=True))
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("P"), omml_r("target", normal=True))
        + omml_r(" · ", normal=True)
        + omml_r("BPCER", normal=True)
        + omml_delim(omml_r("θ"))
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("C"), omml_r("fa", normal=True))
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("P"), omml_r("spoof", normal=True))
        + omml_r(" · ", normal=True)
        + omml_r("APCER", normal=True)
        + omml_delim(omml_r("θ"))
    )
    dcf_den = (
        omml_r("min", normal=True)
        + omml_delim(
            omml_sub(omml_r("C"), omml_r("miss", normal=True))
            + omml_r(" · ", normal=True)
            + omml_sub(omml_r("P"), omml_r("target", normal=True))
            + omml_r(" , ", normal=True)
            + omml_sub(omml_r("C"), omml_r("fa", normal=True))
            + omml_r(" · ", normal=True)
            + omml_sub(omml_r("P"), omml_r("spoof", normal=True)),
            beg="(",
            end=")",
        )
    )
    mindcf_eq = (
        omml_r("minDCF", normal=True)
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("min", normal=True), omml_r("θ"))
        + omml_r(" ", normal=True)
        + omml_frac(dcf_num, dcf_den)
    )
    add_omml_equation(
        doc,
        "Hàm chi phí phát hiện tối thiểu chuẩn hóa minDCF (ASVspoof / NIST)",
        mindcf_eq,
        variables=[
            ("C_miss = 1", "Chi phí thiệt hại khi từ chối nhầm một mẫu giọng người thật (False Rejection / Miss)."),
            ("C_fa = 10", "Chi phí thiệt hại khi chấp nhận nhầm một mẫu giả mạo thành người thật (False Acceptance — phạt nặng gấp 10 lần C_miss)."),
            ("P_target, P_spoof", "Xác suất tiên nghiệm gặp giọng người thật và giọng tấn công giả mạo (thỏa mãn P_target + P_spoof = 1, cấu hình chuẩn P_spoof = 0,05 hoặc 0,95 tùy kịch bản ASVspoof)."),
            ("Mẫu số chuẩn hóa", "Chi phí của một bộ phân loại mù tối ưu (luôn chọn hoàn toàn một lớp ít thiệt hại hơn), giúp chuẩn hóa minDCF ≤ 1,0 (càng gần 0,0 càng xuất sắc)."),
        ],
    )

    if figs and "fig1" in figs:
        add_figure(
            doc,
            figs["fig1"],
            "Hình 1.1: Minh họa trực quan cơ chế chấm điểm và đánh giá của ViTrueVoice v0.9.4. "
            "Khung A (Trái): Mật độ phân phối điểm thô s = z_bonafide − z_spoof của lớp Giọng Giả (đỏ) và Giọng Thật (xanh lá) "
            "quanh vạch ngưỡng quyết định θ = 0,0, làm rõ phần diện tích đuôi chồng lấn gây lỗi lọt lưới giả mạo APCER (s ≥ 0) "
            "và lỗi báo nhầm người thật BPCER (s < 0). Khung B (Phải): Đường cong đánh đổi lỗi phát hiện DET cắt đường phân giác "
            "APCER = BPCER ngay tại điểm cân bằng EER = 5,63% trên tập kiểm thử nội bộ 15.980 mẫu.",
        )

    add_callout_box(
        doc,
        "Khi Hội đồng hỏi: **'Vì sao trong bảng kết quả em báo cáo cả EER, minDCF lẫn Tỷ lệ chặn tại θ = 0,0?'**, hãy "
        "trả lời mạch lạc 3 ý: *(1) EER đo năng lực phân tách nội tại của kiến trúc mạng độc lập với ngưỡng cắt và tỷ lệ "
        "mất cân bằng dữ liệu; (2) minDCF đo hiệu quả quản trị rủi ro an ninh khi lỗi bỏ lọt tội phạm bị phạt nặng gấp "
        "10 lần lỗi báo nhầm; (3) Tỷ lệ chặn và BPCER tại ngưỡng khóa cứng θ = 0,0 phản ánh chính xác hành vi thực tế của "
        "API và Bot khi phục vụ người dân theo thời gian thực (bởi ngoài đời thực hệ thống phải ra quyết định ngay trên 1 "
        "tệp đơn lẻ chứ không thể biết trước nhãn để dò ngưỡng θ_EER).* ",
        title="BÍ QUYẾT PHẢN BIỆN CHƯƠNG 1: PHỐI HỢP BỘ BA CHỈ SỐ EER — minDCF — NGƯỠNG θ = 0,0",
    )

    add_term_glossary(
        doc,
        [
            (
                "Logit",
                "Unnormalized Log-Odds Score",
                "Đầu ra số thực thô của tầng tuyến tính cuối cùng trong mạng nơ-ron (có thể âm hoặc dương tùy ý) trước khi đưa qua hàm Softmax/Sigmoid.",
            ),
            (
                "ISO/IEC 30107-3",
                "Biometric Presentation Attack Detection — Part 3",
                "Bộ tiêu chuẩn quốc tế quy định cách đo lường và báo cáo sai số (APCER, BPCER) cho mọi hệ thống chống giả mạo sinh trắc học.",
            ),
            (
                "APCER / FAR",
                "Attack Presentation Classification Error Rate / False Acceptance Rate",
                "Xác suất một mẫu tấn công giọng giả vượt qua hàng rào kiểm duyệt và bị nhận nhầm là người thật.",
            ),
            (
                "BPCER / FRR",
                "Bona Fide Presentation Classification Error Rate / False Rejection Rate",
                "Xác suất một mẫu giọng người thật hợp lệ bị hệ thống từ chối nhầm thành giọng nhân tạo.",
            ),
            (
                "EER",
                "Equal Error Rate",
                "Tỷ lệ sai số cân bằng nơi APCER và BPCER gặp nhau; con số chuẩn vàng của cộng đồng xử lý tiếng nói quốc tế.",
            ),
            (
                "minDCF",
                "Minimum Detection Cost Function",
                "Hàm chi phí quyết định tối thiểu chuẩn hóa có trọng số rủi ro bất đối xứng của cuộc thi quốc tế ASVspoof.",
            ),
            (
                "DET & ROC-AUC",
                "Detection Error Trade-off & Area Under ROC Curve",
                "Đồ thị DET vẽ trực tiếp cặp lỗi (APCER, BPCER); còn ROC-AUC đo diện tích dưới đường cong thu nhận (AUC = 1,0 là tách biệt tuyệt đối).",
            ),
        ],
    )

    # =========================================================================
    # CHƯƠNG 2: KIẾN TRÚC DỮ LIỆU ĐỐI XỨNG v0.9.4 & BỘ LỌC 4 CỔNG CHỐNG RÒ RỈ
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 2",
        "Kiến Trúc Dữ Liệu Đối Xứng v0.9.4, Sinh Mẫu Zero-Shot Kép & Bộ Lọc 4 Cổng Chống Rò Rỉ",
    )

    add_styled_paragraph(
        doc,
        "Trong học sâu hiện đại, chất lượng thiết kế tập dữ liệu quyết định trực tiếp tính trung thực của mọi con số thực "
        "nghiệm. Chương 2 trình bày chi tiết kiến trúc dữ liệu đối xứng của **`ViTrueVoice v0.9.4`**: cách tổ chức 3 nguồn "
        "giọng thật tiếng Việt, sự phân vai chiến lược giữa hai động cơ Seen TTS đối xứng (`F5-TTS` + `OmniVoice CFM`) và "
        "động cơ Unseen TTS (`VieNeu-TTS v3 Turbo`), các rào chắn toán học chống rò rỉ dữ liệu 100%, bộ lọc chất lượng tự "
        "động 4 cổng cùng hệ thống 5 tệp Manifest 19 cột và kho lưu trữ nghiệm thu `Voice_Final` (`103.189` tệp).",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 2.1 Nguồn dữ liệu Bonafide & Phân công động cơ TTS v0.9.4
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "2.1 Ba Nguồn Giọng Thật (Bonafide) & Phân Công Động Cơ TTS Đối Xứng Trong ViTrueVoice v0.9.4",
    )

    add_foundation_primer(
        doc,
        process_name="Thiết kế tập dữ liệu nhân bản giọng nói Zero-Shot & Phòng chống rò rỉ dữ liệu (Data Leakage)",
        why_needed=(
            "Rất nhiều đề tài nhận diện giọng giả đạt EER 0,1% trên giấy nhưng khi đem ra chạy thử giọng người ngoài đời "
            "thì đoán sai hoàn toàn. Nguyên nhân nằm ở hiện tượng rò rỉ người nói, đường tắt câu chữ hoặc dùng nhầm công "
            "cụ đọc văn bản cố định thay vì công cụ nhân bản giọng nói thực thụ."
        ),
        real_analogy=(
            "Hãy hình dung kỳ thi sát hạch bác sĩ chẩn đoán hình ảnh: "
            "(1) Rò rỉ người nói (Speaker Leakage) giống như lấy đúng ảnh X-quang của bệnh nhân Nguyễn Văn A lúc học trên lớp đem vào đề thi tốt nghiệp — sinh viên nhớ tên bệnh nhân chứ không biết đọc phim; "
            "(2) Đường tắt văn bản (Text Shortcut) giống như mọi ca có bệnh trong đề ôn tập đều chụp kèm chữ 'CẤP CỨU' ở góc phim — sinh viên chỉ nhìn góc chữ mà đoán đúng 100%!"
        ),
        core_points=[
            "Zero-Shot Voice Cloning vs. Preset Multi-Speaker TTS: Preset TTS chỉ đọc bằng 5–10 giọng phát thanh viên đóng sẵn trong phần mềm (không thể giả giọng người thân của bạn); còn Zero-Shot Voice Cloning nghe một đoạn audio mẫu 3–7 giây của bất kỳ ai và lập tức tổng hợp câu thoại mới mang đúng âm sắc người đó.",
            "Trường phái Continuous Flow Matching (CFM — như F5-TTS, OmniVoice CFM) biến đổi nhiễu liên tục thành phổ âm thanh cực kỳ mượt qua phương trình vi phân; trong khi trường phái Discrete Neural Codec TTS (như VieNeu-TTS v3 Turbo) lượng tử hóa âm thanh thành các mã token rời rạc điều khiển bởi mô hình ngôn ngữ lớn (LLM).",
            "Rò rỉ dữ liệu (Data Leakage) xảy ra ngay cả khi hai tệp âm thanh khác tên nhau nhưng cùng một người đọc hoặc đọc cùng một câu kịch bản ở cả tập Train và tập Test.",
        ],
    )

    add_heading_subsection(
        doc,
        "2.1.1 Ba Nguồn Dữ Liệu Giọng Người Thật Tiếng Việt (Bonafide Corpora)",
    )
    add_styled_paragraph(
        doc,
        "Hệ thống sử dụng kết hợp 3 nguồn âm thanh giọng người thật bổ trợ lẫn nhau về môi trường thu âm, thiết bị micro "
        "và vùng miền phương ngữ tiếng Việt:",
    )

    add_bullet_item(
        doc,
        "Gồm **15 giờ âm thanh chuẩn phòng thu `16kHz` Mono** của **`65` người nói** (cả giọng Bắc và giọng Nam, giấy phép "
        "học thuật `CC BY-NC 4.0`). Tập `VIVOS` được chia tách cứng theo người nói: `40` người nói phục vụ tập Train, `10` "
        "người nói phục vụ tập Dev và **`15` người nói giữ riêng hoàn toàn** cho tập kiểm thử nội bộ (`Test In-domain`).",
        "1. Kho ngữ liệu chuẩn VIVOS (ĐHQG TP.HCM)",
    )
    add_bullet_item(
        doc,
        "Gồm **`22,97` giờ âm thanh thực tế** từ **`419` người nói** khắp các tỉnh thành thu âm qua micro điện thoại, tai "
        "nghe và laptop cá nhân (giấy phép mở `CC0 1.0`). Dữ liệu được lọc nghiêm ngặt từ `validated.tsv` với điều kiện "
        "`up_votes ≥ 2`, `down_votes = 0`, độ dài câu `> 10` ký tự, loại bỏ câu chứa chữ số và kiểm tra bitrate nén gốc "
        "ghi vào cột `pre_codec`.",
        "2. Kho ngữ liệu cộng đồng Mozilla Common Voice 8.0 (Tiếng Việt)",
    )
    add_bullet_item(
        doc,
        "Thu âm trực tiếp có ký Phiếu đồng ý thu thập dữ liệu sinh trắc học (*Consent Form*) tuân thủ Luật Bảo vệ dữ liệu "
        "cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP. Trong tổng số 6 tình nguyện viên đã thu âm (`SPK_0001`, "
        "`SPK_0003..0007`), **5 tình nguyện viên (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007` — gồm `84` "
        "tệp gốc sạch × `5` biến thể codec = `420` tệp bonafide)** được khóa cứng làm **Bộ Nghiệm Thu Độc Lập Chính Thức "
        "cô lập 100%** (tuyệt đối không xuất hiện trong Train, Dev, hiệu chuẩn hay chọn ngưỡng). Do bộ nghiệm thu 5 tình "
        "nguyện viên đã hoàn chỉnh đầy đủ, 1 tình nguyện viên còn lại (`SPK_0001`, gồm `175` tệp qua 5 codecs) được đưa "
        "vào tập Train chính thức (`54.400` dòng so với tập đối chứng `54.225` dòng).",
        "3. Kho Tình Nguyện Viên Thực Tế & Bộ Nghiệm Thu Độc Lập 5 Người Nói",
    )

    add_heading_subsection(
        doc,
        "2.1.2 Phân Công Động Cơ TTS Trong v0.9.4: Seen TTS Đối Xứng 1:1 vs. Unseen TTS Kiểm Định H2",
    )
    add_styled_paragraph(
        doc,
        "Để mô hình vừa nắm bắt triệt để các biến thể tinh vi của kiến trúc Flow Matching hiện đại, vừa chứng minh được "
        "năng lực khái quát hóa sang họ kiến trúc rời rạc hoàn toàn khác biệt, phiên bản **`v0.9.4`** phân công rõ ràng:",
    )

    add_bullet_item(
        doc,
        "Kết hợp đối xứng hai động cơ nhân bản Zero-Shot thuộc trường phái *Diffusion / Continuous Flow Matching*:\n"
        "• **`F5-TTS-Vietnamese` (`6.170` tệp qua 5 codecs)**: Kiến trúc *Diffusion Transformer (DiT)* + bộ giải mã sóng "
        "âm `Vocos` @ `24kHz` (hạ mẫu đa pha về `16kHz`), chọn mẫu tham chiếu đơn dải vàng `3,5s – 7,5s` không ghép nối "
        "(`allow_stitching=False`).\n"
        "• **`VoiceStudio / OmniVoice CFM` (`6.445` tệp đối xứng 1:1 = `1.289` tệp sạch × `5` codecs)**: Động cơ "
        "*Continuous Flow Matching* thế hệ mới (`num_step=16`, `guidance_scale=2,0`), phân bổ đối xứng gồm **`4.795` tệp "
        "VIVOS** (`65` người nói), **`1.225` tệp Common Voice** (`25` người nói) và **`425` tệp Tình nguyện viên** (`50` "
        "tệp thuộc tập Train và `375` tệp thuộc Bộ nghiệm thu 5 người nói `SPK_0003..0007`). Văn bản đầu vào cho bộ gióng "
        "hàng `OmniVoice` được chuẩn hóa chữ hoa đầu câu và dấu chấm cuối câu (`normalize_tts_prompt`) để ngăn lỗi sụp đổ "
        "bộ gióng hàng (*Neural Aligner*).",
        "Nhóm Seen TTS (Tham gia huấn luyện Train & đánh giá nội bộ Dev / Test In-domain)",
    )
    add_bullet_item(
        doc,
        "Sử dụng động cơ **`VieNeu-TTS v3 Turbo`** (kiến trúc mô hình ngôn ngữ tự hồi quy `Qwen LLM` kết hợp bộ mã hóa âm "
        "học rời rạc `NeuCodec / MOSS 48kHz`, tắt khử nhiễu `denoise=False` và tắt thủy vân `apply_watermark=False`). "
        "Toàn bộ mẫu `VieNeu-TTS v3 Turbo` bị **cô lập 100% khỏi quá trình huấn luyện và chọn siêu tham số của `v0.9.4`**, "
        "tạo thành hai bài thi độc lập cho Giả thuyết H2: tập **`955` mẫu** OOD Dev (`unseen_vieneu_benchmark.csv`) và tập "
        "**`375` mẫu** trên 5 tình nguyện viên nghiệm thu (`SPK_0003..0007`).",
        "Nhóm Unseen TTS (Cô lập 100% phục vụ kiểm định Giả thuyết H2)",
    )
    add_bullet_item(
        doc,
        "Công cụ `Kokoro-Vietnamese` (`StyleTTS 2 + iSTFTNet`) bị **loại bỏ hoàn toàn khỏi bộ nghiệm thu chính thức** "
        "theo quy tắc bất biến của dự án. Lý do khoa học: `Kokoro-TTS` chỉ là *Preset Multi-Speaker TTS* (chỉ phát ra một "
        "vài giọng mẫu có sẵn), hoàn toàn **không hỗ trợ Zero-Shot Voice Cloning từ tệp ghi âm của nạn nhân**, nên không "
        "đại diện đúng cho mối đe dọa giả mạo danh tính người thân.",
        "Quyết định loại bỏ Kokoro-TTS khỏi tập nghiệm thu chính thức",
    )

    add_term_glossary(
        doc,
        [
            (
                "Zero-Shot Voice Cloning",
                "Nhân bản giọng nói không cần huấn luyện lại",
                "Kỹ thuật sao chép tức thì màu giọng, nhịp điệu của một người lạ chỉ dựa trên một đoạn âm thanh mẫu dài vài giây.",
            ),
            (
                "CFM",
                "Continuous Flow Matching",
                "Phương pháp sinh dữ liệu tiên tiến học trường vector vận tốc để biến đổi nhiễu Gauss thành phổ tiếng nói tự nhiên chỉ sau 16 bước tích phân.",
            ),
            (
                "Neural Codec TTS",
                "Tổng hợp tiếng nói qua mã rời rạc nơ-ron",
                "Kiến trúc biến sóng âm thành chuỗi mã nguyên rời rạc (giống từ vựng trong ChatGPT) rồi dùng mô hình ngôn ngữ sinh tiếp chuỗi âm thanh.",
            ),
            (
                "Neural Aligner",
                "Bộ gióng hàng văn bản - âm thanh nơ-ron",
                "Thành phần căn chỉnh từng âm tiết chữ viết khớp với từng khung thời gian của giọng mẫu tham chiếu trong các mô hình TTS.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 2.2 Rào chắn chống rò rỉ dữ liệu & Ghép cặp base_utt
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "2.2 Ba Rào Chắn Toán Học Chống Rò Rỉ Dữ Liệu Tuyệt Đối (0% Leakage) & Liên Kết Cặp base_utt",
    )

    add_styled_paragraph(
        doc,
        "Mọi tệp manifest trong `ViTrueVoice v0.9.4` bắt buộc vượt qua bài kiểm toán tự động bằng kịch bản kiểm thử đơn "
        "vị với **3 ràng buộc cô lập không khoan nhượng**:",
    )

    add_bullet_item(
        doc,
        "Tập hợp mã định danh người nói (`speaker_id`) giữa các phân vùng `Train`, `Dev`, `Test In-domain`, `Test OOD` và "
        "`Bộ nghiệm thu 5 SPK` giao nhau bằng rỗng tuyệt đối (`0` người nói trùng lặp). Mô hình không có bất kỳ cơ hội nào "
        "ghi nhớ âm sắc riêng của từng cá nhân để ăn gian điểm số.",
        "1. Hard Speaker-Disjoint (Cô lập 100% người nói giữa mọi phân vùng)",
    )
    add_bullet_item(
        doc,
        "Không một câu kịch bản văn bản nào được phép xuất hiện đồng thời ở hai phân vùng khác nhau. Quá trình khử trùng "
        "tuân thủ chiều ưu tiên bất biến: **Giữ nguyên 100% câu thoại của tập `Test` → Lọc bỏ mọi câu trùng khỏi tập `Dev` "
        "→ Lọc bỏ mọi câu trùng với cả `Test` và `Dev` khỏi tập `Train`**. Hơn thế nữa, ngay trong cùng một người nói "
        "(*Intra-Speaker Disjointness*), các câu đóng vai trò giọng mẫu tham chiếu (`role = ref`) và đăng ký vân giọng "
        "(`role = enroll`) cũng tách biệt hoàn toàn khỏi các câu dùng để chấm điểm (`role = eval`).",
        "2. Hard Text-Disjoint & Intra-Speaker Role Disjointness (Cô lập triệt để văn bản & vai trò)",
    )
    add_bullet_item(
        doc,
        "Mỗi phát ngôn sạch gốc (`clean_16khz`) được gán một khóa định danh gốc **`base_utt`** và sinh đồng bộ ra đúng 4 "
        "phiên bản nén kênh truyền (`aac_zalo_76k`, `opus_zalo_24k`, `g711_alaw`, `amr_nb`). Cả 5 biến thể mang cùng một "
        "`base_utt` bắt buộc nằm trọn trong cùng một phân vùng `split`. Thiết kế đối xứng 5 chiều này vừa chặn đứng rò rỉ "
        "chéo kênh nén, vừa cho phép tính chính xác độ sụt giảm điểm số trên cùng một câu nói khi đổi từ phòng thu sang "
        "Zalo hoặc GSM (*Paired Codec Delta*).",
        "3. Ghép Cặp Đồng Bộ Đa Kênh Nén Qua Khóa Liên Kết base_utt",
    )

    add_term_glossary(
        doc,
        [
            (
                "Speaker-Disjoint",
                "Phân chia tách rời người nói",
                "Nguyên tắc đảm bảo người nói đã xuất hiện trong tập huấn luyện thì không bao giờ xuất hiện lại trong tập thẩm định hay kiểm thử.",
            ),
            (
                "Hard Text-Disjoint",
                "Phân chia tách rời cứng nội dung văn bản",
                "Nguyên tắc cấm trùng lặp câu chữ kịch bản giữa các tập Train, Dev, Test nhằm ngăn mạng nơ-ron học vẹt từ vựng.",
            ),
            (
                "base_utt",
                "Base Utterance Identifier",
                "Mã gốc kết nối 5 biến thể kênh truyền (Clean, AAC, Opus, G.711, AMR-NB) của cùng một bản thu âm hoặc bản nhân bản.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 2.3 Bộ lọc 4 cổng tự động & Chuẩn hóa văn bản tách rời
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "2.3 Bộ Lọc Kiểm Định Chất Lượng Mẫu Giả 4 Cổng & Ranh Giới Chuẩn Hóa Văn Bản",
    )

    add_foundation_primer(
        doc,
        process_name="Kiểm định chất lượng tự động 4 cổng cho mẫu giọng giả tổng hợp (Multi-Gate Quality Filter)",
        why_needed=(
            "Các mô hình TTS Zero-Shot đôi khi sinh ra tệp bị nói lắp, nuốt chữ, lạc mất giọng nạn nhân hoặc câm lặng. "
            "Nếu đưa các tệp lỗi thô thiển này vào tập dữ liệu, mô hình chống giả mạo sẽ trở nên 'lười biếng' — chỉ cần "
            "bắt lỗi nói ngọng thay vì học dấu vết tinh vi của những bản Deepfake hoàn hảo nhất!"
        ),
        real_analogy=(
            "Giống như xưởng đúc tiền thử nghiệm nhằm huấn luyện máy soi tiền giả của ngân hàng: trước khi đem đồng tiền "
            "giả đưa vào bài kiểm tra cho máy soi, bản thân tờ tiền giả đó phải vượt qua 4 vòng KCS (in rõ chữ không nhòe, "
            "màu sắc giống tiền thật, đúng kích thước chuẩn, độ dày giấy đồng đều). Tờ nào in hỏng bị hủy và in lại ngay!"
        ),
        core_points=[
            "Bảng mã tiếng Việt Unicode có hai cách biểu diễn ký tự có dấu: dựng sẵn NFC (1 mã duy nhất cho chữ 'à') và tổ hợp NFD (chữ 'a' ghép với dấu huyền rời). Nếu không đưa về NFC, máy tính sẽ tưởng hai chữ 'hòa' giống hệt nhau trên màn hình là hai từ khác nhau!",
            "Khoảng cách chỉnh sửa Levenshtein đếm số thao tác Thay thế (S), Xóa bỏ (D) và Chèn thêm (I) ít nhất để biến câu chép lời của AI thành câu gốc ban đầu.",
            "Độ tương đồng góc Cosine đo góc lệch giữa hai vector vân giọng trong không gian 192 chiều: bằng 1,0 khi hai vector trùng hướng hoàn toàn, bằng 0 khi vuông góc không liên quan.",
        ],
    )

    add_styled_paragraph(
        doc,
        "**Ranh giới sắt trong chuẩn hóa văn bản tiếng Việt (`normalize_for_eval` vs. Raw TTS Prompt)**: Dự án xây dựng hàm "
        "`normalize_for_eval(text)` thực hiện 3 thao tác: (1) Đưa chuỗi về dạng dựng sẵn chuẩn **Unicode `NFC`**; (2) Chuẩn "
        "hóa vị trí đặt dấu thanh chỉ ở âm tiết mở cuối từ qua hàm `_fix_tone_token` (chuyển `hoà → hòa`, `thuỷ → thủy`, "
        "`khoẻ → khỏe` nhưng **bảo toàn tuyệt đối** các vần có phụ âm cuối hoặc âm đệm như `toàn`, `hoàng`, `thuở`, `quý` — "
        "không bao giờ gây lỗi biến dạng thành *'tòan'*); (3) Loại bỏ dấu câu và câu chứa chữ số (`has_digits`). **Quy tắc "
        "bất biến**: Chuỗi đã qua `normalize_for_eval` **CHỈ** được dùng để tính `WER/CER` ở Cổng 1 và lọc trùng văn bản; "
        "còn **prompt đưa vào bộ sinh TTS bắt buộc giữ nguyên dấu phẩy, dấu chấm câu tự nhiên** để bảo toàn nhịp nghỉ ngữ "
        "âm chân thực!",
    )

    add_styled_paragraph(
        doc,
        "Mọi mẫu giả mạo sau khi tổng hợp phải vượt qua tuần tự **4 Cổng kiểm định tự động** (nếu trượt bất kỳ cổng nào, "
        "pipeline tự động đổi hạt giống ngẫu nhiên `seed ∈ {42, 200, 300}` để tổng hợp lại):",
    )

    add_bullet_item(
        doc,
        "Đưa âm thanh tổng hợp qua mô hình nhận dạng tiếng Việt `wav2vec2-base-vietnamese-250h` để thu văn bản chép lời, "
        "chuẩn hóa `normalize_for_eval` và đối chiếu với kịch bản gốc. Mẫu chỉ đạt khi đồng thời thỏa mãn **Tỷ lệ lỗi từ "
        "`WER ≤ 15%`** và **Tỷ lệ lỗi ký tự `CER ≤ 8%`**, loại bỏ hoàn toàn hiện tượng đọc ngọng, lặp từ hoặc đứt câu.",
        "Cổng 1 — Kiểm định độ rõ nội dung phát âm (ASR Intelligibility Gate)",
    )

    wer_eq = (
        omml_r("WER", normal=True)
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("S"), omml_r("w"))
            + omml_r(" + ", normal=True)
            + omml_sub(omml_r("D"), omml_r("w"))
            + omml_r(" + ", normal=True)
            + omml_sub(omml_r("I"), omml_r("w")),
            omml_sub(omml_r("N"), omml_r("w")),
        )
        + omml_r("   ;   ", normal=True)
        + omml_r("CER", normal=True)
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("S"), omml_r("c"))
            + omml_r(" + ", normal=True)
            + omml_sub(omml_r("D"), omml_r("c"))
            + omml_r(" + ", normal=True)
            + omml_sub(omml_r("I"), omml_r("c")),
            omml_sub(omml_r("N"), omml_r("c")),
        )
    )
    add_omml_equation(
        doc,
        "Tỷ lệ lỗi từ WER và Tỷ lệ lỗi ký tự CER dựa trên khoảng cách Levenshtein (Cổng lọc số 1)",
        wer_eq,
        variables=[
            ("S_w , D_w , I_w", "Số lượng từ bị Thay thế sai (Substitutions), bị Bỏ sót/nuốt từ (Deletions) và bị Chèn dư (Insertions) khi ASR nghe lại mẫu giả."),
            ("N_w", "Tổng số từ chuẩn trong câu kịch bản gốc sau khi chuẩn hóa normalize_for_eval."),
            ("S_c , D_c , I_c , N_c", "Các đại lượng tương ứng tính ở cấp độ từng ký tự tiếng Việt (nhạy với cả lỗi sai dấu thanh điệu)."),
        ],
    )

    add_bullet_item(
        doc,
        "Dùng mạng sinh trắc học `spkrec-ecapa-voxceleb` trích xuất vector vân giọng 192 chiều của mẫu giả `e_syn` và so "
        "khớp với vector tâm cụm đăng ký `e_ref` (trung bình chuẩn hóa bậc hai của `K = 4` tệp `enroll` độc lập của nạn "
        "nhân). Mẫu sinh ra phải vượt ngưỡng tương đồng thích ứng `T_spk` (sàn tối thiểu `≥ 0,4905` theo ước lượng co rút "
        "phương sai, trung bình thực tế đạt `0,71 – 0,80`), đảm bảo giọng giả thực sự mang âm sắc của nạn nhân.",
        "Cổng 2 — Kiểm định độ giống vân giọng sinh trắc (ECAPA-TDNN Speaker Similarity Gate)",
    )

    cos_eq = (
        omml_r("cos", normal=True)
        + omml_delim(
            omml_sub(omml_r("e", bold=True), omml_r("ref", normal=True))
            + omml_r(" , ", normal=True)
            + omml_sub(omml_r("e", bold=True), omml_r("syn", normal=True))
        )
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("e", bold=True), omml_r("ref", normal=True))
            + omml_r(" · ", normal=True)
            + omml_sub(omml_r("e", bold=True), omml_r("syn", normal=True)),
            omml_sub(
                omml_delim(omml_sub(omml_r("e", bold=True), omml_r("ref", normal=True)), beg="‖", end="‖"),
                omml_r("2", normal=True),
            )
            + omml_r(" · ", normal=True)
            + omml_sub(
                omml_delim(omml_sub(omml_r("e", bold=True), omml_r("syn", normal=True)), beg="‖", end="‖"),
                omml_r("2", normal=True),
            ),
        )
    )
    add_omml_equation(
        doc,
        "Độ tương đồng vân giọng Cosine trong không gian nhúng 192 chiều (Cổng lọc số 2)",
        cos_eq,
        variables=[
            ("e_ref", "Vector tâm cụm vân giọng chuẩn (192 chiều) tính từ 4 tệp giọng thật độc lập thuộc nhóm enroll của người nói mục tiêu."),
            ("e_syn", "Vector nhúng vân giọng (192 chiều) trích xuất từ tệp âm thanh giả mạo vừa được động cơ TTS tổng hợp."),
            ("e_ref · e_syn", "Tích vô hướng giữa hai vector đặc trưng vân giọng."),
            ("‖e‖₂", "Chuẩn Euclid bậc hai (độ dài hình học của vector), chuẩn hóa kết quả về đoạn [-1, +1]."),
        ],
    )

    add_bullet_item(
        doc,
        "Kiểm tra nghiêm ngặt tính toàn vẹn số học: không chứa `NaN` hoặc `Inf`, năng lượng hiệu dụng **`RMS ≥ 0,01`** "
        "(chặn đứng các tệp câm lặng hoặc sụp đổ biên độ), thời lượng hợp lệ **`≥ 1,0 giây`** và biên độ đỉnh **`Peak ≤ "
        "0,999`** nhờ chuẩn hóa trần `Headroom ≤ 0,95` (ngăn hiện tượng xén đỉnh gây rè vỡ tiếng).",
        "Cổng 3 — Kiểm định toàn vẹn tín hiệu & Chống khoảng lặng chết (Signal Sanity & Anti-Silence Gate)",
    )
    add_bullet_item(
        doc,
        "Trích xuất đường cong tần số cơ bản `F0` bằng thuật toán `YIN` trên dải giọng nói `[65 Hz, 400 Hz]`. Yêu cầu độ "
        "lệch cao độ tương đối `≤ 0,30`, độ chênh hệ số biến thiên `|ΔCV_F0| ≤ 0,12`, bước nhảy đột biến `≤ 0,18` và điểm "
        "tự nhiên tổng hợp **`≥ 0,65`** nhằm loại bỏ các câu tổng hợp phẳng lì vô cảm hoặc gãy thanh điệu tiếng Việt. "
        "Ngoài ra, toàn bộ tập dữ liệu còn được kiểm toán bằng bộ phân loại Logistic nông (`detect_shortcuts.py`) trên 2 "
        "đặc trưng bề mặt (năng lượng `> 7 kHz` và tỷ lệ khoảng lặng), đảm bảo `ROC-AUC ≤ 0,65` không tồn tại đường tắt.",
        "Cổng 4 — Kiểm định ngữ điệu thuần âm học không nhãn (Label-Free Prosody YIN F0 Gate) & Kiểm toán Shortcut",
    )

    add_term_glossary(
        doc,
        [
            (
                "NFC",
                "Normalization Form Canonical Composition",
                "Chuẩn mã hóa Unicode dựng sẵn giúp hợp nhất ký tự gốc và dấu thanh tiếng Việt thành một điểm mã duy nhất nhất quán.",
            ),
            (
                "WER & CER",
                "Word Error Rate & Character Error Rate",
                "Tỷ lệ lỗi cấp độ từ và cấp độ ký tự khi nhận dạng tiếng nói; càng thấp chứng tỏ mẫu âm thanh tổng hợp phát âm càng tròn vành rõ chữ.",
            ),
            (
                "ECAPA-TDNN",
                "Emphasized Channel Attention, Propagation and Aggregation TDNN",
                "Kiến trúc mạng nơ-ron chuẩn mực dùng để trích xuất vector vân giọng sinh trắc học 192 chiều.",
            ),
            (
                "YIN F0",
                "Thuật toán ước lượng tần số cơ bản YIN",
                "Thuật toán tự tương quan sai phân đo chính xác cao độ giọng nói (Hz) theo từng khung thời gian ngắn.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 2.4 Bảng 5 Manifests 19 cột & Kho lưu trữ Voice_Final (103.189 tệp)
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "2.4 Hệ Thống 5 Tệp Manifest Chính Thức Chuẩn 19 Cột & Kho Lưu Trữ Voice_Final (103.189 Tệp)",
    )

    add_styled_paragraph(
        doc,
        "Kế thừa khung siêu dữ liệu 18 cột ban đầu và bổ sung cột thứ 19 **`base_utt`** để khóa liên kết đối xứng qua 5 "
        "kênh truyền, toàn bộ vòng đời huấn luyện và đánh giá của **`ViTrueVoice v0.9.4`** được quản lý minh bạch qua **5 "
        "tệp Manifest chuẩn 19 cột** (`utt_id`, `audio_path`, `speaker_id`, `source`, `label`, `role`, `tts_generator`, "
        "`codec`, `pre_codec`, `split`, `duration_sec`, `transcript`, `raw_wer`, `raw_cer`, `ecapa_sim`, `wavlm_sim`, "
        "`derived_tier`, `seed`, `base_utt`):",
    )

    add_styled_table(
        doc,
        headers=[
            "Tên Tệp Manifest Chính Thức",
            "Quy Mô (Số Dòng)",
            "Thành Phần Nguồn & TTS",
            "Vai Trò Khoa Học Trong ViTrueVoice v0.9.4",
        ],
        rows=[
            (
                "train_v8_f5_omni_with_spk1.csv",
                "54.400 dòng",
                "Bonafide (VIVOS Train, CV Train, SPK_0001) + Seen Spoof đối xứng (F5-TTS & OmniVoice CFM) × 5 codecs",
                "Tập huấn luyện chính thức tạo ra mô hình phát hành v0.9.4 (cô lập 100% 5 SPK nghiệm thu & VieNeu-TTS).",
            ),
            (
                "train_v8_f5_omni_no_spk1.csv",
                "54.225 dòng",
                "Giống tập Train chính thức nhưng tách riêng 175 dòng của tình nguyện viên thứ 6 (SPK_0001)",
                "Tập huấn luyện đối chứng khoa học (Control Split) phục vụ phân tích tác động phân bố âm vực.",
            ),
            (
                "dev_v8_f5_omni.csv",
                "12.405 dòng",
                "Bonafide (VIVOS Dev, CV Dev) + Seen Spoof (F5-TTS & OmniVoice CFM) × 5 codecs",
                "Tập thẩm định độc lập dùng để theo dõi hội tụ, dừng sớm (Early Stopping) và kiểm tra hiệu chuẩn.",
            ),
            (
                "test_indomain_v8_f5_omni.csv",
                "15.980 dòng (15.665 eval)",
                "15 người nói VIVOS Held-out + Seen Spoof (F5-TTS & OmniVoice CFM) × 5 codecs",
                "Tập kiểm thử quy mô lớn đo KPI Giả thuyết H1 & In-domain EER (v0.9.4 đạt 5,63% EER, chặn 95,01%).",
            ),
            (
                "unseen_vieneu_benchmark.csv",
                "955 dòng",
                "100% mẫu giả VieNeu-TTS v3 Turbo chưa từng thấy khi học × 5 codecs",
                "Tập chuẩn khóa cứng kiểm định Giả thuyết H2 ngoài phân phối (v0.9.4 đạt 12,05% EER ≤ 15,0%).",
            ),
        ],
        col_widths=[1.85, 1.00, 1.85, 2.00],
        highlight_row_pred=lambda idx, _: idx in (0, 3, 4),
    )

    add_styled_paragraph(
        doc,
        "Song song với hệ thống Manifest huấn luyện, toàn bộ tài sản âm thanh phục vụ bàn giao và hậu kiểm độc lập của Hội "
        "đồng được đóng gói đối xứng 1:1 trong kho lưu trữ bất biến **`Voice_Final`** với tổng cộng **`103.189` tệp âm "
        "thanh** được kiểm toán mã băm mật mã học **`SHA-256`** khớp 100% với `VOICE_FINAL_MANIFEST.csv`:",
    )

    add_styled_table(
        doc,
        headers=[
            "Phân Nhánh Trong Kho Voice_Final",
            "Số Lượng Tệp",
            "Nội Dung Lưu Trữ & Ý Nghĩa Đối Chứng",
        ],
        rows=[
            (
                "bonafide/",
                "70.174 tệp",
                "Toàn bộ tệp giọng người thật gốc và các bản sao suy giảm qua kênh truyền của VIVOS, Common Voice 8.0 và nhóm tình nguyện viên.",
            ),
            (
                "spoof/v7/",
                "13.955 tệp",
                "Nhánh mẫu giả thế hệ đối chứng lịch sử (tổ hợp F5-TTS + VieNeu-TTS v3 Turbo) giữ lại để tái lập thí nghiệm hoán đổi hai chiều.",
            ),
            (
                "spoof/v8/",
                "19.060 tệp",
                "Nhánh mẫu giả đối xứng chính thức của v0.9.4 (bao gồm trọn vẹn 6.445 tệp OmniVoice CFM 1:1 cùng F5-TTS và tập kiểm định Unseen).",
            ),
            (
                "TỔNG CỘNG TOÀN KHO VOICE_FINAL",
                "103.189 tệp",
                "100% đường dẫn chuẩn POSIX và khớp tuyệt đối chữ ký băm SHA-256 chống sửa đổi dữ liệu nghiệm thu.",
            ),
        ],
        col_widths=[1.85, 1.15, 3.70],
        highlight_row_pred=lambda idx, _: idx == 3,
    )

    if figs and "fig2" in figs:
        add_figure(
            doc,
            figs["fig2"],
            "Hình 2.1: Sơ đồ kiến trúc dữ liệu đối xứng và luồng chống rò rỉ của ViTrueVoice v0.9.4. "
            "Ba nguồn giọng thật đi qua màng lọc cô lập cứng (Speaker-Disjoint, Hard Text-Disjoint, cô lập 100% 5 tình nguyện "
            "viên nghiệm thu SPK_0003..0007), phân tách rạch ròi giữa 2 động cơ Seen TTS (F5-TTS 6.170 tệp & OmniVoice CFM "
            "6.445 tệp đối xứng) và động cơ Unseen TTS kiểm định H2 (VieNeu-TTS v3 Turbo), vượt qua bộ lọc 4 cổng và 5 cấu "
            "hình nén để kết xuất thành 5 tệp Manifest 19 cột cùng kho lưu trữ Voice_Final 103.189 tệp.",
        )

    add_term_glossary(
        doc,
        [
            (
                "Manifest CSV (19 cột)",
                "Bảng kê siêu dữ liệu huấn luyện & kiểm thử",
                "Tệp bảng tính chuẩn hóa lưu trữ đường dẫn, nhãn, người nói, công cụ TTS, codec, chỉ số 4 cổng lọc và khóa base_utt của từng mẫu âm thanh.",
            ),
            (
                "pre_codec",
                "Trạng thái nén nguồn ban đầu",
                "Cột ghi nhận định dạng nén vốn có của tệp gốc trước khi đưa vào pipeline (ví dụ mp3 của Common Voice so với pcm sạch của VIVOS).",
            ),
            (
                "SHA-256",
                "Secure Hash Algorithm 256-bit",
                "Hàm băm mật mã một chiều biến nội dung tệp âm thanh thành chuỗi 64 ký tự thập lục phân duy nhất để kiểm tra toàn vẹn và ẩn danh hóa nhật ký.",
            ),
        ],
    )

    # =========================================================================
    # CHƯƠNG 3: TIỀN XỬ LÝ TÍN HIỆU SỐ (DSP), REPEAT PADDING, 5 CODECS & RAWBOOST
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 3",
        "Tiền Xử Lý Tín Hiệu Số (DSP), Repeat Padding, 5 Kênh Codec & Mô Phỏng Nhiễu RawBoost",
    )

    add_styled_paragraph(
        doc,
        "Trước khi bất kỳ mạng nơ-ron học sâu nào có thể phát huy sức mạnh, tín hiệu âm thanh thô phải đi qua chuỗi "
        "**Tiền xử lý tín hiệu số (*Digital Signal Processing — DSP*)** tại gói `src/preprocessing/`. Chương 3 giải mã "
        "từng mắt xích vật lý và toán học giúp `ViTrueVoice v0.9.4` chuẩn hóa mọi định dạng hỗn tạp về tensor chuẩn "
        "`(1, 64000)` trực tiếp trên RAM, triệt tiêu hoàn toàn các đường tắt âm học và mô phỏng chính xác 5 kênh nén thực "
        "tế cùng nhiễu `RawBoost`.",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 3.1 Magic-bytes RAM decoding & Polyphase Resampling 16kHz
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "3.1 Giải Mã Đa Định Dạng Theo Magic Bytes Trên RAM & Tái Lấy Mẫu Đa Pha 16.000 Hz Mono",
    )

    add_foundation_primer(
        doc,
        process_name="Chuỗi tiền xử lý tín hiệu số (DSP) chuẩn hóa sóng âm đầu vào",
        why_needed=(
            "Ngoài đời thực, người dùng có thể tải lên tệp ghi âm iPhone (.m4a 48kHz), tin nhắn thoại Zalo (.ogg 24kbps), "
            "tệp tổng đài (.wav 8kHz), hoặc thu trực tiếp qua micro trình duyệt. Nếu đưa thẳng dữ liệu lệch tần số, lệch "
            "độ to và lệch độ dài vào mô hình, mạng nơ-ron sẽ học vẹt đặc điểm kỹ thuật của tệp tin thay vì phân biệt giọng thật/giả!"
        ),
        real_analogy=(
            "Hãy hình dung quy trình chụp ảnh làm căn cước công dân gắn chip: dù công dân cao hay thấp, mặc áo sáng hay tối, "
            "trước khi đưa vào thuật toán nhận diện sinh trắc học, tất cả đều phải ngồi trước phông nền đồng nhất, cân bằng "
            "sáng chuẩn (tương đương EBU R128 −23 LUFS & Z-score), cắt gọn khung hình đúng tỷ lệ chuẩn (64.000 mẫu = 4,0 giây) "
            "ở cùng một độ phân giải cảm biến (16.000 Hz Mono) — tuyệt đối không chèn viền đen cắt ghép (Zero-Padding)!"
        ),
        core_points=[
            "Tần số lấy mẫu 16.000 Hz & Định lý Nyquist–Shannon: Lấy mẫu 16.000 điểm biên độ mỗi giây cho phép thu trọn mọi tần số âm thanh từ 0 Hz đến đúng một nửa tần số lấy mẫu (f_Nyquist = 8.000 Hz), bao phủ toàn bộ tần số cơ bản F0, các đỉnh cộng hưởng nguyên âm Formants (F1–F4) và phụ âm xát tiếng Việt.",
            "Waveform (Miền thời gian) vs. Spectrogram (Miền thời gian - tần số): Waveform là chuỗi số 1 chiều biểu diễn độ rung màng loa theo thời gian; Spectrogram là ảnh nhiệt 2 chiều (tạo bởi phép biến đổi Fourier thời gian ngắn STFT) cho thấy năng lượng phân bố ở từng dải Hz theo từng mili-giây.",
            "Độ to cảm nhận LUFS vs. Biên độ đỉnh Peak: Một tiếng gõ micro thoáng qua có thể đẩy Peak chạm đỉnh 1,0 nhưng cả câu nói vẫn nhỏ lí nhí; chuẩn LUFS đo năng lượng tích hợp theo độ nhạy thính giác con người.",
            "Cạm bẫy vách không (Zero-Wall Shortcut): Nếu một tệp ngắn 2,5 giây được bù thêm 1,5 giây toàn số 0 tuyệt đối cho đủ 4,0 giây, mạng nơ-ron sẽ gian lận bằng cách đo độ dài đoạn số 0 hoặc bắt nhiễu xung giả tại điểm đứt gãy rơi thẳng về 0!",
        ],
    )

    add_styled_paragraph(
        doc,
        "Mắt xích đầu tiên của hệ thống là bộ nạp âm thanh đa định dạng **`src/preprocessing/audio_loader.py`**, được thiết "
        "kế tuân thủ hai nguyên tắc bất biến của dự án:",
    )

    add_bullet_item(
        doc,
        "Người dùng hoặc các ứng dụng nhắn tin thường xuyên đổi tên phần mở rộng tệp một cách tùy tiện (ví dụ tệp nén "
        "`.m4a` của iOS hoặc `.ogg` của Zalo bị đổi tên đuôi thành `.wav`). Nếu gọi hàm đọc WAV thông thường theo đuôi tệp, "
        "hệ thống sẽ báo lỗi hỏng định dạng ngay lập tức. Do đó, `load_audio` đọc trực tiếp **các byte chữ ký đầu tiên "
        "(*Magic Bytes*)** trong luồng nhị phân: `RIFF....WAVE` (WAV), `OggS` (OGG/Opus), `fLaC` (FLAC), `ID3` hoặc byte "
        "đồng bộ khung `0xFF 0xFB` (MP3), hộp `ftyp` tại vị trí byte thứ 4 (M4A/AAC/MP4) và `#!AMR` (AMR-NB).",
        "1. Nhận diện định dạng bằng chữ ký nhị phân Magic Bytes (Tuyệt đối không tin đuôi tệp)",
    )
    add_bullet_item(
        doc,
        "Với định dạng không nén chuẩn (WAV, FLAC, OGG), dữ liệu đọc thẳng qua vùng đệm `io.BytesIO`. Với các định dạng "
        "nén phức tạp (M4A, AAC, MP3, AMR, WebM), hệ thống truyền luồng byte trực tiếp qua đường ống bộ nhớ RAM của FFmpeg "
        "(`pipe:0 → pipe:1` xuất chuẩn `pcm_s16le` 1 kênh Mono `16.000 Hz`). **Không một tệp âm thanh tạm nào được ghi "
        "xuống ổ cứng**, bảo vệ tuyệt đối dữ liệu giọng nói sinh trắc học theo Luật 91/2025/QH15.",
        "2. Giải mã luồng trực tiếp 100% trên bộ nhớ RAM (In-Memory FFmpeg Pipe)",
    )
    add_bullet_item(
        doc,
        "Khi hạ tần số lấy mẫu từ `48.000 Hz` hoặc `44.100 Hz` về `16.000 Hz`, nếu chỉ lấy mẫu thưa đơn giản, các thành "
        "phần tần số cao trên `8.000 Hz` sẽ bị gập ngược vào vùng tần số thấp gây méo tiếng nghiêm trọng (*Aliasing*). "
        "Hệ thống sử dụng **bộ lọc thông thấp đa pha (*Polyphase Anti-Aliasing Filter* với cửa sổ Kaiser / `soxr_vhq`)** "
        "để cắt sạch mọi năng lượng trên ngưỡng Nyquist `8.000 Hz` trước khi nội suy về đúng `16.000 Hz` Mono.",
        "3. Gộp kênh đơn Mono & Tái lấy mẫu đa pha chống chồng phổ (Polyphase Resampling)",
    )

    add_term_glossary(
        doc,
        [
            (
                "DSP",
                "Digital Signal Processing",
                "Xử lý tín hiệu số: tập hợp các phép toán biến đổi, lọc nhiễu và chuẩn hóa sóng âm rời rạc trong máy tính.",
            ),
            (
                "Hz / kHz & Định lý Nyquist",
                "Hertz / Kilohertz & Nyquist–Shannon Theorem",
                "Số mẫu thu được trong 1 giây (16kHz = 16.000 mẫu/giây); tần số âm thanh cao nhất biểu diễn được bằng đúng một nửa tần số lấy mẫu (8kHz).",
            ),
            (
                "Aliasing",
                "Hiện tượng chồng phổ (Gập tần số ma)",
                "Sự biến dạng xảy ra khi hạ tần số lấy mẫu mà không lọc bỏ trước các tần số cao vượt quá ngưỡng Nyquist.",
            ),
            (
                "Polyphase Resampling",
                "Tái lấy mẫu đa pha",
                "Kỹ thuật đổi tần số lấy mẫu tích hợp bộ lọc thông thấp độ dốc cao giúp bảo toàn nguyên vẹn pha và biên độ trong dải thông 0–8kHz.",
            ),
            (
                "Magic Bytes",
                "Chữ ký nhị phân đầu tệp (File Signature)",
                "Chuỗi byte định danh cố định nằm ở ngay đầu luồng dữ liệu cho biết bản chất thật sự của định dạng âm thanh bất kể tên tệp là gì.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 3.2 RMS P20 Trimming, WebRTC Conditioning & Repeat Padding 64k
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "3.2 Cắt Khoảng Lặng Thích Ứng RMS P20, Điều Hòa Micro WebRTC & Repeat Padding 64.000 Mẫu",
    )

    add_heading_subsection(
        doc,
        "3.2.1 Cắt Khoảng Lặng Đầu/Cuối Thích Ứng Theo Phân Vị Năng Lượng Thứ 20 (RMS P20 Trimming)",
    )
    add_styled_paragraph(
        doc,
        "Bản ghi âm của người thật luôn có khoảng trễ im lặng lúc đưa tay bấm nút thu và bấm nút dừng, trong khi tệp xuất "
        "ra từ nhiều công cụ TTS lại phát tiếng nói ngay lập tức ở mẫu đầu tiên. Để xóa bỏ sự khác biệt bề mặt này mà "
        "không cắt lẹm vào các phụ âm đầu câu khi thu trong môi trường ồn, hệ thống chia tín hiệu thành các khung trượt "
        "(`K = 512` mẫu ≈ `32 ms`, bước nhảy `H = 160` mẫu = `10 ms`), tính **năng lượng hiệu dụng `RMS`** của từng khung "
        "và lấy **phân vị thứ 20 (`P20`)** của chính tệp đó làm ngưỡng cắt khoảng lặng hai đầu:",
    )

    rms_eq = (
        omml_r("RMS", normal=True)
        + omml_delim(omml_r("m"))
        + omml_r(" = ", normal=True)
        + omml_sqrt(
            omml_frac(omml_r("1", normal=True), omml_r("K"))
            + omml_r(" ", normal=True)
            + omml_subsup(
                omml_r("∑", normal=True),
                omml_r("k=0", normal=True),
                omml_r("K−1", normal=True),
            )
            + omml_sup(
                omml_r("x")
                + omml_delim(
                    omml_r("m · H + k"),
                    beg="[",
                    end="]",
                ),
                omml_r("2", normal=True),
            )
        )
    )
    add_omml_equation(
        doc,
        "Năng lượng hiệu dụng khung thời gian ngắn RMS(m) phục vụ cắt khoảng lặng thích ứng P20",
        rms_eq,
        variables=[
            ("m", "Chỉ số thứ tự của khung thời gian đang xét dọc theo đoạn ghi âm."),
            ("K = 512", "Độ dài mỗi khung phân tích (tương đương 32 mili-giây ở tần số 16.000 Hz)."),
            ("H = 160", "Bước nhảy trượt giữa hai khung liên tiếp (tương đương 10 mili-giây)."),
            ("x[m · H + k]", "Giá trị biên độ mẫu sóng âm tại vị trí tương ứng; các khung rìa đầu/cuối có RMS(m) ≤ P₂₀(RMS) sẽ được cắt gọn."),
        ],
    )

    add_heading_subsection(
        doc,
        "3.2.2 Điều Hòa Luồng Thu Âm Trực Tiếp Từ Micro Trình Duyệt (WebRTC Browser Mic Conditioning)",
    )
    add_styled_paragraph(
        doc,
        "Khi người dùng thu âm trực tiếp trên giao diện Web (`48.000 Hz`), bộ xử lý tín hiệu mặc định của trình duyệt "
        "(`WebRTC`) tự động bật 3 bộ lọc phần mềm: khử ồn (`noiseSuppression`), khử vọng (`echoCancellation`) và tự động "
        "kích biên (`autoGainControl`). Các bộ lọc này gây ra hiện tượng **cổng ngắt đột ngột (*Squelch Gating*)**: cứ mỗi "
        "khi người nói nghỉ lấy hơi `0,1 giây` giữa hai từ, trình duyệt ép biên độ đoạn nghỉ đó về con số `0,000000` phẳng "
        "lì phi tự nhiên, làm mạng đồ thị `AASIST` lầm tưởng là vết cắt ghép nhân tạo. `ViTrueVoice v0.9.4` giải quyết triệt "
        "để từ hai đầu: (1) Tắt hoàn toàn cả 3 cờ `noiseSuppression = false`, `echoCancellation = false`, "
        "`autoGainControl = false` ngay khi gọi micro trình duyệt; (2) Điều hòa luồng thu qua hàm cắt khoảng lặng rìa "
        "(`top_db = 25`) và chuẩn hóa biên độ đỉnh đạt **`95%`** (`−0,45 dBFS`) trước khi đưa vào chuỗi suy luận.",
    )

    add_heading_subsection(
        doc,
        "3.2.3 Repeat Padding (np.tile) Đủ Chính Xác 64.000 Mẫu (4,0 Giây) vs. Lệnh Cấm Zero-Padding",
    )
    add_styled_paragraph(
        doc,
        "Kiến trúc `Wav2Vec 2.0` + `Compact AASIST` đòi hỏi mỗi cửa sổ đầu vào phải có kích thước cố định chính xác "
        "**`64.000` mẫu** (`4,0 giây × 16.000 Hz`). Với các câu thoại ngắn hơn 4 giây (có độ dài `L < 64.000` mẫu), dự án "
        "khóa cứng quy tắc bất biến (**`STUBBORN_FACT`**): **Bắt buộc dùng kỹ thuật nối lặp tuần hoàn `Repeat Padding` "
        "(`np.tile`), nghiêm cấm tuyệt đối kỹ thuật đệm số không `Zero-Padding`** vì hai lý do vật lý cốt tử:",
    )

    add_bullet_item(
        doc,
        "Nếu đang dao động sóng âm bình thường ở mẫu `L − 1` mà bị ép rơi thẳng đứng về `0` từ mẫu `L` đến `63.999`, tại "
        "điểm nối xuất hiện một **bước nhảy bậc thang gián đoạn (*Heaviside Step Discontinuity*)**. Theo nguyên lý biến đổi "
        "Fourier, một vách đứng đột ngột trong miền thời gian sẽ phát tán năng lượng nhiễu giả trải rộng khắp mọi dải tần "
        "số (*Broadband Spectral Click / Hiện tượng Gibbs*), làm sai lệch nghiêm trọng ma trận chú ý của đồ thị tần số.",
        "Tác hại 1 của Zero-Padding — Sinh xung nhiễu phổ giả dải rộng tại vách đứt gãy",
    )
    add_bullet_item(
        doc,
        "Đệm số `0` tạo ra cả một mảng phẳng chết có phương sai bằng `0` kéo dài ở nửa sau tensor, vừa làm lệch phép tính "
        "trung bình/độ lệch chuẩn của bước `Z-Score`, vừa tạo khe hở cho mạng nơ-ron học vẹt tỷ lệ thời lượng câu nói. "
        "Ngược lại, **`Repeat Padding`** quay vòng nối tiếp chính câu nói đó theo phép chia lấy dư modulo, bảo toàn 100% "
        "mật độ phổ, cấu trúc formant và nhịp thanh điệu xuyên suốt 4,0 giây!",
        "Tác hại 2 của Zero-Padding & Ưu thế tuyệt đối của Repeat Padding",
    )

    reppad_eq = (
        omml_sub(omml_r("x"), omml_r("pad", normal=True))
        + omml_delim(omml_r("n"), beg="[", end="]")
        + omml_r(" = ", normal=True)
        + omml_r("x")
        + omml_delim(
            omml_r("n") + omml_r(" mod ", normal=True) + omml_r("L"),
            beg="[",
            end="]",
        )
        + omml_r("   ,   0 ≤ n < 64.000", normal=True)
    )
    add_omml_equation(
        doc,
        "Ánh xạ chỉ số tuần hoàn của kỹ thuật Repeat Padding (np.tile)",
        reppad_eq,
        variables=[
            ("x_pad[n]", "Giá trị mẫu thứ n của tensor đầu vào cố định 64.000 mẫu (tương ứng đúng 4,0 giây @ 16kHz)."),
            ("x[...]", "Đoạn sóng âm gốc có độ dài thực tế L mẫu sau khi đã cắt khoảng lặng (với 0 < L < 64.000)."),
            ("n mod L", "Phép chia lấy phần dư của chỉ số n cho độ dài L (ví dụ nếu L = 40.000 mẫu = 2,5s thì mẫu thứ 40.000 sẽ nối lặp lại từ x[0])."),
        ],
    )

    add_term_glossary(
        doc,
        [
            (
                "RMS & P20",
                "Root Mean Square & 20th Percentile",
                "Năng lượng hiệu dụng trung bình bình phương của khung âm thanh và mức ngưỡng phân vị thứ 20 tự thích nghi theo nền ồn của từng tệp.",
            ),
            (
                "WebRTC",
                "Web Real-Time Communication",
                "Chuẩn giao tiếp âm thanh/hình ảnh thời gian thực tích hợp sẵn trong trình duyệt Chrome, Edge, Safari khi người dùng bấm nút thu micro.",
            ),
            (
                "Repeat Padding",
                "Đệm nối lặp tuần hoàn",
                "Kỹ thuật nhân bản nối đuôi chính đoạn sóng âm ngắn cho tới khi đạt đủ 64.000 mẫu nhằm giữ liên tục phổ - thời gian.",
            ),
            (
                "Zero-Padding",
                "Đệm chèn số không",
                "Cách điền đầy đuôi tín hiệu ngắn bằng các số 0 — bị nghiêm cấm trong ViTrueVoice vì gây vách nhảy phổ giả và rò rỉ độ dài.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 3.3 Chuẩn hóa EBU R128 (-23 LUFS), Z-Score & Comfort Dithering
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "3.3 Chuẩn Hóa Độ To EBU R128 (−23 LUFS), Chuẩn Hóa Z-Score & Ranh Giới Comfort Dithering",
    )

    add_styled_paragraph(
        doc,
        "Để đảm bảo hai bản ghi âm dù thu gần micro hay xa micro đều đi vào mạng `Wav2Vec 2.0` với cùng một thang đo biên "
        "độ thống nhất, hệ thống áp dụng chuẩn hóa kép kết hợp kiểm soát nhiễu nền thông minh:",
    )

    add_bullet_item(
        doc,
        "Áp dụng tiêu chuẩn phát thanh truyền hình quốc tế **`EBU R128`** đưa độ to tích hợp (*Integrated Loudness* qua bộ "
        "lọc thính giác *K-weighting*) của cả mẫu thật lẫn mẫu giả về đúng mức **`−23 LUFS`**, loại bỏ hoàn toàn khả năng "
        "mô hình đoán nhãn dựa trên độ to nhỏ trung bình của nguồn phát.",
        "1. Chuẩn hóa độ to cảm nhận EBU R128 (−23 LUFS)",
    )
    add_bullet_item(
        doc,
        "Mỗi cửa sổ `64.000` mẫu tiếp tục được chuẩn hóa thống kê **`Z-Score`** đưa giá trị trung bình `μ` về `0` (triệt "
        "tiêu hoàn toàn dòng điện một chiều *DC Offset* gây sóng ù `50Hz`) và đưa phương sai về `1`, giúp các bộ lọc tích "
        "chập tầng đầu của `Wav2Vec 2.0` hội tụ ổn định tuyệt đối:",
        "2. Chuẩn hóa thống kê dạng sóng Z-Score Normalization",
    )

    zscore_eq = (
        omml_sub(omml_r("x"), omml_r("norm", normal=True))
        + omml_delim(omml_r("n"), beg="[", end="]")
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("x"), omml_r("pad", normal=True))
            + omml_delim(omml_r("n"), beg="[", end="]")
            + omml_r(" − μ", normal=True),
            omml_r("σ + ε"),
        )
    )
    add_omml_equation(
        doc,
        "Chuẩn hóa thống kê biên độ sóng âm Z-Score trên từng cửa sổ 64.000 mẫu",
        zscore_eq,
        variables=[
            ("x_norm[n]", "Giá trị biên độ chuẩn hóa cuối cùng đưa vào tensor mạng nơ-ron (có kỳ vọng bằng 0 và độ lệch chuẩn xấp xỉ 1)."),
            ("μ", "Giá trị trung bình cộng biên độ của 64.000 mẫu trong cửa sổ (khử lệch nền một chiều DC Offset)."),
            ("σ", "Độ lệch chuẩn biên độ của 64.000 mẫu trong cửa sổ."),
            ("ε = 10⁻⁸", "Hằng số an toàn cực nhỏ cộng vào mẫu số để ngăn lỗi chia cho 0 trong trường hợp tín hiệu phẳng."),
        ],
    )

    add_bullet_item(
        doc,
        "Với các tệp giọng thật thu từ thiết bị di động có phần cứng triệt ồn quá gắt làm sàn nhiễu vùng lặng rơi xuống "
        "`σ_floor < 10⁻⁴`, kỹ thuật **`Adaptive Comfort Dithering`** (theo chuẩn viễn thông `RFC 3389` / `AES-17`) cho phép "
        "bù một lớp nhiễu nền Gauss vi mô (`σ_dither = 0,0035`, giữ tỷ số tín hiệu trên nhiễu **`SNR`** rất cao không nghe "
        "thấy bằng tai thường) để khôi phục sự liên tục tự nhiên. **Đặc biệt lưu ý ranh giới cô lập pháp y**: Hệ thống khóa "
        "cứng `apply_dither = False` trên mọi luồng thẩm định bản nhân bản `OmniVoice CFM`, bởi nếu rải nhiễu ngẫu nhiên lên "
        "âm thanh giả mạo sẽ vô tình che mờ các vết đứt gãy pha vi mô của bộ giải mã CFM!",
        "3. Bù đắp nhiễu tiện nghi thích ứng (Adaptive Comfort Dithering) & Ranh giới cô lập mẫu giả",
    )

    add_term_glossary(
        doc,
        [
            (
                "LUFS & EBU R128",
                "Loudness Units relative to Full Scale",
                "Đơn vị đo độ to cảm nhận chuẩn phát thanh châu Âu EBU R128 (mốc chuẩn −23 LUFS phản ánh đúng độ nhạy tai người ở từng tần số).",
            ),
            (
                "Z-Score",
                "Standard Score Normalization",
                "Phép biến đổi thống kê trừ đi trung bình μ và chia cho độ lệch chuẩn σ để đưa mọi cửa sổ sóng âm về phân phối chuẩn tắc.",
            ),
            (
                "SNR",
                "Signal-to-Noise Ratio",
                "Tỷ số công suất tín hiệu giọng nói hữu ích trên công suất tạp âm nền (tính bằng dB); SNR càng cao âm thanh càng trong sạch.",
            ),
            (
                "Comfort Dithering",
                "Nhiễu tiện nghi vi mô (RFC 3389 / AES-17)",
                "Lớp nhiễu trắng biên độ siêu nhỏ bù vào vùng số 0 nhân tạo của micro chống ồn nhằm xóa vết cắt cổng squelch mà không làm ồn câu nói.",
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # 3.4 Năm cấu hình Codec thực tế & Tăng cường nhiễu RawBoost
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "3.4 Năm Cấu Hình Kênh Truyền Thực Tế (5 Codec Profiles) & Mô Phỏng Nhiễu RawBoost (LnL + ISD)",
    )

    add_foundation_primer(
        doc,
        process_name="Mô phỏng suy giảm 5 kênh truyền nén (Codecs) & Tăng cường nhiễu sóng âm RawBoost",
        why_needed=(
            "Muốn một vận động viên thi đấu thắng lợi dưới trời mưa bão, họ không thể chỉ tập luyện mãi trong nhà thi đấu "
            "máy lạnh. Tương tự, muốn mô hình bắt được giọng giả gửi qua Zalo và mạng di động, ta phải cho mô hình cọ xát "
            "trực tiếp với đúng các phép nén mất mát và méo dạng phần cứng micro ngay trong lúc học."
        ),
        real_analogy=(
            "Giống như luyện thi nghe tiếng Anh giao tiếp thực tế: nếu chỉ nghe băng đọc chuẩn phòng thu BBC (Clean 16kHz), "
            "khi ra sân bay nghe loa phát thanh rè đục (AMR-NB / G.711) hoặc nói chuyện qua bộ đàm sóng yếu (Opus 24k + RawBoost), "
            "người học sẽ không nghe ra chữ nào. Luyện nghe đa môi trường giúp não bộ nắm bắt cốt lõi ngữ âm bất biến!"
        ),
        core_points=[
            "Kênh băng rộng OTT (Wideband — Zalo AAC-LC, Zalo Opus) giữ được dải tần 60–7.800 Hz nhưng áp dụng lượng tử hóa băng con MDCT xóa các chi tiết phổ năng lượng thấp.",
            "Kênh băng hẹp viễn thông (Narrowband — G.711 A-law, AMR-NB) lấy mẫu ở 8.000 Hz và cắt phăng mọi tần số dưới 300 Hz lẫn trên 3.400 Hz, buộc mô hình phải tìm dấu vết giả mạo ngay trong vùng lõi nguyên âm F0 và Formants F1–F3.",
            "RawBoost tạo nhiễu toán học trực tiếp lên sóng âm ngay trên RAM (không cần trộn tệp tiếng ồn thu sẵn bên ngoài), ngăn chặn nguy cơ mô hình học vẹt chính tệp tiếng ồn phụ trợ.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Phiên bản **`ViTrueVoice v0.9.4`** chuẩn hóa ma trận **5 cấu hình kênh truyền thực tế** đại diện đầy đủ cho hạ "
        "tầng nhắn tin mạng xã hội và mạng viễn thông tại Việt Nam:",
    )

    add_styled_table(
        doc,
        headers=[
            "Mã Kênh (Codec)",
            "Thông Số Kỹ Thuật Chuẩn",
            "Dải Tần Hữu Dụng",
            "Đặc Điểm Biến Dạng Vật Lý",
            "EER v0.9.4 (Test)",
        ],
        rows=[
            (
                "clean_16khz",
                "PCM 16-bit không nén @ 16kHz Mono (256 kbps)",
                "50 – 8.000 Hz",
                "Âm thanh chuẩn đối chứng bảo toàn nguyên vẹn toàn dải phổ Nyquist.",
                "5,52%",
            ),
            (
                "aac_zalo_76k",
                "Zalo Profile A: AAC-LC @ 48kHz Mono (.m4a, 76 kbps)",
                "60 – 7.800 Hz",
                "Gửi tệp đính kèm qua Zalo; lượng tử hóa MDCT & che lấp tâm lý âm học.",
                "5,79%",
            ),
            (
                "opus_zalo_24k",
                "Zalo Profile B: Opus @ 16k/48k (.ogg, 24 kbps)",
                "60 – 7.500 Hz",
                "Tin nhắn thoại bấm giữ trên Zalo (lai ghép bộ mã giọng nói SILK + CELT).",
                "6,02%",
            ),
            (
                "g711_alaw",
                "PSTN / VoIP: ITU-T G.711 A-law @ 8kHz (64 kbps)",
                "300 – 3.400 Hz",
                "Nén logarit 8-bit/mẫu mạng cố định; cắt trắng toàn bộ tần số > 3,4 kHz.",
                "6,11%",
            ),
            (
                "amr_nb",
                "2G/3G GSM: 3GPP AMR-NB @ 8kHz (4,75–12,2 kbps)",
                "300 – 3.400 Hz",
                "Mã hóa dự đoán tuyến tính ACELP siêu nén trên mạng di động băng hẹp.",
                "4,88%",
            ),
        ],
        col_widths=[1.15, 1.65, 1.05, 1.95, 0.90],
        highlight_row_pred=lambda idx, _: True,
    )

    add_styled_paragraph(
        doc,
        "Bên cạnh 5 cấu hình nén kênh truyền, trong quá trình nạp dữ liệu huấn luyện (`DataLoader`), mỗi cửa sổ sóng âm "
        "còn đi qua bộ tăng cường nhiễu miền thời gian **`RawBoost`** (với xác suất kích hoạt ngẫu nhiên `50%`) gồm hai "
        "cơ chế vật lý kết hợp:",
    )

    add_bullet_item(
        doc,
        "Cho tín hiệu đi qua chuỗi bộ lọc đáp ứng xung hữu hạn (`FIR`) đa dải có hệ số ngẫu nhiên kết hợp hàm biến dạng "
        "lũy thừa bậc cao. Nhánh `LnL` mô phỏng chân thực sự sai khác đáp tuyến tần số giữa hàng trăm loại micro điện "
        "thoại giá rẻ, tai nghe không dây, loa ngoài và hiện tượng méo hài phi tuyến của mạch khuếch đại thu âm.",
        "1. Nhánh LnL (Linear and Non-Linear Convolutive Noise — Nhiễu tích chập tuyến tính và phi tuyến)",
    )
    add_bullet_item(
        doc,
        "Cộng trực tiếp các xung nhiễu ngẫu nhiên có biên độ tỷ lệ thuận với biên độ tức thời của chính mẫu sóng âm tại "
        "điểm đó. Nhánh `ISD` tái hiện chính xác hiện tượng luồng hơi bật mạnh phả vào micro (*plosives*), nhiễu lạo xạo "
        "lượng tử và mất gói vi mô theo biên độ tín hiệu. Thực nghiệm đối chứng chứng minh việc kết hợp `RawBoost` giúp "
        "giảm thêm **`13,8% – 22,1%` tỷ lệ lỗi EER tương đối** trên mọi kênh truyền.",
        "2. Nhánh ISD (Impulsive Signal-Dependent Noise — Nhiễu xung phụ thuộc tín hiệu)",
    )

    if figs and "fig3" in figs:
        add_figure(
            doc,
            figs["fig3"],
            "Hình 3.1: Minh họa trực quan hai quyết định tiền xử lý cốt lõi trong Chương 3. "
            "Khung A (Trái): So sánh dạng sóng 4,0 giây (64.000 mẫu @ 16kHz) giữa lỗi thiết kế Zero-Padding (tạo vách đứt "
            "gãy biên độ rơi thẳng về 0 tại 2,25s) và kỹ thuật chuẩn Repeat Padding (nối lặp tuần hoàn bảo toàn tính liên "
            "tục sóng âm). Khung B (Phải): Đối chiếu dải băng thông tần số giữ lại được của 5 kênh truyền trong ViTrueVoice "
            "v0.9.4, cho thấy sự thu hẹp khắc nghiệt từ 50–8.000 Hz (Clean) xuống chỉ còn 300–3.400 Hz trên G.711 và AMR-NB.",
        )

    add_callout_box(
        doc,
        "Câu hỏi hay gặp từ Hội đồng: **'Tại sao kênh di động AMR-NB nén khắc nghiệt nhất (4,75–12,2 kbps, cắt mất sạch tần "
        "số trên 3,4 kHz) mà mô hình v0.9.4 lại đạt EER = 4,88% thấp hơn cả kênh Clean 16kHz (5,52%)?'** — Cách trả lời "
        "điểm 10: *'Dạ thưa Thầy/Cô, có 2 nguyên nhân khoa học: Thứ nhất, vì mô hình được huấn luyện đối xứng trên cả 5 "
        "kênh nén, khối Wav2Vec 2.0 + HS-GAL không còn phụ thuộc vào nhiễu tần số cao > 4 kHz mà tập trung hoàn toàn vào "
        "dải lõi 300–3.400 Hz nơi chứa tần số cơ bản F0 của 6 thanh điệu tiếng Việt và 3 formant đầu tiên (F1, F2, F3). "
        "Thứ hai, bộ mã hóa dự đoán tuyến tính ACELP của AMR-NB được thiết kế tối ưu riêng cho mô hình ống thanh quản sinh "
        "học của con người; khi gặp sóng âm nhân tạo có pha phi sinh học từ các vocoder TTS, bộ lọc ACELP tạo ra biến dạng "
        "tái tổng hợp đặc trưng ngay trong vùng 300–3.400 Hz giúp đồ thị AASIST nhận diện càng sắc nét hơn.'*",
        title="BÍ QUYẾT PHẢN BIỆN CHƯƠNG 3: GIẢI THÍCH HIỆN TƯỢNG AMR-NB ĐẠT EER 4,88% XUẤT SẮC",
    )

    add_term_glossary(
        doc,
        [
            (
                "AAC-LC",
                "Advanced Audio Coding — Low Complexity",
                "Chuẩn nén âm thanh hiện đại dùng cho tệp âm thanh .m4a trên iOS, Android và tệp đính kèm Zalo (76 kbps @ 48kHz).",
            ),
            (
                "Opus",
                "IETF RFC 6716 Interactive Audio Codec",
                "Chuẩn nén thoại độ trễ siêu thấp kết hợp thuật toán SILK và CELT, được Zalo và Telegram sử dụng cho tin nhắn thoại trực tiếp (24 kbps).",
            ),
            (
                "G.711 A-law",
                "ITU-T Pulse Code Modulation Companding",
                "Chuẩn nén thoại tổng đài cố định PSTN Châu Âu/Việt Nam ở tần số 8kHz (64 kbps), giữ lại dải tần hẹp 300–3.400 Hz.",
            ),
            (
                "AMR-NB & ACELP",
                "Adaptive Multi-Rate Narrowband & Algebraic Code-Excited Linear Prediction",
                "Chuẩn nén thoại mạng di động GSM 2G/3G ở 8kHz (4,75–12,2 kbps) mô hình hóa ống thanh quản bằng bộ lọc dự đoán tuyến tính.",
            ),
            (
                "RawBoost (LnL + ISD)",
                "Waveform-level Data Augmentation",
                "Thuật toán bơm nhiễu tích chập tuyến tính/phi tuyến (LnL) và nhiễu xung phụ thuộc tín hiệu (ISD) trực tiếp lên sóng âm khi huấn luyện.",
            ),
        ],
    )
