"""
Chương 4, 5, 6 của Sổ tay Bảo vệ & Nghiên cứu Chuyên sâu ViTrueVoice v0.9.4:
- Chương 4: Kiến trúc mạng lai SSL-AASIST, Huấn luyện 2 pha & Hiệu chuẩn đầu phân loại head_blend_a0.75
- Chương 5: Thuật toán gộp đa cửa sổ đồng thuận bất đối xứng (Multi-Window Consensus Asymmetric Veto)
- Chương 6: Hiệu chuẩn xác suất Platt Scaling, Vùng cảnh báo biên & Hàng rào giám định số chuẩn NIST
"""

from __future__ import annotations

from docx.shared import Pt

from .styles import (
    add_bullet_item,
    add_callout_box,
    add_figure,
    add_foundation_primer,
    add_heading_chapter,
    add_heading_part,
    add_heading_section,
    add_heading_subsection,
    add_omml_equation,
    add_styled_paragraph,
    add_styled_table,
    add_term_glossary,
    omml_delim,
    omml_frac,
    omml_r,
    omml_sub,
    omml_subsup,
    omml_sup,
)


def add_chapters_4_to_6(doc, figs: dict | None = None) -> None:
    """Biên soạn Chương 4, 5 và 6 cho Sổ tay Bảo vệ ViTrueVoice v0.9.4."""

    add_heading_part(
        doc,
        "PHẦN III: KIẾN TRÚC MẠNG HỌC SÂU SSL-AASIST, GỘP ĐA CỬA SỔ ĐỒNG THUẬN & HIỆU CHUẨN XÁC SUẤT",
    )

    # =========================================================================
    # CHƯƠNG 4: KIẾN TRÚC MẠNG LAI SSL-AASIST, HUẤN LUYỆN 2 PHA & HEAD_BLEND_A0.75
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 4",
        "Kiến Trúc Mạng Lai SSL-AASIST, Huấn Luyện 2 Pha & Hiệu Chuẩn Đầu Phân Loại head_blend_a0.75",
    )

    add_styled_paragraph(
        doc,
        "Trái tim nhận thức của **ViTrueVoice v0.9.4** là kiến trúc lai ghép giữa bộ mã hóa biểu diễn tự giám sát tiếng Việt "
        "(`nguyenvulebinh/wav2vec2-base-vietnamese-250h`) và mạng đồ thị chú ý không đồng nhất thời gian - tần số (`Compact AASIST`). "
        "Chương này giải thích tường minh từ trực giác nền tảng đến từng tầng toán học trong mã nguồn `src/models/ssl_aasist.py`, "
        "`src/training/losses.py` và cơ chế hiệu chuẩn đầu phân loại `head_blend_a0.75` giúp hệ thống đạt `5.63% EER` trên `15.980` mẫu kiểm thử.",
    )

    # -------------------------------------------------------------------------
    # MỤC 4.1: KIẾN TRÚC MÔ HÌNH SSL-AASIST & ĐỐI SÁNH BASELINES
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "4.1 Kiến Trúc Mạng Lai SSL-AASIST & Sự Tiến Hóa Vượt Qua Các Baseline Cổ Điển",
    )

    add_foundation_primer(
        doc,
        process_name="Kiến Trúc Mạng Lai Học Tự Giám Sát & Đồ Thị Âm Học (SSL-AASIST)",
        why_needed=(
            "Các bộ phát hiện cổ điển dựa trên đặc trưng phổ thủ công (như LFCC+GMM) hoặc mạng nơ-ron học từ con số 0 "
            "phụ thuộc nặng vào các hài âm tần số cao trên 4 kHz. Khi âm thanh đi qua bộ nén thoại Zalo (Opus 24kbps, AAC-LC 76kbps) "
            "hoặc mạng di động GSM (AMR-NB 8kHz, cắt sạch tần số trên 3.4 kHz), các dấu vết tần số cao này bị xóa sổ khiến mô hình cũ sụp đổ. "
            "Ta cần một kiến trúc đã thông thạo quy luật ngữ âm - thanh điệu tiếng Việt trước khi học cách truy tìm vết giả mạo."
        ),
        real_analogy=(
            "Hãy hình dung việc tuyển chuyên gia giám định giọng nói giả: Phương pháp huấn luyện từ đầu giống như tuyển một người "
            "chưa từng nghe tiếng Việt và bắt họ nhìn hình sóng để đoán thật giả. Ngược lại, **SSL (Học tự giám sát)** giống như tuyển một "
            "nhà ngôn ngữ học bản xứ đã nghe trọn vẹn **250 giờ giọng nói tiếng Việt thật** đủ mọi thanh điệu Bắc - Trung - Nam (`Wav2Vec 2.0`), "
            "sau đó trang bị thêm cho vị chuyên gia này một **bàn nối dây điều tra hình sự (`GNN AASIST`)** để đối chiếu chéo từng thời điểm "
            "với từng dải tần số nhằm vạch trần những nhịp chuyển thanh điệu phi sinh học của AI."
        ),
        core_points=[
            "**Học tự giám sát (`Self-Supervised Learning - SSL`)**: Mô hình tự che ngẫu nhiên các đoạn sóng âm ngắn rồi tự dự đoán phần bị che trên 250 giờ tiếng Việt không nhãn, qua đó tự động nắm bắt cấu trúc 6 thanh điệu (ngang, huyền, sắc, hỏi, ngã, nặng) và quy luật nối âm tự nhiên.",
            "**Tích chập 1D (`CNN`) so với Tự chú ý (`Transformer Self-Attention`)**: Khối `CNN` đóng vai trò kính lúp cục bộ soi từng khung 25 ms để trích xuất hình thái sóng cơ sở, còn `Transformer Self-Attention` cho phép mỗi khung âm thanh nhìn bao quát toàn bộ câu nói 4.0 giây để phát hiện sự bất nhất ngữ điệu giữa đầu câu và cuối câu.",
            "**Mạng nơ-ron đồ thị (`Graph Neural Network - GNN`)**: Thay vì ép âm thanh vào lưới ô vuông cố định như ảnh 2D, `GNN` biểu diễn mỗi khung thời gian và mỗi dải tần số thành các **Nút (Nodes)** nối nhau bằng **Cạnh (Edges)** có trọng số chú ý, cho phép tần số cơ bản 120 Hz đối chiếu trực tiếp với hài âm 3.000 Hz.",
            "**Tại sao `LFCC+GMM` thất bại trên kênh thoại nén?** `LFCC` chỉ chụp bao phổ tĩnh theo thang tuyến tính còn `GMM` giả định các chiều đặc trưng độc lập từng khung; khi bộ mã hóa thoại lượng tử hóa thô và cắt băng thông, phân phối Gauss của giọng thật và giọng giả chồng lấp gần như hoàn toàn.",
        ],
    )

    add_heading_subsection(
        doc,
        "4.1.1 Đối sánh 3 thế hệ kiến trúc trong dự án: LFCC+GMM, AASIST nguyên bản và SSL-AASIST",
    )
    add_styled_paragraph(
        doc,
        "Để trả lời thuyết phục câu hỏi của Hội đồng *\"Vì sao không dùng các mô hình nhẹ cổ điển như LFCC+GMM hay AASIST huấn luyện từ đầu?\"*, "
        "dự án đã hiện thực đầy đủ cả ba thế hệ mô hình trong `src/models/` để đối chứng thực nghiệm công bằng trên cùng một quy trình tiền xử lý:",
    )

    add_styled_table(
        doc,
        headers=[
            "Tiêu Chí Kỹ Thuật",
            "Baseline 1: LFCC + GMM",
            "Baseline 2: Raw AASIST (Từ đầu)",
            "ViTrueVoice v0.9.4: SSL-AASIST",
        ],
        rows=[
            (
                "Đầu vào trực tiếp",
                "Bao phổ tuyến tính 60 chiều (20 LFCC + Δ + ΔΔ) trích xuất thủ công",
                "Sóng âm thô 64.000 mẫu qua bộ lọc dải SincConv cố định",
                "Sóng âm thô 64.000 mẫu (4.0s @ 16kHz) chuẩn hóa Z-score nội bộ",
            ),
            (
                "Tri thức tiếng Việt tiền huấn luyện",
                "Không có (0 giờ) — mù hoàn toàn về cấu trúc 6 thanh điệu",
                "Không có (0 giờ) — chỉ học từ tập chống giả mạo hạn hẹp",
                "250 giờ tiếng Việt chuẩn (`wav2vec2-base-vietnamese-250h`)",
            ),
            (
                "Mô hình hóa không - thời gian",
                "Trộn Gauss tĩnh (`GMM`), mất thứ tự thời gian dài hạn",
                "Đồ thị không đồng nhất `HS-GAL` nhưng thiếu ngữ cảnh ngôn ngữ",
                "12 tầng `Transformer` ngữ cảnh xa + 2 tầng đồ thị dị thể `HS-GAL`",
            ),
            (
                "Độ bền qua kênh nén Zalo / GSM 8kHz",
                "Sụp đổ nặng (EER > 25–35%) khi mất dải tần > 3.4 kHz",
                "Nhạy cảm với méo nén MDCT/CELP nếu thiếu biểu diễn ngữ âm gốc",
                "Bền vững vượt trội: EER 4.88% (AMR-NB) đến 6.11% (G.711) trên 15.980 mẫu",
            ),
            (
                "Năng lực bắt giọng giả dòng liên tục CFM",
                "Gần như đoán mò vì CFM có bao phổ trung bình cực mượt",
                "Dễ học vẹt nhiễu phòng thu (channel shortcut)",
                "Phát hiện vi sai số tích phân ODE của `OmniVoice CFM` (chặn 91.52%)",
            ),
        ],
        col_widths=[1.35, 1.65, 1.75, 1.95],
    )

    add_heading_subsection(
        doc,
        "4.1.2 Giải phẫu khối Front-end tự giám sát tiếng Việt (`SSLFrontEnd`)",
    )
    add_styled_paragraph(
        doc,
        "Trong `src/models/ssl_aasist.py`, lớp `SSLFrontEnd` nạp trực tiếp mô hình `nguyenvulebinh/wav2vec2-base-vietnamese-250h` "
        "và thực thi chuỗi biến đổi chính xác theo 4 bước toán học:",
    )
    add_bullet_item(
        doc,
        "Mỗi cửa sổ sóng âm đầu vào kích thước `(B, 64000)` (đúng `4.0 giây` ở tần số `16.000 Hz`, đệm lặp `Repeat Padding` nếu clip ngắn) "
        "được chuẩn hóa Z-score trực tiếp theo trục thời gian với hằng số ổn định số học `1e-7` nhằm khử hoàn toàn sai lệch âm lượng thu âm.",
        bold_prefix="1. Chuẩn hóa biên độ nội bộ theo từng cửa sổ",
    )
    add_bullet_item(
        doc,
        "Gồm **7 tầng tích chập 1 chiều (`1D Temporal CNN`)** với bước trượt tổng hợp `320 mẫu` (`20 ms`) và vùng cảm nhận `400 mẫu` (`25 ms`), "
        "biến đổi chuỗi `64.000` điểm sóng thô thành đúng `T = 199` khung đặc trưng tiềm ẩn liên tục.",
        bold_prefix="2. Khối mã hóa sóng cục bộ 7 tầng CNN",
    )
    add_bullet_item(
        doc,
        "Gồm **12 tầng `Transformer Encoder`** (`hidden_size = 768`, `12` đầu chú ý `Multi-Head Self-Attention`). "
        "Đặc biệt, mã nguồn chủ động khóa `apply_spec_augment = False` và `layerdrop = 0.0` để ngăn mô hình tự đục lỗ phổ ngẫu nhiên — "
        "vì trong bài toán giám định giả mạo, việc che khuất dải tần nội bộ có thể vô tình xóa đúng vết rạn vi mô của bộ tạo sinh `CFM` hoặc `Vocos`.",
        bold_prefix="3. Khối ngữ cảnh toàn cục 12 tầng Transformer",
    )
    add_bullet_item(
        doc,
        "Ma trận biểu diễn `(B, 199, 768)` từ tầng ẩn cuối cùng được nén qua phép chiếu tuyến tính học được `nn.Linear(768, 128)` "
        "thành tensor `(B, 199, 128)`, giảm hơn 83% chi phí tính toán cho khối đồ thị phía sau mà vẫn giữ trọn tinh hoa thanh điệu tiếng Việt.",
        bold_prefix="4. Tầng chiếu nén chiều thông tin (`768 → 128`)",
    )

    add_heading_subsection(
        doc,
        "4.1.3 Giải phẫu khối Back-end đồ thị dị thể `Compact AASIST` (`HS-GAL` & `Master Node`)",
    )
    add_styled_paragraph(
        doc,
        "Các công cụ nhân bản giọng nói thế hệ mới như `F5-TTS` và `OmniVoice CFM` tạo ra âm thanh cực kỳ tự nhiên nếu xét riêng "
        "từng khung thời gian hoặc xét riêng phổ trung bình, nhưng lại để lộ **sự lệch pha tinh vi giữa biến thiên thanh điệu theo thời gian "
        "và cấu trúc hài âm theo tần số**. Khối `Compact AASIST` trong lớp `SSLAASIST` giải quyết bài toán này qua 4 tầng xử lý:",
    )
    add_bullet_item(
        doc,
        "Tensor `(B, 199, 128)` được chuyển vị thành bản đồ 2 chiều `(B, 1, 128, 199)`, giảm chiều qua `MaxPool2d(3, 3)` còn `(B, 1, 42, 66)` "
        "rồi đi qua 2 khối dư `ResBlock2d` (`1 → 16 → 32` kênh) dùng hàm kích hoạt tự chuẩn hóa `SELU` và `BatchNorm2d` để làm nổi bật các biên chuyển tiếp phổ.",
        bold_prefix="Bước 1 — Trích xuất bản đồ đặc trưng 2D (`ResBlock2d`)",
    )
    add_bullet_item(
        doc,
        "Từ bản đồ `(B, 32, 42, 66)`, mô hình lấy cực đại tuyệt đối dọc trục thời gian để lập `42` nút phổ tần số và lấy cực đại dọc trục tần số "
        "để lập `66` nút thời gian, sau đó đưa qua hai mạng chú ý đồ thị độc lập `gat_s` và `gat_t` (`GraphAttention(32 → 64)`).",
        bold_prefix="Bước 2 — Khởi tạo đồ thị Tần số (`gat_s`) và Thời gian (`gat_t`)",
    )
    add_bullet_item(
        doc,
        "Hai tập nút được ghép chung thành đồ thị dị thể `N = 108` nút (`66` nút thời gian + `42` nút phổ) đi qua **2 tầng `HS-GAL`** nối tiếp. "
        "Điểm đắt giá nhất trong lớp `HSGAL` là ma trận tham số `att_w` kích thước `(64, 3)` phân biệt rạch ròi **3 loại cạnh truyền tin**: "
        "(0) cạnh Thời gian–Thời gian, (1) cạnh Tần số–Tần số, và (2) **cạnh chéo Thời gian–Tần số** giúp phát hiện ngay lập tức khi đường cong thanh điệu "
        "dấu ngã/dấu hỏi đổi hướng nhưng dải hài âm bậc cao không dịch chuyển tương ứng.",
        bold_prefix="Bước 3 — Truyền tin dị thể 3 loại cạnh (`HS-GAL`)",
    )
    add_bullet_item(
        doc,
        "Một nút tham số học được `Master Node` kích thước `(1, 1, 64)` thực hiện cơ chế chú ý toàn cục lên toàn bộ `108` nút ở mỗi tầng `HS-GAL`. "
        "Cuối cùng, mô hình ghép nối 5 vector thống kê (`max` thời gian, `mean` thời gian, `max` tần số, `mean` tần số và `Master Node`) thành vector nhúng "
        "`320` chiều (`5 × 64`), đưa qua tầng `Linear(320 → 2)` xuất cặp logit `[z_spoof, z_bonafide]` và tính điểm quyết định `s = z_bonafide − z_spoof`.",
        bold_prefix="Bước 4 — Tổng hợp qua `Master Node` và xuất điểm thô `s`",
    )

    if figs and "fig4" in figs:
        add_figure(
            doc,
            figs["fig4"],
            "Hình 4.1: Sơ đồ kiến trúc mạng lai SSL-AASIST kết hợp quy trình huấn luyện 2 pha và hiệu chuẩn đầu phân loại head_blend_a0.75 trên ViTrueVoice v0.9.4.",
        )

    add_term_glossary(
        doc,
        [
            ("SSL", "Self-Supervised Learning", "Học tự giám sát: phương pháp cho mạng nơ-ron tự học quy luật ngữ âm từ hàng trăm giờ giọng nói thô không cần nhãn thủ công bằng cách che và đoán lại các đoạn sóng."),
            ("Wav2Vec 2.0", "Waveform-to-Vector 2.0", "Kiến trúc mạng tự giám sát âm thanh của Meta AI gồm 7 tầng CNN và 12 tầng Transformer; bản trong đồ án được tiền huấn luyện chuyên sâu trên 250 giờ tiếng Việt."),
            ("CNN", "Convolutional Neural Network", "Mạng nơ-ron tích chập: dùng các bộ lọc trượt cục bộ để trích xuất hình dạng sóng âm trong những khoảng thời gian rất ngắn (20–25 ms)."),
            ("Transformer / Self-Attention", "Cơ chế Tự chú ý", "Kiến trúc giúp mỗi khung thời gian tính trọng số liên kết với mọi khung khác trong câu nói 4 giây để nắm bắt ngữ điệu dài hạn."),
            ("LFCC + GMM", "Linear Frequency Cepstral Coefficients + Gaussian Mixture Model", "Phương pháp chống giả mạo cổ điển ghép đặc trưng bao phổ tần số tuyến tính với mô hình trộn phân phối chuẩn Gauss."),
            ("GNN", "Graph Neural Network", "Mạng nơ-ron đồ thị: mô hình hóa dữ liệu dưới dạng các đỉnh (nút) và các mối liên kết (cạnh), cho phép truyền tin linh hoạt vượt khỏi khuôn lưới cố định."),
            ("AASIST", "Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks", "Kiến trúc mạng đồ thị chú ý tích hợp phổ - thời gian hàng đầu trong lĩnh vực phát hiện giọng nói giả mạo."),
            ("HS-GAL", "Heterogeneous Stacking Graph Attention Layer", "Tầng chú ý đồ thị chồng ghép không đồng nhất: xử lý đồng thời nút thời gian và nút tần số bằng 3 bộ trọng số cạnh riêng biệt."),
            ("Master Node", "Nút Chủ Quyền / Nút Tổng Hợp Toàn Cục", "Một nút đặc biệt kết nối tới tất cả các nút thời gian và tần số để đúc kết bản tóm tắt toàn cục trước khi phân loại."),
        ],
    )

    # -------------------------------------------------------------------------
    # MỤC 4.2: HUẤN LUYỆN 2 PHA, HÀM MẤT MÁT & HIỆU CHUẨN HEAD_BLEND_A0.75
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "4.2 Chiến Lược Huấn Luyện 2 Pha, Hàm Mất Mát Siêu Cầu & Hiệu Chuẩn Đầu Phân Loại head_blend_a0.75",
    )

    add_foundation_primer(
        doc,
        process_name="Huấn Luyện 2 Pha, Hàm Mất Mát Biên Góc & Nội Suy Trọng Số Đầu Phân Loại",
        why_needed=(
            "Khi ghép khối `Wav2Vec 2.0` đã tinh thông tiếng Việt với khối đồ thị `AASIST` vừa khởi tạo ngẫu nhiên, nếu cập nhật toàn mạng ngay lập tức "
            "với tốc độ học lớn, đạo hàm hỗn loạn từ tầng cuối sẽ phá hủy toàn bộ tri thức tiếng Việt 250 giờ. Thêm vào đó, tập huấn luyện thực tế có số mẫu "
            "giọng thật nhiều gấp hơn 6 lần giọng giả (`47.000` so với `7.400`), và sau khi học sâu các mẫu `CFM` khó, ranh giới đầu ra cần được cân tâm chính xác tại `θ = 0.0`."
        ),
        real_analogy=(
            "Giống như **ghép một vị nhạc trưởng kỳ cựu (`Wav2Vec 2.0`) với một dàn nhạc mới lập (`AASIST`)**: "
            "Ở **Pha 1**, nhạc trưởng đứng yên giữ nhịp chuẩn (đóng băng `SSL`) để dàn nhạc mới tập đánh đúng phách trước. "
            "Sang **Pha 2**, cả nhạc trưởng và dàn nhạc mới cùng vi chỉnh nhịp cực nhỏ để hòa quyện tuyệt đối. "
            "Cuối cùng ở **Giai đoạn 3 (`Head-Calibration`)**, kỹ sư âm thanh giữ nguyên cách chơi của cả dàn nhạc, chỉ xoay nhẹ nút cân bằng "
            "trên bàn tổng (`head_blend_a0.75`) để âm lượng hai kênh Thật - Giả nằm đúng vạch 0 chính giữa."
        ),
        core_points=[
            "**Quên thảm khốc (`Catastrophic Forgetting`)**: Hiện tượng mạng tiền huấn luyện bị mất sạch kiến thức nền tảng ban đầu khi bị cập nhật bằng tốc độ học quá lớn trên tác vụ mới.",
            "**Phạt trọng số hàm mất mát (`Dynamic Weighted Loss`) so với Lấy mẫu lặp (`Oversampling`)**: Cân bằng dữ liệu lệch bằng cách nhân hệ số phạt lớn hơn cho lớp ít mẫu ngay trong công thức tính lỗi; tuyệt đối không dùng chung với bộ lấy mẫu cân bằng để tránh nhân đôi hình phạt.",
            "**Biên độ góc trên mặt cầu (`AM-Softmax Angular Margin`)**: Chuẩn hóa vector đặc trưng lên mặt cầu bán kính 1 và ép giữa cụm Giọng Thật với cụm Giọng Giả phải có một khoảng hở góc an toàn `m`, giúp ranh giới không bị mong manh.",
            "**Nội suy tuyến tính không gian trọng số (`Weight-Space Linear Interpolation`)**: Khi hai đầu phân loại cùng đặt trên một thân trích xuất đặc trưng cố định (`Frozen Backbone`), phép lấy trung bình có trọng số `0.25 : 0.75` giữa chúng kết hợp hài hòa độ nhạy chặn giả mạo và độ an toàn cho giọng người thật.",
        ],
    )

    add_heading_subsection(
        doc,
        "4.2.1 Quy trình huấn luyện 2 pha, tốc độ học phân tầng và tối ưu bộ nhớ VRAM",
    )
    add_styled_paragraph(
        doc,
        "Để huấn luyện hiệu quả trên cả GPU đám mây (`NVIDIA T4 16GB`) lẫn GPU máy trạm cá nhân (`RTX 3050 4GB VRAM`) mà không làm hỏng "
        "biểu diễn ngữ âm của `Wav2Vec 2.0`, hệ thống áp dụng quy trình 3 chặng chặt chẽ:",
    )
    add_bullet_item(
        doc,
        "Gọi phương thức `model.freeze_ssl()` khóa hoàn toàn `requires_grad = False` và ép chế độ `.eval()` trên toàn bộ 7 tầng CNN + 12 tầng Transformer "
        "của `Wav2Vec 2.0`. Chỉ cập nhật tầng chiếu `Linear(768 → 128)`, khối đồ thị `Compact AASIST` và đầu phân loại với bộ tối ưu `AdamW` "
        "(`lr = 1e-4`, `weight_decay = 1e-4`). Bước làm ấm này giúp đồ thị `HS-GAL` hội tụ ổn định trước khi chạm vào backbone.",
        bold_prefix="Pha 1 — Khóa cứng SSL, làm ấm đồ thị Back-end (`Frozen Warm-up`)",
    )
    add_bullet_item(
        doc,
        "Gọi `model.unfreeze_ssl()` và phân tách tham số qua `model.param_groups(lr_backend, lr_ssl)` với **tốc độ học phân tầng (`Differential Learning Rates`)**: "
        "đặt `lr_ssl = 1e-6` cho khối `Wav2Vec 2.0` (nhỏ gấp 10 đến 100 lần để bảo toàn tri thức thanh điệu tiếng Việt) và `lr_backend = 1e-5` "
        "(hoặc `1e-4` ở các nhánh đầu) cho khối đồ thị `AASIST/Head` kèm lịch giảm `Cosine Annealing`. Nhờ cấu hình `batch_size = 8` kết hợp "
        "**tích lũy đạo hàm (`accum_steps = 2`, tương đương `effective_batch_size = 16`)**, mức chiếm dụng VRAM thực tế chỉ khoảng `1.1 GB`, "
        "loại bỏ 100% hiện tượng tràn bộ nhớ qua khe `PCIe paging` trên Windows 11.",
        bold_prefix="Pha 2 — Tinh chỉnh toàn mạng với Tốc độ học Phân tầng & Tích lũy đạo hàm",
    )

    add_heading_subsection(
        doc,
        "4.2.2 Hàm mất mát cân bằng động `Dynamic Weighted Cross-Entropy` & Cấm bù trừ kép",
    )
    add_styled_paragraph(
        doc,
        "Trong tập huấn luyện chính thức `train_v8_f5_omni_with_spk1.csv` (`54.400` dòng: gồm `47.000` mẫu `Bonafide` và `7.400` mẫu `Spoof` "
        "chia đều `3.710 F5-TTS` + `3.690 OmniVoice CFM`), số lượng mẫu thật nhiều gấp `6.35` lần mẫu giả do mở rộng kho giọng người thật đa vùng miền "
        "từ `VIVOS` và `Common Voice 8.0`. Để ngăn mô hình thiên vị lớp đa số, hàm `loss_weights_from_counts` trong `src/training/losses.py` "
        "tính tự động trọng số tỉ lệ nghịch tần suất thực tế của tập Train:",
    )

    eq_wce_weight = (
        omml_sub(omml_r("w"), omml_r("c"))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("N"),
            omml_r("2 · ", normal=True) + omml_sub(omml_r("N"), omml_r("c")),
        )
        + omml_r(" ,    ", normal=True)
        + omml_sub(omml_r("L"), omml_r("WCE", normal=True))
        + omml_r(" = −", normal=True)
        + omml_frac(omml_r("1", normal=True), omml_r("B"))
        + omml_r(" · ", normal=True)
        + omml_subsup(omml_r("∑", normal=True), omml_r("i=1", normal=True), omml_r("B"))
        + omml_r(" ", normal=True)
        + omml_sub(omml_r("w"), omml_sub(omml_r("y"), omml_r("i")))
        + omml_r(" · log", normal=True)
        + omml_delim(
            omml_sub(
                omml_r("p"),
                omml_r("i,") + omml_sub(omml_r("y"), omml_r("i")),
            )
        )
    )
    add_omml_equation(
        doc,
        "Trọng số lớp cân bằng động và Hàm mất mát Weighted Cross-Entropy",
        eq_wce_weight,
        variables=[
            ("N", "Tổng số mẫu của tập huấn luyện (`N = N_spoof + N_bonafide = 54.400` dòng ở bản chính thức `v0.9.4`)."),
            ("N_c", "Số lượng mẫu thực tế của từng lớp `c ∈ {0: Spoof, 1: Bonafide}` trong tập Train (sau chuẩn hóa tổng bằng 1 hoặc kẹp an toàn `clamp_range`)."),
            ("w_c", "Hệ số phạt động của lớp `c`: lớp ít mẫu (`Spoof`) nhận trọng số lớn hơn để cân bằng độ lớn kỳ vọng của đạo hàm giữa hai lớp."),
            ("B", "Kích thước lô huấn luyện hiệu dụng (`Effective Batch Size = 16`)."),
            ("y_i, p_{i, y_i}", "Nhãn thực tế và xác suất dự đoán tương ứng của mẫu thứ `i` trong lô."),
        ],
    )

    add_callout_box(
        doc,
        "Quy tắc bất khả xâm phạm (`STUBBORN_FACT`): **Tuyệt đối KHÔNG dùng đồng thời `WeightedRandomSampler` cùng với `Weighted Cross-Entropy`!** "
        "Nếu vừa dùng `WeightedRandomSampler` ép tần suất xuất hiện trong mỗi mini-batch về tỷ lệ `1 : 1` (nhân tần suất lớp `Spoof` lên `N_bona / N_spoof` lần), "
        "vừa tiếp tục nhân trọng số phạt `w_spoof / w_bona = N_bona / N_spoof` trong hàm mất mát, tỷ số đạo hàm thực tế sẽ bị phóng đại thành bình phương "
        "`(N_bona / N_spoof)² ≈ 40.3 lần` (**Lỗi bù trừ kép — Double Penalty**). Hậu quả là toàn bộ mặt phẳng quyết định bị đẩy lệch cực đoan sang vùng âm, "
        "khiến người dùng thật bị báo động giả hàng loạt.",
        title="GHI NHỚ PHẢN BIỆN HỘI ĐỒNG: TẠI SAO CẤM DÙNG CHUNG SAMPLER VÀ WEIGHTED LOSS?",
    )

    add_heading_subsection(
        doc,
        "4.2.3 Hàm mất mát siêu cầu `AM-Softmax` (`s = 30.0`, `m = 0.20`)",
    )
    add_styled_paragraph(
        doc,
        "Bên cạnh việc cân bằng số lượng mẫu, để chống lại các công cụ giả mạo chưa từng thấy (`Unseen TTS`), các vector đặc trưng `320` chiều "
        "của giọng người thật không chỉ cần nằm đúng phía bên phải ranh giới mà còn phải gom cụm thật chặt trên mặt cầu đơn vị. "
        "Lớp `AMSoftmaxLoss` trong `src/training/losses.py` chuẩn hóa độ dài L2 cho cả vector đặc trưng `x` lẫn vector trọng số tâm lớp `W_j`, "
        "biến tích vô hướng thành `cos(θ_j)` và trừ trực tiếp biên độ góc `m` vào lớp đúng `y`:",
    )

    am_margin_expr = omml_r("s · ", normal=True) + omml_delim(
        omml_r("cos ", normal=True) + omml_sub(omml_r("θ"), omml_r("y")) + omml_r(" − m", normal=True)
    )
    am_num = omml_sup(omml_r("e"), am_margin_expr)
    am_den = (
        am_num
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("∑", normal=True), omml_r("j≠y", normal=True))
        + omml_r(" ", normal=True)
        + omml_sup(
            omml_r("e"),
            omml_r("s · cos ", normal=True) + omml_sub(omml_r("θ"), omml_r("j")),
        )
    )
    eq_am = (
        omml_sub(omml_r("L"), omml_r("AM", normal=True))
        + omml_r(" = −log ", normal=True)
        + omml_frac(am_num, am_den)
    )
    add_omml_equation(
        doc,
        "Hàm mất mát Biên độ góc Cộng tính trên Siêu cầu (Additive Angular Margin Softmax)",
        eq_am,
        variables=[
            ("θ_y", "Góc giữa vector đặc trưng chuẩn hóa L2 của mẫu âm thanh và vector tâm chuẩn hóa của lớp đúng `y`."),
            ("θ_j", "Góc giữa vector đặc trưng của mẫu âm thanh và vector tâm của lớp đối lập `j ≠ y`."),
            ("m = 0.20", "Biên độ phạt góc cộng tính (`Additive Margin`): ở `v0.9.4`, `m` được nới hợp lý từ `0.35` về `0.20` để tạo vùng đệm phân tách vững chắc mà không ép quá gắt các giọng nam trầm tự nhiên ra khỏi nón đặc trưng `Bonafide`."),
            ("s = 30.0", "Hệ số phóng đại bán kính mặt cầu (`Scale Factor`), giúp đạo hàm hội tụ sắc nét và định hình dải điểm thô đầu ra khoảng `[-50, +50]`."),
        ],
    )

    add_heading_subsection(
        doc,
        "4.2.4 Giai đoạn 3: Hiệu chuẩn đầu phân loại `head_blend_a0.75` trên mô hình chính thức `v0.9.4`",
    )
    add_styled_paragraph(
        doc,
        "Khi mở rộng kho `OmniVoice CFM` lên đủ `6.445` tệp đối xứng 1:1 và huấn luyện Pha 2 trên tập `54.400` dòng (`am_s = 30.0`, `am_m = 0.20`), "
        "nhóm nghiên cứu phát hiện một hiện tượng hình học rất thú vị: thân mạng `SSL + AASIST` của Pha 2 đạt năng lực tách lớp nội tại cực tốt "
        "(`Dev EER = 5.95%`, đảo chiều `86.2%` các ca `OmniVoice` khó), nhưng các mẫu `CFM` có pha siêu mượt nằm sát ranh giới đã đẩy mặt phẳng đầu ra "
        "bị dịch lệch về phía âm (`negative classifier bias`), làm tăng tỷ lệ báo nhầm giọng thật tại ngưỡng cố định `θ = 0.0`.",
    )
    add_styled_paragraph(
        doc,
        "Nếu tiếp tục mở khóa tinh chỉnh cả khối `Wav2Vec 2.0`, mô hình sẽ đánh mất độ nhạy vừa học được trên `OmniVoice CFM`. "
        "Vì vậy, **Giai đoạn 3 (`Stage 3 Head-Calibration`)** giải quyết bài toán bằng phương pháp phẫu thuật chính xác: "
        "**đóng băng 100% thân trích xuất `SSL + AASIST`** của Pha 2, chỉ vi chỉnh nhẹ tầng phân loại đầu ra (`Head-Only`) đúng `1 epoch` trên tập cân bằng "
        "`train_v8_balanced_ft.csv` (`5.100` dòng, kiểm toán `0%` rò rỉ tập `Dev`, `Test`, `VieNeu-TTS` và `5` tình nguyện viên nghiệm thu), "
        "sau đó thực hiện **nội suy lồi không gian trọng số (`Convex Weight-Space Blending`)** với hệ số `α = 0.75`:",
    )

    eq_blend = (
        omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(v0.9.4)", normal=True))
        + omml_r(" = ", normal=True)
        + omml_delim(omml_r("1 − α", normal=True))
        + omml_r(" · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(P2)", normal=True))
        + omml_r(" + α · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(HeadOnly)", normal=True))
        + omml_r(" = 0.25 · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(P2)", normal=True))
        + omml_r(" + 0.75 · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(HeadOnly)", normal=True))
    )
    add_omml_equation(
        doc,
        "Nội suy tuyến tính trọng số đầu phân loại (Head-Calibration Convex Blend α = 0.75)",
        eq_blend,
        variables=[
            ("W_head^(P2)", "Trọng số đầu phân loại ngay sau Pha 2 trên `54.400` dòng — cực nhạy với giả mạo `CFM` nhưng hơi khắt khe với giọng thật."),
            ("W_head^(HeadOnly)", "Trọng số đầu phân loại sau 1 epoch hiệu chuẩn trên `5.100` dòng cân bằng khi giữ cố định 100% thân `SSL + AASIST`."),
            ("α = 0.75", "Hệ số pha trộn tối ưu tìm được trên tập kiểm soát: giữ 25% độ sắc biên của Pha 2 và 75% tâm cân bằng của Head-Only."),
            ("W_head^(v0.9.4)", "Trọng số đầu phân loại chính thức xuất bản tại `out/v0.9.4/best_model.pt` (`sha256: 30a383256458740e...`)."),
        ],
    )

    add_styled_table(
        doc,
        headers=[
            "Chặng Huấn Luyện v0.9.4",
            "Trạng Thái Khối SSL",
            "Tập Dữ Liệu & Quy Mô",
            "Siêu Tham Số Chính",
            "Vai Trò Toán Học Cốt Lõi",
        ],
        rows=[
            (
                "Pha 1: Warm-up Backend",
                "Đóng băng 100% (`freeze_ssl`)",
                "`54.400` dòng (`train_v8_f5_omni_with_spk1.csv`)",
                "`LR = 1e-4`, `1 epoch` (~34 phút)",
                "Làm ấm đồ thị `HS-GAL` trước để không gây sốc đạo hàm lên `Wav2Vec 2.0`",
            ),
            (
                "Pha 2: Joint Fine-Tuning",
                "Mở khóa phân tầng (`unfreeze_ssl`)",
                "`54.400` dòng + `RawBoost` + `Pitch Aug`",
                "`LR_SSL = 1e-6`, `LR_Back = 1e-5`, `AM-Softmax m=0.20`",
                "Khắc sâu dấu vết vi sai số ODE của `OmniVoice CFM` và pha `F5-TTS` (`Dev EER 5.95%`)",
            ),
            (
                "Giai đoạn 3: `head_blend_a0.75`",
                "Đóng băng 100% thân `SSL + AASIST`",
                "`5.100` dòng cân bằng (`0%` rò rỉ nghiệm thu)",
                "Head-Only `1 epoch` + nội suy lồi `α = 0.75`",
                "Khử hoàn toàn độ lệch biên âm tại `θ = 0.0`, đạt `5.63% EER` & chặn `95.01%` trên `15.980` mẫu Test",
            ),
        ],
        col_widths=[1.35, 1.25, 1.45, 1.30, 1.35],
        highlight_row_pred=lambda idx, _: idx == 2,
    )

    add_term_glossary(
        doc,
        [
            ("Catastrophic Forgetting", "Hiện tượng Quên thảm khốc", "Sự cố mạng tiền huấn luyện bị xóa nhòa kiến thức tiếng Việt gốc do cập nhật trọng số quá mạnh ở giai đoạn đầu tinh chỉnh."),
            ("Differential Learning Rate", "Tốc độ học phân tầng", "Kỹ thuật đặt tốc độ học rất nhỏ (`1e-6`) cho thân mạng tiền huấn luyện và lớn hơn (`1e-5` đến `1e-4`) cho các tầng đồ thị mới thêm vào."),
            ("Gradient Accumulation", "Tích lũy đạo hàm", "Kỹ thuật cộng dồn đạo hàm qua nhiều lô nhỏ (`batch_size = 8 × 2 bước = 16`) trước khi cập nhật trọng số, giúp huấn luyện mô hình lớn trên GPU 4GB VRAM."),
            ("Weighted Cross-Entropy", "Hàm mất mát Cross-Entropy có trọng số", "Biến thể của hàm mất mát phân loại nhân thêm hệ số phạt tỉ lệ nghịch với số mẫu mỗi lớp để xử lý mất cân bằng dữ liệu."),
            ("Double Penalty", "Lỗi Bù trừ kép", "Sai lầm kỹ thuật khi dùng chung bộ lấy mẫu lặp cân bằng với hàm mất mát có trọng số, làm nhân bình phương hệ số phạt và lệch biên quyết định."),
            ("AM-Softmax", "Additive Angular Margin Softmax", "Hàm mất mát chiếu đặc trưng lên mặt cầu đơn vị và chèn thêm khoảng đệm góc `m` nhằm gom chặt các mẫu cùng lớp và đẩy xa hai lớp Thật - Giả."),
            ("Head-Calibration", "Hiệu chuẩn đầu phân loại", "Quá trình cố định toàn bộ thân trích xuất đặc trưng và chỉ hiệu chỉnh tầng phân loại cuối cùng kết hợp nội suy trọng số (`head_blend_a0.75`) để căn chuẩn ngưỡng `θ = 0.0`."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 5: THUẬT TOÁN GỘP ĐA CỬA SỔ ĐỒNG THUẬN BẤT ĐỐI XỨNG
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 5",
        "Thuật Toán Gộp Đa Cửa Sổ Đồng Thuận Bất Đối Xứng (Multi-Window Consensus Asymmetric Veto)",
    )

    add_styled_paragraph(
        doc,
        "Trong điều kiện thực chiến trên Zalo và Telegram, một tin nhắn thoại lừa đảo hoặc tin nhắn của người thân thường kéo dài từ `5` đến `12` giây, "
        "trong khi đầu vào của khối `SSL-AASIST` cố định nghiêm ngặt ở `64.000` mẫu (`4.0 giây @ 16kHz`). Chương này trình bày giải thuật "
        "**Gộp Đa Cửa Sổ Đồng Thuận Bất Đối Xứng (`Multi-Window Consensus Asymmetric Veto`)** tại `src/preprocessing/pooling.py` — phát kiến kỹ thuật "
        "giúp giải quyết trọn vẹn nghịch lý đánh đổi giữa việc bảo vệ người thật ngập ngừng lấy hơi và việc chặn đứng giọng giả `OmniVoice CFM` có đuôi im lặng.",
    )

    # -------------------------------------------------------------------------
    # MỤC 5.1: TRÍCH XUẤT ĐA CỬA SỔ DÀY & MINI-BATCH MỘT LƯỢT
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "5.1 Trích Xuất Cửa Sổ Trượt Chồng Lấp Dày & Suy Luận Song Song Một Lượt (`pooling.py`)",
    )

    add_foundation_primer(
        doc,
        process_name="Trích Xuất Đa Cửa Sổ Trượt & Gộp Điểm Đồng Thuận Bất Đối Xứng",
        why_needed=(
            "Nếu chỉ cắt lấy `4.0 giây` đầu tiên của một đoạn ghi âm dài `8 giây`, hệ thống sẽ mù hoàn toàn trước phần nửa sau của câu nói. "
            "Ngược lại, khi chia đoạn ghi âm thành `5` cửa sổ trượt để chấm điểm, hai phép gộp kinh điển đều bộc lộ điểm yếu chí tử: "
            "**`Max-Pooling` thuần túy** quá cả tin (chỉ cần 1 cửa sổ cuối câu của giọng giả `CFM` rơi vào khoảng lặng được chấm điểm dương nhẹ là cả tệp giả mạo lọt lưới), "
            "còn **`Mean-Pooling` thuần túy** lại quá khắt khe (người thật chỉ cần hắng giọng lấy hơi ở 1 giây đầu bị điểm âm sâu là kéo tụt trung bình cộng của cả câu nói thật)."
        ),
        real_analogy=(
            "Hãy hình dung **Hội đồng Giám khảo 5 người** cùng nghe 5 lát cắt chồng lấp của một đoạn ghi âm:\n"
            "• Nếu theo luật **`Max` dễ dãi** (chỉ cần 1 người bảo Thật là cho qua): kẻ gian ghép 1 giây im lặng cuối câu đánh lừa giám khảo số 5 chấm `+8.1`, thế là giọng giả thoát tội!\n"
            "• Nếu theo luật **`Mean` cào bằng** (lấy trung bình cộng cả 5 người): bác lớn tuổi nói thật nhưng giây đầu lấy hơi bị giám khảo số 1 chấm `-18.5`, kéo tụt điểm của 4 giám khảo khen thật phía sau!\n"
            "• Luật **`Consensus Asymmetric Veto` (Đồng thuận Phủ quyết Bất đối xứng)**: Khi có giám khảo phát hiện dấu vết giả mạo cực nặng (`< -12.0`), hội đồng hỏi ngay: "
            "*\"Có ít nhất 2 giám khảo độc lập cùng khẳng định giọng người thật rõ nét (`≥ +6.0`) hay không?\"*. Nếu **CÓ** (người thật chỉ lấy hơi đầu câu), bảo vệ người thật bằng phiếu cao thứ nhì; "
            "nếu **KHÔNG** (giọng giả `CFM` chỉ ăn may ở 1 đoạn lặng cuối), bác bỏ ngay phiếu dương lẻ loi đó và lấy trung bình cắt ngọn của các phiếu còn lại để chặn đứng kẻ lừa đảo!"
        ),
        core_points=[
            "**Cửa sổ trượt (`Sliding Window = 4.0s`) & Bước nhảy (`Hop Size = 1.0s`)**: Mỗi cửa sổ dài `64.000` mẫu dịch chuyển từng bước `16.000` mẫu, tạo độ chồng lấp `75%` (`3.0 giây`) để mọi âm tiết chuyển tiếp đều nằm trọn ở vùng trung tâm của ít nhất một cửa sổ.",
            "**Cắt chồng lấp dày (`Dense Overlap Slicing`)**: Các đoạn thoại sát biên `3.125s – 4.0s` (`≥ 50.000` mẫu) được nối lặp chu kỳ (`Repeat Padding`) để luôn trích xuất tối thiểu `2` cửa sổ lệch pha nhau `0.5 giây` (`8.000` mẫu), không để bộ phủ quyết bị mất tác dụng trên câu ngắn.",
            "**Suy luận song song 1 lượt (`Single Batched Forward Pass`)**: Gom cả `K` cửa sổ (`1 ≤ K ≤ 5`) thành một ma trận duy nhất `(K, 64000)` để GPU/CPU tính toán trong đúng **1 lần truyền thẳng**, giữ độ trễ gần như không đổi so với chạy 1 cửa sổ.",
            "**Thống kê thứ tự (`Order Statistics`) & Trung bình cắt ngọn (`Trimmed Mean`)**: Sắp xếp các điểm cửa sổ từ nhỏ nhất đến lớn nhất `s_(1) ≤ s_(2) ≤ … ≤ s_(K)` để kiểm tra đồng thuận của phần tử lớn thứ nhì `s_(K−1)` hoặc cắt bỏ phần tử ngoại lai `s_(K)`.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Module `src/preprocessing/pooling.py` triển khai quy trình trích xuất và suy luận đa cửa sổ thông qua 3 hàm cốt lõi tuân thủ nghiêm ngặt các `STUBBORN_FACT` của dự án:",
    )
    add_bullet_item(
        doc,
        "Với tín hiệu dài từ `64.000` mẫu trở lên, cửa sổ độ dài `win = 64.000` trượt theo bước `hop = 16.000` mẫu; nếu cửa sổ cuối chưa chạm sát mẫu tận cùng, "
        "hệ thống tự động bổ sung cửa sổ đuôi `t[-64000:]` để không bỏ sót giây cuối cùng. Với tín hiệu ngắn hơn `64.000` mẫu, hệ thống dùng `torch.tile` nối lặp "
        "(`Repeat Padding`, tuyệt đối cấm `Zero-padding`). Đặc biệt khi bật `dense_slicing = True`, mọi đoạn thoại có độ dài `≥ 50.000` mẫu (`~3.125 giây`) "
        "đều được đảm bảo sinh tối thiểu `2` cửa sổ lệch pha `8.000` mẫu.",
        bold_prefix="1. Hàm `sliding_windows(x, win=64000, hop=16000, dense_slicing=True)`",
    )
    add_bullet_item(
        doc,
        "Khi đoạn ghi âm rất dài sinh ra nhiều hơn `5` cửa sổ, hàm dùng `np.linspace(0, len - 1, 5, dtype=int)` chọn đều `K = 5` cửa sổ đại diện trải từ đầu đến cuối tệp "
        "nhằm khóa cứng trần thời gian phản hồi `NFR-1 ≤ 3.0 giây`. Ngoài ra, tham số nhiễu nền vi mô `apply_comfort_dither` (`noise_std = 0.0035`, `seed = 42`) "
        "được cô lập chặt chẽ: chỉ bật riêng cho luồng thu trực tiếp từ micro trình duyệt WebRTC để bù hiện tượng cắt nền im lặng nhân tạo, và **khóa cứng `apply_dither = False`** "
        "trên mọi tệp tải lên cũng như luồng kiểm định clone nhằm giữ nguyên vẹn dấu vết pha của `OmniVoice CFM`.",
        bold_prefix="2. Hàm `extract_window_batch(..., max_windows=5, apply_dither=False)`",
    )
    add_bullet_item(
        doc,
        "Nghiêm cấm chạy vòng lặp `for` gọi mô hình tuần tự `K` lần! Toàn bộ tensor `(K, 64000)` được đẩy qua `model.score(batch_dev)` dưới ngữ cảnh "
        "`torch.inference_mode()` trong **một lượt truyền thẳng duy nhất**. Nhờ đó, độ trễ suy luận trên GPU chỉ đạt trung vị **`66.3 ms`**, "
        "đo chuẩn API 30 lần liên tiếp đạt trung vị **`1.101 giây`** và nhật ký thực tế `140` lượt chạy cục bộ đạt trung vị **`0.705 giây`**.",
        bold_prefix="3. Hàm `batch_window_forward(model, windows_batch, device)`",
    )

    add_term_glossary(
        doc,
        [
            ("Sliding Window", "Cửa sổ trượt", "Kỹ thuật dùng một khung độ dài cố định (`4.0 giây = 64.000 mẫu`) dịch chuyển dọc theo đoạn âm thanh dài để quét hết toàn bộ nội dung."),
            ("Hop Size", "Bước nhảy cửa sổ", "Khoảng cách dịch chuyển giữa hai cửa sổ liên tiếp (`1.0 giây = 16.000 mẫu`), tạo mức gối đầu 75% giữa hai cửa sổ kề nhau."),
            ("Dense Overlap Slicing", "Cắt chồng lấp dày sát biên", "Cơ chế đảm bảo các đoạn thoại dài từ `3.125 giây` trở lên luôn tạo ra ít nhất `2` cửa sổ lệch pha để kiểm tra tính đồng thuận."),
            ("Mini-batch Tensor", "Khối ma trận lô nhỏ", "Ma trận gộp nhiều cửa sổ âm thanh thành kích thước `(K, 64000)` để phần cứng tính toán song song cùng một lúc."),
            ("Single Batched Forward Pass", "Truyền thẳng gộp lô một lượt", "Chạy mạng nơ-ron đúng 1 lần cho toàn bộ `K` cửa sổ thay vì chạy lặp `K` lần nối tiếp, giúp tiết kiệm tối đa độ trễ."),
            ("Comfort Dither", "Nhiễu nền êm vi mô", "Lớp nhiễu Gauss biên độ cực nhỏ (`σ = 0.0035`) chỉ dùng cho micro trình duyệt để khôi phục nền phòng tự nhiên bị bộ lọc WebRTC cắt mất."),
        ],
    )

    # -------------------------------------------------------------------------
    # MỤC 5.2: TOÁN HỌC CONSENSUS ASYMMETRIC VETO & BẢNG ABLATION 15.980 CLIPS
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "5.2 Công Thức Toán Học Của Consensus Asymmetric Veto & Đối Chứng Thực Nghiệm Trên 15.980 Mẫu",
    )

    add_styled_paragraph(
        doc,
        "Giả sử sau lượt truyền thẳng song song, đoạn thoại gồm `K` cửa sổ (`1 ≤ K ≤ 5`) cho ra vector điểm thô `s = [s_1, s_2, …, s_K]`. "
        "Ta sắp xếp mảng điểm này theo thứ tự không giảm: `s_(1) ≤ s_(2) ≤ … ≤ s_(K-1) ≤ s_(K)`, trong đó `s_(1) = min(s)` là cửa sổ đáng ngờ nhất, "
        "`s_(K) = max(s)` là cửa sổ có điểm thật cao nhất, và `s_(K-1)` (`sorted_s[-2]`) là cửa sổ có điểm thật cao thứ nhì. "
        "Hàm `pool_scores(scores, mode='asymmetric_veto')` ra quyết định theo ba nhánh phân loại chặt chẽ:",
    )

    add_bullet_item(
        doc,
        "Nếu `s_(1) ≥ −12.0` (không có bất kỳ cửa sổ nào chứa bằng chứng giả mạo sâu): hệ thống tin tưởng bảo vệ giọng người thật bằng phép lấy cực đại "
        "`s_veto = s_(K) = max(s)`, loại bỏ hoàn toàn ảnh hưởng của các cửa sổ hơi yếu nhẹ đầu hoặc cuối câu.",
        bold_prefix="Nhánh 1 — Không có dị thường giả mạo sâu (`s_(1) ≥ −12.0`)",
    )
    add_bullet_item(
        doc,
        "Nếu `s_(1) < −12.0` (xuất hiện ít nhất 1 cửa sổ nghi giả rất mạnh) **VÀ** `K ≥ 3` **VÀ** `s_(K-1) ≥ +6.0`: điều này chứng minh có **ít nhất 2 cửa sổ độc lập** "
        "(`s_(K-1)` và `s_(K)`) cùng mang đặc trưng sinh trắc người thật rõ rệt, tức cửa sổ âm sâu `s_(1)` chỉ là tiếng lấy hơi, ho nhẹ hoặc chạm micro đầu câu. "
        "Hệ thống kích hoạt cơ chế **Giải cứu Đồng thuận (`Consensus Rescue`)**, trả về `s_veto = s_(K-1) ≥ +6.0` để bảo vệ an toàn cho người nói thật.",
        bold_prefix="Nhánh 2 — Có đồng thuận người thật đa cửa sổ (`K ≥ 3`, `s_(1) < −12.0`, `s_(K-1) ≥ +6.0`)",
    )
    add_bullet_item(
        doc,
        "Nếu `s_(1) < −12.0` **NHƯNG** không đạt đồng thuận người thật (`s_(K-1) < +6.0` khi `K ≥ 3`): đây chính xác là chân dung toán học của một cuộc tấn công "
        "`OmniVoice CFM` hoặc cắt ghép giọng giả — phần lớn các cửa sổ có tiếng nói đều bị chấm âm, chỉ duy nhất `1` cửa sổ rơi vào khoảng nghỉ vô thanh cuối câu "
        "vọt lên điểm dương giả tạo `s_(K) > 0`. Hệ thống lập tức **Phủ quyết (`Veto`)** bằng cách vứt bỏ cửa sổ ngoại lai cao nhất `s_(K)` và tính **Trung bình cắt ngọn (`Trimmed Mean`)** "
        "trên `K − 1` cửa sổ còn lại (hoặc trung bình cộng `2` cửa sổ nếu `K = 2`).",
        bold_prefix="Nhánh 3 — Phủ quyết chặn giả mạo bằng Trimmed Mean (`s_(1) < −12.0`, `s_(K-1) < +6.0`)",
    )

    eq_veto = (
        omml_sub(omml_r("s"), omml_r("veto", normal=True))
        + omml_r(" = ", normal=True)
        + omml_delim(
            omml_sub(omml_r("s"), omml_r("(K−1)", normal=True))
            + omml_r("  [khi s_(1) < −12, s_(K−1) ≥ +6] ;   ", normal=True)
            + omml_frac(omml_r("1", normal=True), omml_r("K − 1"))
            + omml_subsup(omml_r("∑", normal=True), omml_r("i=1", normal=True), omml_r("K−1"))
            + omml_sub(omml_r("s"), omml_r("(i)", normal=True))
            + omml_r("  [khi s_(1) < −12, s_(K−1) < +6] ;   ", normal=True)
            + omml_sub(omml_r("s"), omml_r("(K)", normal=True))
            + omml_r("  [khi s_(1) ≥ −12]", normal=True),
            "{",
            "}",
        )
    )
    add_omml_equation(
        doc,
        "Hàm gộp điểm Đa cửa sổ Đồng thuận Bất đối xứng (Consensus Asymmetric Veto với K ≥ 3)",
        eq_veto,
        variables=[
            ("s_(1) ≤ s_(2) ≤ … ≤ s_(K)", "Dãy điểm thô của `K` cửa sổ trượt (`3 ≤ K ≤ 5`) sau khi sắp xếp tăng dần; trường hợp `K = 2` và `s_(1) < −12.0` lấy trung bình cộng `(s_(1) + s_(2)) / 2`."),
            ("τ_veto = −12.0", "Ngưỡng phát hiện bằng chứng giả mạo mạnh trên cửa sổ thấp nhất `s_(1)` để kích hoạt kiểm tra đồng thuận."),
            ("τ_cons = +6.0", "Ngưỡng xác nhận đồng thuận giọng người thật trên cửa sổ cao thứ nhì `s_(K−1)` (đảm bảo ít nhất 2 cửa sổ độc lập cùng xác nhận thật)."),
            ("1/(K−1) ∑ s_(i)", "Trung bình cắt ngọn (`Trimmed Mean`) loại bỏ đúng 1 cửa sổ cao nhất `s_(K)` để triệt tiêu đoạn lặng dương giả ở cuối tệp deepfake."),
        ],
    )

    if figs and "fig5" in figs:
        add_figure(
            doc,
            figs["fig5"],
            "Hình 5.1: Minh họa trực quan hai tình huống đối lập được giải quyết trọn vẹn bởi Consensus Asymmetric Veto: (Trái) Bảo vệ người thật có nhịp nghỉ lấy hơi đầu câu; (Phải) Chặn đứng giọng giả CFM có đoạn im lặng cuối câu.",
        )

    add_styled_paragraph(
        doc,
        "Bảng dưới đây trình bày kết quả thực nghiệm đối chứng (Ablation Study) giữa 3 cơ chế gộp điểm của mô hình chính thức **ViTrueVoice v0.9.4 (`head_blend_a0.75`)** "
        "trên toàn bộ tập kiểm thử độc lập `test_indomain_v8_f5_omni.csv` (`15.980` mẫu), tập ngoại lai `Unseen VieNeu-TTS` (`955` mẫu), "
        "tập ca khó `Gate 4 OmniVoice Reversal` (`195` mẫu) và bộ nghiệm thu sạch `5` tình nguyện viên (`84` mẫu):",
    )

    add_styled_table(
        doc,
        headers=[
            "Chế Độ Gộp Đa Cửa Sổ",
            "Test 15.980: Tổng EER",
            "Test 15.980: Tỷ Lệ Chặn Spoof",
            "Test 15.980: BPCER @ θ=0",
            "Chặn OmniVoice CFM (Test)",
            "Gate 2 Clean 5 SPK (84 mẫu)",
            "Gate 4 Đảo Chiều Ca Khó (195)",
        ],
        rows=[
            (
                "Max-Pooling thuần (`max`)",
                "8.33%",
                "88.24% (1.981/2.245)",
                "5.34% (Dev: 4.85%)",
                "78.75% (EER 11.61%)",
                "98.81% (83/84) — 4 SPK: 100%",
                "60.51% (118/195)",
            ),
            (
                "Mean-Pooling thuần (`mean`)",
                "6.24%",
                "96.17% (2.159/2.245)",
                "8.80% (Dev: 8.10%)",
                "93.66% (EER 7.77%)",
                "91.67% (77/84) — Bị rớt người thật",
                "74.36% (145/195)",
            ),
            (
                "Consensus Asymmetric Veto (Chuẩn v0.9.4)",
                "5.63% (Tốt nhất)",
                "95.01% (2.133/2.245)",
                "6.73% (Dev: 6.00%)",
                "91.52% (EER 7.95%)",
                "95.24% (80/84) — 4 SPK: 100%",
                "72.82% (142/195)",
            ),
        ],
        col_widths=[1.25, 0.85, 1.05, 0.90, 0.95, 0.95, 0.75],
        highlight_row_pred=lambda idx, _: idx == 2,
    )

    add_callout_box(
        doc,
        "Bảng đối chứng trên `15.980` mẫu Test chứng minh tính ưu việt toán học của **`Consensus Asymmetric Veto`**: "
        "So với `Max-Pooling` cũ, thuật toán kéo giảm sai số `EER` toàn cục một cú nhảy vọt từ **`8.33%` xuống chỉ còn `5.63%`**, "
        "nâng tỷ lệ chặn đứng `OmniVoice CFM` từ `78.75%` lên **`91.52%`** (chặn thêm `152` cuộc tấn công deepfake nguy hiểm!), "
        "đồng thời vẫn giữ trọn vẹn **`100.0% (64/64)`** tỷ lệ nhận đúng trên 4 tình nguyện viên đối chứng chính (`SPK_0004..0007`) và **`95.24% (80/84)`** trên cả 5 người nói nghiệm thu.",
        title="Ý NGHĨA BẢO VỆ TRƯỚC HỘI ĐỒNG CỦA BẢNG ĐỐI CHỨNG ABLATION POOLING",
    )

    add_term_glossary(
        doc,
        [
            ("Max-Pooling", "Phép gộp cực đại", "Chọn điểm số cao nhất trong các cửa sổ làm điểm chung cuộc; rất ưu ái giọng người thật nhưng dễ bị lọt lưới nếu tệp giả mạo có 1 đoạn lặng cuối câu."),
            ("Mean-Pooling", "Phép gộp trung bình cộng", "Lấy trung bình số học của tất cả cửa sổ; bắt giả mạo gắt nhưng dễ báo nhầm oan khi người thật ngập ngừng hoặc lấy hơi đầu câu."),
            ("Trimmed Mean", "Trung bình cắt ngọn", "Phép tính trung bình sau khi đã loại bỏ giá trị cực đoan ở đầu mút (`s_(K)`), giúp khử nhiễu ngoại lai vô thanh một cách vững chắc."),
            ("Consensus Asymmetric Veto", "Đồng thuận Phủ quyết Bất đối xứng", "Thuật toán gộp điểm chính thức của `ViTrueVoice v0.9.4`: kết hợp kiểm tra đồng thuận ít nhất 2 cửa sổ giọng thật (`s_(K−1) ≥ +6.0`) với phép phủ quyết cắt ngọn khi có cửa sổ nghi giả sâu (`s_(1) < −12.0`)."),
            ("Outlier", "Điểm ngoại lai", "Một cửa sổ có điểm số lệch hẳn khỏi xu hướng chung của cả đoạn thoại (ví dụ tiếng hắng giọng đầu câu của người thật hoặc khoảng lặng cuối câu của giọng giả)."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 6: HIỆU CHUẨN PLATT SCALING, VÙNG BIÊN & HÀNG RÀO GIÁM ĐỊNH SỐ NIST
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 6",
        "Hiệu Chuẩn Xác Suất Platt Scaling, Vùng Cảnh Báo Biên & Hàng Rào Giám Định Số Chuẩn NIST",
    )

    add_styled_paragraph(
        doc,
        "Một hệ thống phòng chống lừa đảo phục vụ phụ huynh, người cao tuổi và hỗ trợ giám định kỹ thuật số không thể chỉ trả về con số logit khô khan "
        "như `-16.4` hay `+14.1`, càng không được phép hiển thị những con số phần trăm tự tin ảo `99.99%` khi điểm số thực chất nằm sát ranh giới nghi vấn. "
        "Chương này giải thích chi tiết cơ chế hiệu chuẩn xác suất thực nghiệm tại `src/app/decision.py`, quy tắc vùng cảnh báo biên (`Borderline Zone`) "
        "và hai hàng rào bảo vệ chuẩn pháp y quốc tế `NIST`.",
    )

    # -------------------------------------------------------------------------
    # MỤC 6.1: HIỆU CHUẨN PLATT SCALING / TEMPERATURE SCALING & KẸP CHUẨN NIST
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "6.1 Hiệu Chuẩn Xác Suất Platt Scaling / Temperature Scaling (`T = 16.0`) & Kẹp Chuẩn Pháp Y NIST",
    )

    add_foundation_primer(
        doc,
        process_name="Hiệu Chuẩn Xác Suất Thực Nghiệm & Hàng Rào Chống Quá Tự Tin",
        why_needed=(
            "Do mô hình được huấn luyện với hàm mất mát siêu cầu `AM-Softmax` có hệ số phóng đại `s = 30.0`, điểm thô `s` trải rộng trên dải `[-50, +50]`. "
            "Nếu đưa thẳng điểm `s = +5.0` vào hàm `Sigmoid` cổ điển `1 / (1 + exp(-s))`, máy tính sẽ báo ngay độ tin cậy **`99.33%`** — trong khi ở thang `[-50, +50]`, "
            "mức `+5.0` chỉ mới nhỉnh nhẹ qua vạch `0` và vẫn tiềm ẩn rủi ro nhầm lẫn! Ta bắt buộc phải hiệu chuẩn lại độ dốc xác suất để con số phần trăm phản ánh trung thực mức độ chắc chắn thực tế."
        ),
        real_analogy=(
            "Giống như **một chiếc đồng hồ đo tốc độ bị lắp sai bánh răng**: xe mới chạy `25 km/h` trong hẻm mà kim đồng hồ đã vọt kịch trần `200 km/h`! "
            "**Hiệu chuẩn `Platt / Temperature Scaling` (`T = 16.0`)** chính là việc lắp lại bộ chia tỷ lệ chuẩn xác dựa trên tập thẩm định độc lập `Dev` để kim đồng hồ "
            "lên đều đặn theo đúng vận tốc thật. Còn **hàng rào kẹp `[0.1%, 99.9%]` chuẩn `NIST`** giống như nguyên tắc vàng của phòng giám định pháp y: "
            "không bao giờ đóng dấu khẳng định tuyệt đối `100.0%` hay `0.0%` trước tòa án vì luôn tồn tại sai số vật lý của micro và đường truyền."
        ),
        core_points=[
            "**Điểm thô (`Raw Score s`) so với Xác suất hiệu chuẩn (`Calibrated Probability`)**: Điểm thô chỉ mang tính chất xếp hạng xa - gần so với mặt phẳng phân chia, chỉ sau khi qua hàm hiệu chuẩn mới trở thành thước đo độ tin cậy phần trăm có ý nghĩa thống kê.",
            "**Hiện tượng Quá tự tin (`Overconfidence`)**: Bệnh kinh niên của các mạng học sâu hiện đại khi bão hòa hàm `Sigmoid` quá sớm, biến mọi dự đoán lấp lửng thành `99.9%`.",
            "**Hiệu chuẩn nhiệt độ / hồi quy Platt (`Temperature / Platt Scaling`)**: Chia khoảng cách `(s − θ)` cho hằng số nhiệt độ `T = 16.0` (tương đương hệ số độ dốc `PLATT_SCALE_K = 1 / 16.0 = 0.0625`), kéo giãn mượt đường cong xác suất khớp với dải logit `[-50, +50]` mà tuyệt đối không chạm vào dữ liệu `Test` hay `5 SPK` nghiệm thu.",
            "**Chiết khấu bất định đa cửa sổ (`Multi-Window Variance Penalty`)**: Nếu các cửa sổ trong cùng một tệp âm thanh bất đồng ý kiến mạnh (độ lệch chuẩn `σ_win > 6.0`), hệ thống tự động trừ bớt độ tin cậy để cảnh báo người dùng thận trọng.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Trong `src/app/decision.py`, hàm `platt_calibrator` tính xác suất hậu nghiệm của lớp Giọng Thật dựa trên khoảng cách từ điểm gộp `s` "
        "đến ngưỡng quyết định `θ = 0.0` thông qua hằng số nhiệt độ `T_CALIB = 16.0` (`PLATT_SCALE_K = 0.0625`):",
    )

    eq_platt = (
        omml_r("P")
        + omml_delim(omml_r("Bonafide | s", normal=True))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("1", normal=True),
            omml_r("1 + ", normal=True)
            + omml_sup(
                omml_r("e"),
                omml_r("−", normal=True) + omml_frac(omml_r("s − θ"), omml_r("T")),
            ),
        )
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("1", normal=True),
            omml_r("1 + ", normal=True)
            + omml_sup(omml_r("e"), omml_r("−", normal=True) + omml_r("k") + omml_delim(omml_r("s − θ"))),
        )
    )
    add_omml_equation(
        doc,
        "Hàm hiệu chuẩn xác suất Logistic Platt / Temperature Scaling trên dải AM-Softmax",
        eq_platt,
        variables=[
            ("s", "Điểm thô của đoạn thoại sau khi gộp đa cửa sổ `Consensus Asymmetric Veto` (`s = z_bonafide − z_spoof`)."),
            ("θ = 0.0", "Ngưỡng quyết định chuẩn được khóa cố định trên toàn bộ API, Web UI và Telegram Bot."),
            ("T = 16.0", "Tham số nhiệt độ hiệu chuẩn (`T_CALIB = 16.0`), được xác lập trên phân phối tập `Dev` độc lập để khử triệt để hiện tượng bão hòa sớm."),
            ("k = 1 / T = 0.0625", "Hệ số độ dốc hiệu dụng (`PLATT_SCALE_K = 0.0625`); xác suất lớp Giọng Giả đối xứng là `P(Spoof | s) = 1 − P(Bonafide | s)`."),
        ],
    )

    add_styled_paragraph(
        doc,
        "Để xử lý trường hợp đoạn âm thanh bị cắt ghép cục bộ khiến điểm số giữa các cửa sổ dao động dữ dội, `platt_calibrator` tích hợp thêm "
        "**chiết khấu phương sai đa cửa sổ**: khi độ lệch chuẩn giữa các cửa sổ `σ_win > 6.0`, độ tin cậy của nhãn dự đoán bị trừ một lượng "
        "`0.02 × (σ_win − 6.0)` (không thấp hơn `50.0%`). Cuối cùng, tuân thủ tiêu chuẩn báo cáo giám định kỹ thuật số của Viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ (`NIST`), "
        "mọi xác suất hiển thị trên giao diện đều đi qua phép kẹp cứng hai đầu:",
    )

    eq_nist = (
        omml_sub(omml_r("P"), omml_r("NIST", normal=True))
        + omml_r(" = clip", normal=True)
        + omml_delim(
            omml_r("100 · P", normal=True)
            + omml_delim(omml_r("Bonafide | s", normal=True))
            + omml_r(" ,  0.1% ,  99.9%", normal=True)
        )
    )
    add_omml_equation(
        doc,
        "Hàng rào kẹp xác suất chuẩn Giám định Pháp y Kỹ thuật số NIST",
        eq_nist,
        variables=[
            ("P(Bonafide | s)", "Xác suất hậu nghiệm sau hiệu chuẩn nhiệt độ và chiết khấu bất định đa cửa sổ."),
            ("0.1%, 99.9%", "Cận dưới và cận trên bắt buộc theo nguyên lý bất định pháp y: hệ thống tuyệt đối không bao giờ tuyên bố độ chắc chắn tuyệt đối `0.0%` hoặc `100.0%`."),
            ("P_NIST", "Phần trăm xác suất hiển thị minh bạch trên đồng hồ đo giao diện Web Forensics và tin nhắn cảnh báo Telegram Bot."),
        ],
    )

    add_styled_paragraph(
        doc,
        "Sự khác biệt một trời một vực giữa hàm `Sigmoid` thô chưa hiệu chuẩn và `Platt / Temperature Scaling (T = 16.0)` được thể hiện rõ qua các mốc điểm thực tế: "
        "tại `s = +5.0`, Sigmoid thô báo ảo `99.3%` trong khi hệ thống đã hiệu chuẩn chỉ báo thận trọng **`57.8%`** (nằm trong vùng cảnh báo biên); "
        "tại `s = +16.0`, xác suất đạt **`73.1%`**; tại `s = +32.0`, xác suất đạt **`88.1%`**; và chỉ những mẫu cực kỳ rõ ràng (`|s| ≥ 40.0`) mới vượt trên **`92.4% – 99.9%`**.",
    )

    if figs and "fig6" in figs:
        add_figure(
            doc,
            figs["fig6"],
            "Hình 6.1: Đối chiếu đường cong Sigmoid thô bị bão hòa giả tạo với đường cong hiệu chuẩn Platt Scaling, vùng cảnh báo biên (|s| ≤ 8.0) và ngưỡng kẹp chuẩn NIST [0.1%, 99.9%].",
        )

    add_term_glossary(
        doc,
        [
            ("Logit", "Điểm tuyến tính thô chưa chuẩn hóa", "Giá trị số thực đầu ra trực tiếp của tầng mạng cuối cùng (`[-50, +50]`), chưa phải là xác suất phần trăm."),
            ("Sigmoid", "Hàm ánh xạ chữ S tiêu chuẩn", "Công thức toán học `1 / (1 + e^(-x))` nén trục số thực về đoạn `(0, 1)` nhưng gây bão hòa cực đoan nếu đầu vào có biên độ lớn."),
            ("Overconfidence", "Hiện tượng Quá tự tin", "Tình trạng mô hình AI hiển thị độ tin cậy `99.9%` ngay cả ở những mẫu mập mờ gần ranh giới phân lớp."),
            ("Calibration", "Hiệu chuẩn xác suất", "Kỹ thuật điều chỉnh đầu ra của mô hình sao cho khi hệ thống báo tin cậy `80%`, thì trong thực tế đúng xấp xỉ 8 trên 10 trường hợp là chính xác."),
            ("Platt / Temperature Scaling", "Hiệu chuẩn hồi quy Logistic / Nhiệt độ", "Phương pháp chia logit cho hằng số nhiệt độ `T = 16.0` tối ưu trên tập `Dev` để làm dịu độ dốc xác suất."),
            ("NIST", "National Institute of Standards and Technology", "Viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ — cơ quan ban hành các chuẩn mực đánh giá sinh trắc học (ASV/minDCF) và nguyên tắc báo cáo giám định pháp y số."),
        ],
    )

    # -------------------------------------------------------------------------
    # MỤC 6.2: VÙNG CẢNH BÁO BIÊN & HÀNG RÀO IQR KHI ENROLLMENT
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "6.2 Phân Tầng 3 Vùng Quyết Định (`Borderline Zone`) & Hàng Rào Thống Kê IQR Chống Thao Túng Ngưỡng",
    )

    add_styled_paragraph(
        doc,
        "Trong thực tế phòng chống tội phạm lừa đảo tài chính, một quyết định cắt đôi cứng nhắc Trắng - Đen tại `θ = 0.0` vẫn chưa đủ an toàn "
        "khi người dùng gửi một đoạn thoại quá ồn, thu qua loa ngoài rè hoặc đường truyền 2G mất sóng. Vì vậy, hàm `classify_score` trong `src/app/decision.py` "
        "thiết lập hằng số `BORDERLINE_THRESHOLD = 8.0`, chia không gian điểm thành **3 vùng hành động thực tiễn** rõ ràng:",
    )

    add_styled_table(
        doc,
        headers=[
            "Phân Vùng Quyết Định",
            "Miền Điểm Thô `s` (tại θ = 0)",
            "Độ Tin Cậy Hiệu Chuẩn",
            "Nhãn Trạng Thái Hệ Thống",
            "Khuyến Nghị Hành Động Bảo Vệ Người Dùng",
        ],
        rows=[
            (
                "1. Giả Mạo Rõ Ràng (`Spoof`)",
                "`s < −8.0`",
                "`62.2% – 99.9%` nghiêng về Giả mạo",
                "`SPOOF` (`NORMAL` — Cảnh báo Đỏ)",
                "Chặn khẩn cấp: Tuyệt đối KHÔNG chuyển tiền, KHÔNG đọc mã OTP; cúp máy ngay lập tức.",
            ),
            (
                "2. Vùng Cảnh Báo Biên (`Borderline Zone`)",
                "`−8.0 ≤ s ≤ +8.0` (`|s − θ| ≤ 8.0`)",
                "`50.0% – 62.2%` (Độ bất định cao)",
                "`is_borderline = True` (`BORDERLINE` — Cảnh báo Hổ phách)",
                "Tạm dừng giao dịch! Bắt buộc xác minh kênh phụ (`Out-of-Band`): tự bấm số gọi lại cho người thân hoặc hỏi câu hỏi bí mật gia đình.",
            ),
            (
                "3. Người Thật Rõ Ràng (`Bonafide`)",
                "`s > +8.0`",
                "`62.2% – 99.9%` nghiêng về Người thật",
                "`BONA_FIDE` (`NORMAL` — Xác nhận Xanh)",
                "Giọng nói mang cấu trúc sinh học tự nhiên ổn định; vẫn giữ nguyên tắc an toàn tài chính khi giao dịch số tiền lớn.",
            ),
        ],
        col_widths=[1.30, 1.15, 1.15, 1.35, 1.75],
        highlight_row_pred=lambda idx, _: idx == 1,
    )

    add_styled_paragraph(
        doc,
        "Ngoài ra, hệ thống còn cung cấp hàm hiệu chỉnh ngưỡng cá nhân hóa `calibrate_by_enrollment` dành cho kịch bản người dùng đăng ký trước tối thiểu "
        "`3` mẫu giọng thật (`enroll_scores`). Một nguy cơ bảo mật nghiêm trọng ở đây là **tấn công đầu độc mẫu đăng ký (`Enrollment Poisoning`)** "
        "hoặc tệp ghi âm đăng ký bị hỏng nặng: nếu kẻ tấn công chèn mẫu nhiễu làm điểm trung vị đăng ký tụt sâu xuống `-45.0`, việc tự động dời ngưỡng xuống theo "
        "sẽ mở toang cánh cửa cho mọi tệp deepfake lọt qua! Để khóa chặt lỗ hổng này, ViTrueVoice thiết lập **Hàng rào ngoại lai khoảng tứ phân vị (`IQR Outlier Guardrail`)**:",
    )

    eq_iqr = (
        omml_delim(omml_sub(omml_r("Δ"), omml_r("offset", normal=True)), "|", "|")
        + omml_r(" = ", normal=True)
        + omml_delim(
            omml_sub(omml_r("m"), omml_r("enroll", normal=True))
            + omml_r(" − ", normal=True)
            + omml_sub(omml_r("m"), omml_r("dev", normal=True)),
            "|",
            "|",
        )
        + omml_r(" > 4 · IQR ,    IQR = ", normal=True)
        + omml_sub(omml_r("Q"), omml_r("3", normal=True))
        + omml_r(" − ", normal=True)
        + omml_sub(omml_r("Q"), omml_r("1", normal=True))
    )
    add_omml_equation(
        doc,
        "Điều kiện kích hoạt Hàng rào từ chối dịch ngưỡng tự động (Enrollment IQR Outlier Guardrail)",
        eq_iqr,
        variables=[
            ("m_enroll", "Trung vị (`Median`) điểm số của các mẫu giọng đăng ký từ người dùng (bắt buộc tối thiểu `≥ 3` mẫu hợp lệ)."),
            ("m_dev", "Trung vị điểm số giọng thật chuẩn trên tập thẩm định độc lập `Dev`."),
            ("Q_1, Q_3, IQR", "Phân vị thứ 25 (`Q_1`), phân vị thứ 75 (`Q_3`) và khoảng tứ phân vị `IQR = Q_3 − Q_1` của tập `Dev` — đại lượng thống kê bền vững không bị méo bởi ngoại lai."),
            ("4 · IQR", "Ngưỡng an toàn tối đa (`max_iqr_factor = 4.0`): ngay khi độ lệch `|Δ_offset|` vượt quá `4 · IQR`, hàm lập tức đặt `calibrated = False`, từ chối dời ngưỡng tự động, giữ nguyên điểm thô gốc và chuyển sang quy trình kiểm tra thủ công."),
        ],
    )

    add_callout_box(
        doc,
        "Khi Hội đồng hỏi: *\"Tại sao giao diện của em không bao giờ báo 100%, và nếu điểm số nằm sát mức 0 thì hệ thống xử lý thế nào để bảo vệ người lớn tuổi?\"*, "
        "câu trả lời chuẩn xác gồm 2 ý: **(1)** Hệ thống hiệu chuẩn bằng `Temperature / Platt Scaling (T = 16.0)` và kẹp cứng `[0.1%, 99.9%]` theo đúng chuẩn mực "
        "khoa học pháp y của `NIST`, triệt tiêu hoàn toàn hiện tượng tự tin ảo; **(2)** Mọi mẫu có `|s| ≤ 8.0` đều tự động bật cờ vàng hổ phách **`BORDERLINE`** "
        "khuyến nghị người lớn tuổi gọi lại trực tiếp kiểm chứng thay vì mạo hiểm kết luận vội vàng.",
        title="TỔNG KẾT PHẢN BIỆN CHƯƠNG 6: KẾT HỢP ĐỘ CHÍNH XÁC TOÁN HỌC VÀ AN TOÀN XÃ HỘI",
    )

    add_term_glossary(
        doc,
        [
            ("Borderline Zone", "Vùng cảnh báo biên / Vùng nghi vấn", "Khoảng điểm gần ngưỡng phân lớp (`|s − θ| ≤ 8.0`) nơi tín hiệu chưa đủ rõ ràng, hệ thống tự động cảnh báo màu hổ phách yêu cầu xác minh bổ sung."),
            ("Out-of-Band / OTP Verification", "Xác minh ngoài băng tần / kênh thứ hai", "Quy trình an ninh yêu cầu kiểm chứng qua một kênh độc lập (ví dụ tự gọi điện thoại di động trực tiếp hoặc hỏi câu hỏi riêng tư trong gia đình) khi tin nhắn thoại rơi vào vùng nghi vấn."),
            ("Human-in-the-loop", "Con người trong vòng kiểm soát", "Nguyên lý thiết kế AI an toàn: với các ca dị biệt hoặc sát ranh giới, AI cung cấp chỉ số định lượng và chuyển quyền quyết định cuối cùng cho con người."),
            ("Enrollment", "Đăng ký mẫu sinh trắc học", "Bước thu thập trước từ 3 câu nói thật trở lên của người dùng để ước lượng độ lệch âm học cá nhân."),
            ("Quartiles (Q1, Q3) & IQR", "Tứ phân vị & Khoảng tứ phân vị", "`IQR = Q_3 − Q_1` đo độ rộng của 50% dữ liệu trung tâm, là thước đo độ phân tán cực kỳ miễn nhiễm với các điểm nhiễu dị thường."),
            ("Guardrail", "Hàng rào an toàn tự động", "Chốt chặn logic trong phần mềm (như kẹp `[0.1%, 99.9%]` hoặc khóa `|offset| > 4 · IQR`) ngăn không cho mô hình đưa ra hành vi cực đoan gây mất an toàn."),
        ],
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(10)
