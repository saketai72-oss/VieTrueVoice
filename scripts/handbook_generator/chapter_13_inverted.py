"""
Chương 13 của Sổ Tay Kỹ Thuật & Phản Biện Hội Đồng ViTrueVoice v0.9.4:
Thực Nghiệm Đối Chứng Hoán Đổi Hai Chiều (Inverted Generalization Experiment: V7 vs V8.0 vs v0.9.4)
& Cơ Chế Triệt Tiêu Lỗ Hổng Continuous Flow Matching
"""

from __future__ import annotations

from .styles import (
    add_callout_box,
    add_defense_qa,
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
    omml_sub,
    omml_subsup,
    omml_sup,
)


def add_chapter_13_inverted(doc, figs: dict | None = None) -> None:
    """Render Chapter 13: Bidirectional Inverted Generalization (V7 vs V8.0 vs v0.9.4), CFM Math & Q23-Q27."""

    add_heading_chapter(
        doc,
        "Chương 13",
        "Thực Nghiệm Đối Chứng Hoán Đổi Hai Chiều (Inverted Generalization: V7 vs V8.0 vs v0.9.4) & Cơ Chế Triệt Tiêu Lỗ Hổng Flow Matching",
    )

    # =========================================================================
    # 13.1 THIẾT KẾ THỰC NGHIỆM HOÁN ĐỔI HAI CHIỀU & KHO ĐỐI XỨNG 1:1
    # =========================================================================
    add_foundation_primer(
        doc,
        process_name="Thiết kế thực nghiệm đối chứng hoán đổi hai chiều (Bidirectional Symmetrical Swap)",
        why_needed=(
            "Nếu một mô hình chỉ được kiểm chứng theo một chiều cố định (huấn luyện trên A, thử nghiệm trên B), Hội đồng khoa học "
            "có quyền đặt nghi vấn: liệu kết quả tốt có phải do tập dữ liệu B vô tình dễ hơn tập A, hay mô hình đang thiên kiến vào một "
            "kiến trúc tạo sinh duy nhất? Hoán đổi ngược lại vai trò giữa A và B trên quy mô mẫu đối xứng chính xác 1:1 là phép thử "
            "khắt khe nhất để chứng minh năng lực tổng quát hóa bản chất của kiến trúc SSL-AASIST."
        ),
        real_analogy=(
            "Giống như kiểm định một tấm áo giáp chống đạn: nếu chỉ bắn thử đạn mảnh văng rồi kết luận giáp tốt thì chưa đủ; "
            "khi phát hiện đạn xuyên giáp đầu nhọn (tương tự sóng âm trơn mượt của OmniVoice CFM) có thể xuyên qua khe hẹp, "
            "người kỹ sư gia cố lớp gốm chịu lực rồi bắn kiểm tra chéo lại cả hai loại đạn ở cự ly và số lượng viên đạn bằng hệt nhau."
        ),
        core_points=[
            "**Chiều Thuận (Thế hệ `V7`)**: Mô hình học trên hai công cụ `Seen TTS = {F5-TTS, VieNeu-TTS v3 Turbo}` và kiểm định ngoại lai trên `Unseen TTS = {OmniVoice CFM}`.",
            "**Chiều Nghịch Đối Xứng (Thế hệ `V8.0` → Chính thức `v0.9.4`)**: Hoán đổi hoàn toàn vị trí hai họ công nghệ — đưa `OmniVoice CFM` vào tập huấn luyện `Seen TTS = {F5-TTS, OmniVoice CFM}` và đẩy `VieNeu-TTS v3 Turbo` ra ngoài làm công cụ kiểm định ngoại lai `Unseen TTS` 100%.",
            "**Đối xứng quy mô 1:1 tuyệt đối (`6.445 tệp WAV`)**: Để không bên nào có lợi thế về số lượng mẫu, toàn bộ nhánh `OmniVoice_CFM` trong kho `Voice_Final` (`103.189 tệp`) được sinh đủ **6.445 tệp WAV** khớp 1:1 từng người nói, từng kịch bản và từng biến thể codec với nhánh `VieNeu_TTS` của V7.",
            "**Bất khả xâm phạm tập nghiệm thu**: Dù hoán đổi chiều huấn luyện thế nào, **5 tình nguyện viên nghiệm thu độc lập (`SPK_0003..0007`, `1.545 tệp`)** vẫn giữ nguyên trạng thái cô lập 100% khỏi mọi tập Train, Dev và hiệu chuẩn.",
        ],
    )

    add_heading_section(
        doc,
        "13.1 Thiết Kế Thực Nghiệm Hoán Đổi Đối Xứng 1:1 Giữa V7, V8.0 Và Phiên Bản Chính Thức v0.9.4",
    )
    add_styled_paragraph(
        doc,
        "Ở mô hình `V7`, khi đối mặt với công cụ nhân bản giọng nói ngoại lai `VoiceStudio (OmniVoice CFM)`, dù hệ thống đạt chuẩn "
        "Giả thuyết H2 trên tập chuẩn nhưng vẫn để lộ một khe hở đáng chú ý trên các mẫu giọng cực sạch trùng âm sắc (tỷ lệ lọt lưới trên tập kiểm thử lớn "
        "`test_indomain` lên tới `25.00%`, EER của riêng nhánh OmniVoice là `19.88%`, và trên một số lát cắt 5 tình nguyện viên khắt khe tỷ lệ lọt lưới "
        "từng chạm ngưỡng `~89.9%` ở nhóm ca đảo chiều). Ở phiên bản thử nghiệm trung gian `V8.0 Legacy`, nhóm mới sinh bán phần `1.885` tệp OmniVoice nên chưa "
        "đối xứng hoàn toàn với `V7`. Sang phiên bản chính thức **`ViTrueVoice v0.9.4`**, toàn bộ kho dữ liệu và 5 tệp manifest 19 cột đã được chuẩn hóa đối xứng 1:1 tuyệt đối:",
    )

    add_styled_table(
        doc,
        headers=[
            "Tiêu Chí Kiến Trúc Thực Nghiệm",
            "Mô Hình V7 Best (Chiều Thuận)",
            "Mô Hình V8.0 Legacy (Bán Phần)",
            "Mô Hình Chính Thức v0.9.4 (Đối Xứng 1:1)",
        ],
        rows=[
            (
                "Hai công cụ Seen TTS (Tham gia Train & Dev)",
                "`F5-TTS` + `VieNeu-TTS v3 Turbo`",
                "`F5-TTS` + `OmniVoice CFM` (bán phần 1.885 tệp)",
                "**`F5-TTS` (6.170) + `OmniVoice CFM` (6.445 tệp đối xứng 1:1)**",
            ),
            (
                "Công cụ Unseen TTS (Kiểm định H2 OOD)",
                "`OmniVoice CFM` (Continuous Flow Matching)",
                "`VieNeu-TTS v3 Turbo` (Acoustic LM + RVQ)",
                "**`VieNeu-TTS v3 Turbo` (Cô lập 100% — 955 mẫu Dev & 375 mẫu 5-SPK)**",
            ),
            (
                "Quy mô kho dữ liệu chuẩn `Voice_Final`",
                "Nhánh `spoof/v7`: 13.955 tệp",
                "Đang mở rộng chuyển tiếp",
                "**103.189 tệp** (`bonafide`: 70.174 | `spoof/v7`: 13.955 | `spoof/v8`: 19.060)",
            ),
            (
                "Tập Train đối chứng & chính thức",
                "Dual-Seen F5 + VieNeu",
                "54.225 dòng (bán phần CFM)",
                "Đối chứng `54.225` dòng (`train_v8_f5_omni_no_spk1.csv`) & Chính thức **`54.400` dòng** (`train_v8_f5_omni_with_spk1.csv`)",
            ),
            (
                "Cơ chế hiệu chuẩn trọng số & suy luận",
                "2 Pha + Asymmetric Veto",
                "Layer-Wise Grafting (split=4)",
                "**2 Pha (`am_m = 0.20`) + `head_blend_a0.75` + `Consensus Asymmetric Veto`**",
            ),
            (
                "Bộ nghiệm thu 5 tình nguyện viên",
                "`SPK_0003..0007` (Cô lập 100%)",
                "`SPK_0003..0007` (Cô lập 100%)",
                "**`SPK_0003..0007` (1.545 tệp qua 5 codecs — Cô lập 100%)**",
            ),
        ],
        col_widths=[1.55, 1.65, 1.55, 1.95],
    )

    add_styled_paragraph(
        doc,
        "Chi tiết phân bổ **6.445 tệp `OmniVoice_CFM`** đối xứng 1:1 với `VieNeu_TTS` gồm: (1) **`VIVOS`**: `4.795` tệp WAV (65 người nói, 959 mẫu gốc × 5 codecs); "
        "(2) **`Common Voice`**: `1.225` tệp WAV (25 người nói, 245 mẫu gốc × 5 codecs); và (3) **`SPK_Volunteers`**: `425` tệp WAV (gồm `375` tệp của 5 tình nguyện viên nghiệm thu `SPK_0003..0007` khóa riêng cho kiểm định độc lập và `50` tệp của tình nguyện viên thứ 6 dư ra `SPK_0001` thuộc tập Train chính thức). Bảng 13.2 tóm tắt 5 tệp manifest chuẩn 19 cột của `v0.9.4`:",
    )

    add_styled_table(
        doc,
        headers=[
            "Tệp Manifest (`data/manifests_zalo/`)",
            "Số Dòng",
            "Cơ Cấu Nhãn & Công Cụ Sinh Giả",
            "Vai Trò Khoa Học Trong Chuỗi Thực Nghiệm v0.9.4",
        ],
        rows=[
            (
                "`train_v8_f5_omni_no_spk1.csv`\n*(bản đối chứng `train_v8_nospk_f5_omni`)*",
                "54.225",
                "46.925 Bonafide + 3.660 F5-TTS + 3.640 OmniVoice CFM",
                "Tập huấn luyện đối chứng Run 1 chỉ gồm tập công khai VIVOS & Common Voice (0% tình nguyện viên, 0% VieNeu-TTS).",
            ),
            (
                "`train_v8_f5_omni_with_spk1.csv`\n*(bản chính thức `train_v8_sp1_f5_omni`)*",
                "**54.400**",
                "Bổ sung 175 mẫu của `SPK_0001` (75 Bonafide + 50 F5 + 50 OmniVoice)",
                "Tập huấn luyện chính thức Run 2 của `v0.9.4`: tận dụng tình nguyện viên thứ 6 dư ra sau khi đã khóa đủ 5 tình nguyện viên nghiệm thu `SPK_0003..0007`.",
            ),
            (
                "`dev_v8_f5_omni.csv`",
                "12.405",
                "10.490 Bonafide + 960 F5-TTS + 955 OmniVoice CFM",
                "Tập thẩm định hội tụ trên 15 người nói độc lập qua đủ 5 biến thể kênh thoại.",
            ),
            (
                "`test_indomain_v8_f5_omni.csv`",
                "**15.980**",
                "13.735 Bonafide + 1.125 F5-TTS + 1.120 OmniVoice CFM",
                "Tập kiểm thử quy mô lớn độc lập (`eval_only = 15.665` dòng) dùng đo đối đầu công bằng V7 vs V8.0 vs v0.9.4.",
            ),
            (
                "`unseen_vieneu_benchmark.csv`",
                "**955**",
                "955 mẫu `VieNeu-TTS v3 Turbo` (15 Dev SPK × 5 codecs)",
                "Tập kiểm định Giả thuyết H2 ngoại lai hoàn toàn (yêu cầu KPI `EER ≤ 15.0%`).",
            ),
        ],
        col_widths=[1.95, 0.75, 1.9, 2.1],
        highlight_row_pred=lambda idx, _: idx in (1, 3, 4),
    )

    add_term_glossary(
        doc,
        terms=[
            ("Inverted Generalization", "Bidirectional Symmetrical Generalization Test", "Thực nghiệm hoán đổi ngược hai chiều giữa công cụ đã học (`Seen`) và công cụ chưa từng thấy (`Unseen`) để bác bỏ nghi ngờ ăn may kiến trúc."),
            ("1:1 Path Symmetry", "Exact Utterance- & Codec-Matched Corpus", "Nguyên tắc thiết kế kho mẫu giả sao cho mỗi tệp của công cụ A đều có đúng một tệp đối ứng của công cụ B trùng người nói mẫu, câu kịch bản và biến thể nén."),
            ("eval_only Subset", "Reference-Excluded Evaluation Slice", "Lát cắt `15.665 / 15.980` dòng loại trừ các câu từng đóng vai trò mẫu tham chiếu (`prompt`), đảm bảo không trùng lặp ngữ âm dù nhỏ nhất."),
        ],
    )

    # =========================================================================
    # 13.2 BẢN CHẤT TOÁN HỌC: DÒNG LIÊN TỤC CFM ODE SO VỚI MÃ HÓA RỜI RẠC RVQ
    # =========================================================================
    add_foundation_primer(
        doc,
        process_name="Giải mã toán học giữa Dòng chảy Liên tục (CFM ODE) và Lượng tử hóa Rời rạc (Discrete RVQ)",
        why_needed=(
            "Câu hỏi sâu sắc nhất của Chương 13 là: Tại sao khi chưa học OmniVoice CFM thì V7 bị lọt lưới một phần đáng kể, "
            "nhưng khi v0.9.4 chỉ học F5-TTS + OmniVoice CFM mà KHÔNG HỀ HỌC VieNeu-TTS thì vẫn chặn đứng VieNeu-TTS dễ dàng "
            "(12.05% Dev EER và 92.53% trên 5 tình nguyện viên)? Câu trả lời nằm trọn ở sự bất đối xứng toán học giữa phương trình vi phân liên tục và phép làm tròn rời rạc."
        ),
        real_analogy=(
            "Hãy so sánh hai cách vẽ một đường cong chân dung: (1) `OmniVoice CFM` giống như họa sĩ cầm bút lông lướt một đường mực "
            "liền mạch từ đầu đến cuối theo thước dẫn thẳng — đường nét trơn láng đến mức mắt thường khó phân biệt với ảnh chụp thật, "
            "chỉ khi phóng kính hiển vi mới thấy 16 nốt gãy siêu nhỏ do tay họa sĩ đổi hướng 16 nhịp; (2) `VieNeu-TTS (RVQ)` giống như "
            "ghép bức tranh từ những viên gạch Lego vuông vức lấy sẵn trong hộp — dù xếp khéo đến mấy thì mép nối giữa các viên gạch vẫn có gờ bậc thang rời rạc!"
        ),
        core_points=[
            "**Trường phái Dòng chảy Liên tục (`Continuous Flow Matching - CFM`)**: Biến đổi nhiễu chuẩn trực tiếp thành biểu diễn âm thanh dọc theo quỹ đạo đường thẳng tối ưu (`Optimal Transport`) bằng phương trình vi phân thường `ODE`. Do không nhảy ngẫu nhiên ziczac và không bị ép qua bảng mã rời rạc, phổ pha của nó cực kỳ trơn nhẵn.",
            "**Sai số cắt cụt bước tích phân hữu hạn (`Finite-Step ODE Truncation Error`)**: Để sinh giọng nói nhanh trong thời gian thực, `OmniVoice CFM` chỉ giải phương trình vi phân qua số bước hữu hạn (ví dụ `N = 16` bước Euler/Midpoint). Khoảng bước rời rạc `Δt = 1/N` này vẫn để lại sai số xấp xỉ bậc hai `O(Δt²)` ở dải vi hài âm tần số cao — nhưng mạng `SSL-AASIST` chỉ chú ý tới dấu vết siêu mảnh này khi được nhìn thấy mẫu CFM trong tập huấn luyện!",
            "**Trường phái Lượng tử hóa Phần dư Rời rạc (`Residual Vector Quantization - RVQ`)**: Các mô hình ngôn ngữ âm học như `VieNeu-TTS v3 Turbo` (dùng `NeuCodec`, tương tự họ `EnCodec / SpeechTokenizer`) băm tín hiệu liên tục thành tổng của `M` mã chuẩn lấy từ từ điển hữu hạn. Phép làm tròn này luôn để lại **phần dư lượng tử hóa `e_q ≠ 0`** dạng răng cưa vi mô.",
            "**Hiện tượng Miễn dịch Chéo Một Chiều (`One-Way Cross-Immunity`)**: Một bộ giám định đã được rèn luyện khắc nghiệt để bắt cả những vết xước vi mô của nét bút mực trơn láng (`CFM`) thì khi gặp bức tranh ghép bằng gạch Lego có gờ bậc thang (`RVQ` của `VieNeu-TTS`), nó lập tức phát hiện ra sự bất thường mà không cần học trước!",
        ],
    )

    add_heading_section(
        doc,
        "13.2 Cơ Chế Toán Học Của Sự Bất Đối Xứng Giữa Continuous Flow Matching Và Discrete Neural Codec",
    )
    add_heading_subsection(
        doc,
        "13.2.1 Phương Trình Vi Phân Thường (ODE) Của OmniVoice CFM Và Nguyên Nhân Gây Lọt Lưới Ở V7",
    )
    add_styled_paragraph(
        doc,
        "Khác với mô hình khuếch tán truyền thống phải cộng và khử nhiễu ngẫu nhiên qua hàng trăm bước ziczac, `OmniVoice CFM` học một "
        "trường vận tốc có điều kiện `v_θ(x_t, t, c)` để đẩy mẫu nhiễu Gauss ban đầu `x_0` trượt thẳng về phân phối âm thanh thật `x_1` "
        "theo quỹ đạo nội suy tuyến tính Vận chuyển Tối ưu (`Optimal Transport`) trên miền thời gian ảo `t ∈ [0, 1]`:",
    )

    eq_cfm_xml = (
        omml_frac(
            omml_r("d") + omml_sub(omml_r("x"), omml_r("t")),
            omml_r("dt"),
        )
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("v"), omml_r("θ"))
        + omml_delim(omml_sub(omml_r("x"), omml_r("t")) + omml_r(", t, c"))
        + omml_r(" ,     ", normal=True)
        + omml_sub(omml_r("x"), omml_r("t"))
        + omml_r(" = ", normal=True)
        + omml_delim(omml_r("1 − t"))
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("x"), omml_r("0", normal=True))
        + omml_r(" + ", normal=True)
        + omml_r("t")
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("x"), omml_r("1", normal=True))
    )
    add_omml_equation(
        doc,
        formula_title="Phương trình vi phân dòng liên tục (CFM ODE) và quỹ đạo nội suy thẳng Optimal Transport",
        omml_body_xml=eq_cfm_xml,
        variables=[
            ("x_0, x_1", "`x_0` là vector nhiễu chuẩn Gauss khởi tạo tại `t = 0`; `x_1` là biểu diễn phổ/sóng âm đích của giọng nói tại `t = 1`."),
            ("x_t", "Trạng thái trung gian tại thời điểm nội suy `t ∈ [0, 1]`, di chuyển theo đường thẳng ngắn nhất nối từ `x_0` tới `x_1`."),
            ("c", "Điều kiện ngữ cảnh gồm nội dung văn bản cần đọc và đoạn giọng mẫu tham chiếu (`zero-shot acoustic prompt`) của nạn nhân."),
            ("v_θ(x_t, t, c)", "Mạng nơ-ron dự đoán trường vector vận tốc tức thời. Khi giải tích phân số bằng `N` bước rời rạc `Δt = 1/N`, sai số cắt cụt cục bộ chỉ cỡ `O(Δt²)`, tạo ra sóng âm có bao hình năng lượng cực mượt từng đánh lừa mô hình `V7` chưa được học họ CFM.",
            ),
        ],
    )

    add_heading_subsection(
        doc,
        "13.2.2 Sai Số Lượng Tử Hóa Phần Dư (RVQ Error) Của VieNeu-TTS Và Cơ Chế Miễn Dịch Chéo Ở v0.9.4",
    )
    add_styled_paragraph(
        doc,
        "Ngược lại, `VieNeu-TTS v3 Turbo` mã hóa biểu diễn âm thanh liên tục `z` thành chuỗi chỉ số nguyên thông qua `M` tầng "
        "lượng tử hóa phần dư nối tiếp (`Residual Vector Quantization - RVQ`). Tại mỗi tầng `m`, bộ lượng tử `Q_m` chọn vector gần nhất "
        "trong bảng từ điển hữu hạn để xấp xỉ phần dư `r_m`. Tổng các vector khôi phục luôn tồn tại một sai số lượng tử hóa khác không `e_q`:",
    )

    eq_rvq_xml = (
        omml_sub(omml_r("e"), omml_r("q"))
        + omml_r(" = ", normal=True)
        + omml_r("z")
        + omml_r(" − ", normal=True)
        + omml_subsup(omml_r("∑", normal=True), omml_r("m=1", normal=True), omml_r("M"))
        + omml_sub(omml_r("Q"), omml_r("m"))
        + omml_delim(omml_sub(omml_r("r"), omml_r("m")))
        + omml_r(" ≠ 0", normal=True)
    )
    add_omml_equation(
        doc,
        formula_title="Biểu thức sai số lượng tử hóa phần dư không triệt tiêu trong bộ mã hóa thần kinh rời rạc RVQ",
        omml_body_xml=eq_rvq_xml,
        variables=[
            ("z", "Vector đặc trưng âm học liên tục thực sự trước khi nén rời rạc."),
            ("M", "Tổng số tầng bảng mã (`codebooks`) xếp chồng trong bộ mã hóa âm thanh thần kinh `NeuCodec`."),
            ("r_m, Q_m(r_m)", "`r_m` là phần sai số còn sót lại sau tầng `m − 1`; `Q_m(r_m)` là vector rời rạc gần nhất được tra cứu trong bảng mã thứ `m`."),
            ("e_q ≠ 0", "Sai số lượng tử hóa tất yếu tại ranh giới chuyển tiếp các khung `token`. Khi `v0.9.4` đã học cách bóc tách cả sai số tích phân siêu mịn của `F5-TTS` và `OmniVoice CFM`, sai số bậc thang `e_q` của `VieNeu-TTS` lập tức lộ diện rõ rệt dù mô hình chưa từng gặp `VieNeu-TTS` trong lúc huấn luyện!",
            ),
        ],
    )

    add_term_glossary(
        doc,
        terms=[
            ("ODE", "Ordinary Differential Equation", "Phương trình vi phân thường — mô tả quỹ đạo biến đổi xác định, trơn tru của trạng thái âm thanh theo biến thời gian liên tục `t`."),
            ("Optimal Transport", "Optimal Transport Linear Trajectory", "Bài toán vận chuyển tối ưu tìm đường đi thẳng ngắn nhất từ phân phối nhiễu sang phân phối giọng nói, giúp `OmniVoice CFM` hội tụ chỉ sau ít bước tính."),
            ("Truncation Error", "Numerical Discretization Error", "Sai số xấp xỉ số học phát sinh do máy tính giải phương trình vi phân bằng các bước nhảy hữu hạn `Δt` thay vì vi phân vô cùng bé."),
            ("Cross-Immunity", "Asymmetric Generative Cross-Immunity", "Hiện tượng huấn luyện bộ phát hiện trên công nghệ sinh giọng mượt hơn (`CFM`) tự động tạo sức đề kháng mạnh trước công nghệ sinh giọng rời rạc (`RVQ`)."),
        ],
    )

    # =========================================================================
    # 13.3 HUẤN LUYỆN 2-RUN, HIỆU CHUẨN HEAD_BLEND_A0.75 & CONSENSUS VETO
    # =========================================================================
    add_foundation_primer(
        doc,
        process_name="Hiệu chuẩn không gian trọng số (head_blend_a0.75) & Gộp điểm đồng thuận Consensus Asymmetric Veto",
        why_needed=(
            "Khi đưa 6.445 mẫu OmniVoice CFM siêu mượt vào huấn luyện sâu ở Pha 2, mạng nơ-ron học cách phân tách cực tốt giữa giọng thật "
            "và giọng giả CFM (EER thấp), nhưng đầu phân loại tuyến tính lại có xu hướng kéo biên quyết định dịch sang phía âm để siết chặt an ninh — "
            "hệ quả là một số người thật nói nhỏ hoặc có giọng trầm dễ bị chấm điểm âm oan. Làm sao sửa lại vị trí thanh chắn quyết định về đúng tâm 0.0 "
            "mà không làm mất đi một chút tri thức quý giá nào của khối Wav2Vec 2.0 vừa học được?"
        ),
        real_analogy=(
            "Hãy tưởng tượng một chiếc cân điện tử có cảm biến bên trong cực nhạy (khối `Wav2Vec 2.0` Pha 2), nhưng kim chỉ vạch `0` trên mặt đồng hồ "
            "bị lệch nhẹ sang trái (đầu phân loại `Classifier Head`). Thay vì tháo tung cả bộ cảm biến ra lắp lại từ đầu dễ làm hỏng độ nhạy, "
            "người kỹ sư khóa chặt bộ cảm biến và chỉ vặn nhẹ ốc hiệu chỉnh kim đồng hồ theo tỷ lệ vàng `25% vị trí cũ + 75% vị trí cân bằng chuẩn` (`head_blend_a0.75`)."
        ),
        core_points=[
            "**Thiết kế đối chứng 2 lượt huấn luyện (`Run 1` so với `Run 2`)**: Cả hai lượt đều huấn luyện 2 pha với `AM-Softmax (s = 30.0, m = 0.20)`, `batch_size = 8`, `accum_steps = 2`. `Run 1` chạy trên tập đối chứng công khai `54.225` dòng (`VIVOS + Common Voice`); `Run 2` chạy trên tập chính thức `54.400` dòng có gộp thêm `175` mẫu của tình nguyện viên thứ 6 dư ra (`SPK_0001`) sau khi đã khóa cứng 5 tình nguyện viên nghiệm thu độc lập (`SPK_0003..0007`).",
            "**Hiệu chuẩn Giai đoạn 3 (`head_blend_a0.75`)**: Đóng băng **100% trọng số khối `Wav2Vec 2.0`** của `Run 2 Pha 2`, chỉ vi chỉnh nhẹ đầu phân loại (`Head-Only`) 1 epoch trên tập con cân bằng `train_v8_balanced_ft.csv` (`5.100` dòng, `0%` rò rỉ 5 SPK nghiệm thu / Dev / Test / VieNeu), sau đó nội suy tuyến tính trọng số đầu phân loại với hệ số `α = 0,75`.",
            "**Phối hợp cùng `Consensus Asymmetric Veto`**: Sau khi trọng số mô hình đã được cân tâm bằng `head_blend_a0.75`, tầng suy luận đa cửa sổ tiếp tục áp dụng kiểm tra đồng thuận cửa sổ cao nhì `≥ +6.0` khi gặp cửa sổ nghi giả `< −12.0`, hoàn thiện lá chắn kép hoàn chỉnh của `v0.9.4`.",
        ],
    )

    add_heading_section(
        doc,
        "13.3 Quy Trình Huấn Luyện 2-Run, Hiệu Chuẩn Trọng Số head_blend_a0.75 Và Kết Quả Thực Nghiệm v0.9.4",
    )
    add_heading_subsection(
        doc,
        "13.3.1 So Sánh Trung Thực Hai Lượt Huấn Luyện (Run 1: 54.225 Dòng & Run 2: 54.400 Dòng) Và Công Thức head_blend_a0.75",
    )
    add_styled_paragraph(
        doc,
        "Trong giai đoạn xây dựng phiên bản `v0.9.4`, nhóm thực hiện song song hai lượt huấn luyện độc lập khởi tạo từ nền tảng kênh thoại nén `V5` "
        "với biên góc `AM-Softmax m = 0,20` và hệ số tỷ lệ `s = 30,0`: "
        "(1) **`Run 1` (`train_v8_f5_omni_no_spk1.csv`, `54.225` dòng)** đóng vai trò đường cơ sở thuần dữ liệu công khai (`VIVOS` + `Common Voice`), đạt `Dev EER = 7.96%` ở Pha 1 và **`6.32%`** ở Pha 2; "
        "(2) **`Run 2` (`train_v8_f5_omni_with_spk1.csv`, `54.400` dòng)** tích hợp đầy đủ các nguồn dữ liệu không thuộc diện nghiệm thu — bao gồm `VIVOS`, `Common Voice` và `175` mẫu của tình nguyện viên thứ 6 dư ra (`SPK_0001`, do 5 tình nguyện viên `SPK_0003..0007` đã được niêm phong đủ cho Bộ Nghiệm Thu Độc Lập Chính Thức) — giúp kéo giảm `Dev EER` Pha 2 xuống mức **`5.95%`**.",
    )

    eq_am_xml = (
        omml_sub(omml_r("L"), omml_r("AM", normal=True))
        + omml_r(" = − ", normal=True)
        + omml_r("log", normal=True)
        + omml_delim(
            omml_frac(
                omml_sup(
                    omml_r("e"),
                    omml_r("s · ", normal=True) + omml_delim(omml_r("cos", normal=True) + omml_sub(omml_r("ψ"), omml_r("y")) + omml_r(" − m")),
                ),
                omml_sup(
                    omml_r("e"),
                    omml_r("s · ", normal=True) + omml_delim(omml_r("cos", normal=True) + omml_sub(omml_r("ψ"), omml_r("y")) + omml_r(" − m")),
                )
                + omml_r(" + ", normal=True)
                + omml_sup(
                    omml_r("e"),
                    omml_r("s · ", normal=True) + omml_r("cos", normal=True) + omml_sub(omml_r("ψ"), omml_r("1−y")),
                ),
            )
        )
    )
    add_omml_equation(
        doc,
        formula_title="Hàm mất mát biên góc cộng tính AM-Softmax dùng trong huấn luyện 2 pha của v0.9.4",
        omml_body_xml=eq_am_xml,
        variables=[
            ("ψ_y, ψ_{1−y}", "Góc giữa vector biểu diễn âm thanh chuẩn hóa `L2` và vector trọng số tâm của lớp đúng `y` cũng như lớp đối lập `1 − y`."),
            ("s = 30,0", "Hệ số phóng đại bán kính siêu cầu định hình dải điểm thô logit trên miền `[-50, +50]`."),
            ("m = 0,20", "Biên lề góc ép hai lớp Thật – Giả tách xa nhau nhưng đủ ôn hòa để không đẩy người nói có tần số cơ bản trầm tự nhiên sang miền giả mạo."),
        ],
    )

    add_styled_paragraph(
        doc,
        "Tiếp theo, để khử độ lệch biên âm phát sinh sau Pha 2 mà giữ nguyên vẹn 100% không gian biểu diễn tự giám sát `Wav2Vec 2.0` của `Run 2`, "
        "nhóm thực hiện bước hiệu chuẩn Giai đoạn 3 trên tập cân bằng `train_v8_balanced_ft.csv` (`5.100` dòng) và trộn tuyến tính không gian trọng số đầu phân loại theo công thức **`head_blend_a0.75`**:",
    )

    eq_blend_xml = (
        omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(v0.9.4)", normal=True))
        + omml_r(" = ", normal=True)
        + omml_delim(omml_r("1 − α"))
        + omml_r(" · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(Run2_P2)", normal=True))
        + omml_r(" + α · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(HeadOnly)", normal=True))
        + omml_r(" = 0,25 · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(Run2_P2)", normal=True))
        + omml_r(" + 0,75 · ", normal=True)
        + omml_subsup(omml_r("W", bold=True), omml_r("head", normal=True), omml_r("(HeadOnly)", normal=True))
    )
    add_omml_equation(
        doc,
        formula_title="Phép nội suy tuyến tính không gian trọng số đầu phân loại Stage 3 (head_blend_a0.75)",
        omml_body_xml=eq_blend_xml,
        variables=[
            ("W_head^(Run2_P2)", "Trọng số khối đồ thị và đầu phân loại sau Pha 2 của `Run 2` — rất sắc bén khi bắt `OmniVoice CFM` nhưng hơi thiên lệch về điểm âm."),
            ("W_head^(HeadOnly)", "Trọng số đầu phân loại sau 1 epoch hiệu chuẩn cân bằng khi đóng băng hoàn toàn 100% khối `Wav2Vec 2.0`."),
            ("α = 0,75", "Hệ số pha trộn tối ưu xác định trên tập kiểm chứng Dev, xuất ra checkpoint sản xuất chính thức `out/v0.9.4/best_model.pt` (`sha256: 30a383256458740e...`)."),
        ],
    )

    add_heading_subsection(
        doc,
        "13.3.2 Đối Chứng Toàn Diện Trên Tập Kiểm Thử Độc Lập 15.980 Mẫu & Bộ Nghiệm Thu 5 Tình Nguyện Viên (1.545 Tệp)",
    )
    add_styled_paragraph(
        doc,
        "Bảng 13.3 trình bày kết quả đánh giá đối đầu trực diện giữa 3 thế hệ mô hình (`V7 Best`, `V8.0 Legacy` và **`v0.9.4 Best`**) "
        "qua cả 3 chế độ gộp điểm đa cửa sổ (`Consensus Asymmetric Veto`, `Max-Pooling`, `Mean-Pooling`) trên tập kiểm thử độc lập quy mô lớn **`test_indomain_v8_f5_omni.csv` (`15.980` mẫu)**:",
    )

    add_styled_table(
        doc,
        headers=[
            "Thế Hệ Mô Hình",
            "Chế Độ Pooling",
            "Tổng EER / Tỷ Lệ Chặn",
            "BPCER",
            "F5-TTS (EER / Chặn)",
            "OmniVoice (EER / Chặn)",
            "EER Qua 5 Codecs (Clean | AAC | Opus | G711 | AMR)",
        ],
        rows=[
            (
                "V7 Best",
                "`asymmetric_veto`",
                "13.72% / 87.22%",
                "15.10%",
                "6.17% / 99.38%",
                "19.88% / 75.00%",
                "13.37 | 12.92 | 14.92 | 14.03 | 13.36%",
            ),
            (
                "V8.0 Legacy",
                "`asymmetric_veto`",
                "6.79% / 90.33%",
                "4.12%",
                "2.23% / 98.22%",
                "8.84% / 82.41%",
                "6.46 | 7.35 | 6.90 | 6.24 | 6.11%",
            ),
            (
                "**v0.9.4 Chính thức**",
                "**`asymmetric_veto`**",
                "**5.63% / 95.01%**",
                "**6.73%**",
                "**2.81% / 98.49%**",
                "**7.95% / 91.52%**",
                "**5.52 | 5.79 | 6.02 | 6.11 | 4.88%**",
            ),
            (
                "V7 Best",
                "`max`",
                "14.72% / 83.16%",
                "12.07%",
                "5.14% / 98.93%",
                "21.79% / 67.32%",
                "14.92 | 14.25 | 15.59 | 14.48 | 14.03%",
            ),
            (
                "V8.0 Legacy",
                "`max`",
                "9.31% / 84.37%",
                "2.64%",
                "2.77% / 97.16%",
                "13.30% / 71.52%",
                "9.25 | 10.68 | 9.80 | 8.91 | 7.90%",
            ),
            (
                "v0.9.4 Chính thức",
                "`max`",
                "8.33% / 88.24%",
                "5.34%",
                "3.21% / 97.69%",
                "11.61% / 78.75%",
                "8.24 | 9.35 | 8.69 | 7.35 | 7.13%",
            ),
            (
                "V7 Best",
                "`mean`",
                "13.81% / 87.88%",
                "16.28%",
                "5.32% / 99.47%",
                "19.21% / 76.25%",
                "13.59 | 12.92 | 14.92 | 13.90 | 13.11%",
            ),
            (
                "V8.0 Legacy",
                "`mean`",
                "5.54% / 92.92%",
                "4.81%",
                "2.31% / 98.22%",
                "6.54% / 87.59%",
                "5.57 | 6.17 | 5.88 | 5.12 | 5.25%",
            ),
            (
                "v0.9.4 Chính thức",
                "`mean`",
                "6.24% / 96.17%",
                "8.80%",
                "2.84% / 98.67%",
                "7.77% / 93.66%",
                "6.17 | 6.68 | 6.74 | 5.63 | 5.81%",
            ),
        ],
        col_widths=[0.95, 0.95, 1.05, 0.55, 0.95, 1.0, 1.25],
        highlight_row_pred=lambda idx, _: idx == 2,
    )

    if figs and figs.get("fig8"):
        add_figure(
            doc,
            figs["fig8"],
            "Hình 13.1: (A) Sự sụt giảm mạnh tỷ lệ sai số EER từ V7 Best (13.72%) → V8.0 Legacy (6.79%) → v0.9.4 Chính thức (5.63%) trên 15.980 mẫu kiểm thử qua cả 5 biến thể kênh thoại; (B) Kết quả nghiệm thu độc lập trên 5 tình nguyện viên cô lập hoàn toàn (1.545 tệp).",
        )

    eq_red_xml = (
        omml_sub(omml_r("ΔEER"), omml_r("rel", normal=True))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("EER"), omml_r("V7", normal=True))
            + omml_r(" − ", normal=True)
            + omml_sub(omml_r("EER"), omml_r("v0.9.4", normal=True)),
            omml_sub(omml_r("EER"), omml_r("V7", normal=True)),
        )
        + omml_r(" × 100% = ", normal=True)
        + omml_frac(
            omml_r("13,72% − 5,63%", normal=True),
            omml_r("13,72%", normal=True),
        )
        + omml_r(" × 100% = 58,97%", normal=True)
    )
    add_omml_equation(
        doc,
        formula_title="Tỷ lệ giảm sai số tương đối toàn cục trên 15.980 mẫu và triệt tiêu rò rỉ OmniVoice CFM",
        omml_body_xml=eq_red_xml,
        variables=[
            ("13,72% → 6,79% → 5,63%", "Chuỗi cải thiện EER tổng thể qua 3 thế hệ dưới chế độ chuẩn sản xuất `Consensus Asymmetric Veto` trên `15.980` mẫu (`eval_only`: `5,61%` EER), giảm tương đối **58,97%** sai số so với `V7 Best`."),
            ("OmniVoice Leak Suppression", "Trên bộ 5 tình nguyện viên độc lập (`375` mẫu `OmniVoice CFM` qua 5 codecs), tỷ lệ lọt lưới giảm sâu từ vùng rò rỉ nặng `~89,9%` ở chế độ đối chứng nghiêm ngặt thời kỳ V7 xuống chỉ còn **16,53% rò rỉ / chặn đứng 83,47% (313/375)** ở `v0.9.4`; đồng thời trên tập Test `15.980` mẫu, tỷ lệ chặn `OmniVoice CFM` vọt lên **91,52% (EER 7,95%)**."),
            ("Unseen VieNeu-TTS Stability", "Mặc dù `VieNeu-TTS v3 Turbo` bị loại bỏ 100% khỏi tập huấn luyện của `v0.9.4`, mô hình vẫn giữ vững **12,05% EER** trên tập chuẩn `955` mẫu Dev (`≤ 15,0%` KPI Giả thuyết H2) và chặn đứng **92,53% (347/375)** trên 5 tình nguyện viên độc lập!"),
        ],
    )

    add_styled_paragraph(
        doc,
        "Bảng 13.4 tổng hợp kết quả kiểm định đầy đủ trên **Bộ Nghiệm Thu Độc Lập 5 Tình Nguyện Viên (`SPK_0003..0007`, tổng cộng `1.545` tệp âm thanh qua 5 codecs)** "
        "và **4 Cổng Kiểm Chứng Đối Đầu** của mô hình chính thức `v0.9.4`:",
    )

    add_styled_table(
        doc,
        headers=[
            "Hạng Mục Kiểm Định Độc Lập",
            "Quy Mô Mẫu",
            "Kết Quả Của v0.9.4 (`asymmetric_veto`)",
            "Đối Chiếu Mục Tiêu Khoa Học Đề Tài",
        ],
        rows=[
            (
                "5 Tình nguyện viên — Giọng thật (`Bonafide`)",
                "420 tệp (84 gốc × 5 codecs)",
                "**Nhận diện đúng 94.76% (398/420)** (`BPCER = 5.24%`; riêng 4 SPK `0004..0007` đạt **100% 64/64** trên bản gốc)",
                "**ĐẠT XUẤT SẮC** — Cô lập 100% khỏi mọi tập huấn luyện và hiệu chuẩn.",
            ),
            (
                "5 Tình nguyện viên — Giả `F5-TTS` (Seen)",
                "375 tệp (75 gốc × 5 codecs)",
                "**Chặn đứng 100.0% (375/375)** (`APCER = 0.00%`)",
                "**ĐẠT TUYỆT ĐỐI** trên cả 5 biến thể kênh thoại.",
            ),
            (
                "5 Tình nguyện viên — Giả `OmniVoice CFM` (Seen)",
                "375 tệp (75 gốc × 5 codecs)",
                "**Chặn đứng 83.47% (313/375)** (chỉ còn `16.53%` lọt lưới ở mẫu siêu sạch trùng âm sắc)",
                "**ĐỘT PHÁ** — Khắc phục triệt để lỗ hổng lọt lưới Flow Matching trước đây.",
            ),
            (
                "5 Tình nguyện viên — Giả `VieNeu-TTS` (Unseen H2)",
                "375 tệp (75 gốc × 5 codecs)",
                "**Chặn đứng 92.53% (347/375)** (`APCER = 7.47%`)",
                "**ĐẠT VƯỢT KỲ VỌNG** — Chưa từng xuất hiện 1 mẫu nào trong tập Train/Dev.",
            ),
            (
                "Benchmark chuẩn Giả thuyết H2 (`unseen_vieneu`)",
                "955 mẫu giả + 2.000 mẫu thật Dev",
                "**EER = 12.05%** (tỷ lệ chặn đạt `79.58%` tại `θ = 0.0`)",
                "**H2 PASS** — Thấp hơn rõ rệt so với trần cam kết `EER ≤ 15.0%`.",
            ),
            (
                "Cổng đảo chiều 195 ca lọt lưới khó của V7 (`Gate 4`)",
                "195 mẫu `OmniVoice` từng đánh lừa V7",
                "**Đảo chiều chặn lại thành công 72.8% (142/195)** (ở V7 chỉ đạt `0.5%`, tức `1/195`!)",
                "Ví dụ ca `VIVOSDEV02_omnivoice_prompt_000` đảo từ `+15.17` (V7) xuống sâu vùng âm ở `v0.9.4`.",
            ),
        ],
        col_widths=[1.75, 1.25, 1.9, 1.8],
        highlight_row_pred=lambda idx, _: idx in (0, 1, 3, 4),
    )

    add_callout_box(
        doc,
        "Bức tranh đối xứng hoàn chỉnh của `v0.9.4` rút ra một định luật thực nghiệm cực kỳ đắt giá để trình bày trước Hội đồng: "
        "**Huấn luyện trên dòng chảy liên tục (`F5-TTS` + `OmniVoice CFM`) kết hợp hiệu chuẩn đầu phân loại `head_blend_a0.75` và `Consensus Asymmetric Veto` "
        "tạo ra thế phòng thủ hai chiều tối ưu — vừa kéo EER nội bộ xuống `5.63%` trên `15.980` mẫu, vừa tự động giữ vững khả năng bắt công cụ rời rạc ngoại lai "
        "`VieNeu-TTS` ở mức `12.05% EER` và `92.53%` tỷ lệ chặn trên 5 tình nguyện viên độc lập!**",
        title="THÔNG ĐIỆP KHOA HỌC TRỌNG TÂM CỦA CHƯƠNG 13",
    )

    add_term_glossary(
        doc,
        terms=[
            ("AM-Softmax", "Additive Margin Softmax Loss", "Hàm mất mát đặt thêm biên góc `m = 0,20` giữa hai lớp Thật – Giả trên mặt siêu cầu chuẩn hóa `L2`, giúp cụm đặc trưng gom chặt hơn hàm Softmax thường."),
            ("head_blend_a0.75", "Linear Classifier Head Weight Interpolation", "Phép trộn tuyến tính `25%` trọng số đầu phân loại Pha 2 với `75%` trọng số đầu phân loại hiệu chuẩn cân bằng trong khi giữ đóng băng nguyên vẹn 100% khối `Wav2Vec 2.0`."),
            ("Negative Classifier Bias", "Decision Boundary Drift Toward Spoof", "Hiện tượng biên phân loại tuyến tính bị dịch nhẹ sang miền âm sau khi học cường độ cao trên các mẫu giả rất giống thật."),
            ("Gate 4 Reversal Slice", "Hard False-Acceptance Reversal Subset", "Tập hợp 195 mẫu giả `OmniVoice CFM` khó nhất từng vượt mặt mô hình V7, dùng làm thước đo trực tiếp khả năng vá lỗ hổng của `v0.9.4`."),
        ],
    )

    # =========================================================================
    # 13.4 NĂM CÂU HỎI PHẢN BIỆN CHUYÊN SÂU (CÂU 23 – CÂU 27)
    # =========================================================================
    add_foundation_primer(
        doc,
        process_name="Chiến thuật trả lời 5 câu hỏi phản biện nâng cao về Thực nghiệm đối chứng hai chiều (Câu 23 – Câu 27)",
        why_needed=(
            "Khi thấy sinh viên trình bày cả hai thế hệ mô hình V7 và v0.9.4, các Giảng viên chuyên sâu về Học máy chắc chắn sẽ xoáy vào "
            "tính công bằng của phép hoán đổi, lý do toán học của sự bất đối xứng giữa CFM và RVQ, và tại sao phép trộn trọng số head_blend_a0.75 "
            "không phạm quy rò rỉ dữ liệu. Năm câu hỏi 23–27 dưới đây ghép nối trực tiếp với 22 câu ở Chương 11 thành trọn bộ 27 câu hỏi bảo vệ toàn diện."
        ),
        real_analogy=(
            "Nếu 22 câu ở Chương 11 là tấm khiên bảo vệ toàn bộ khung nhà kỹ thuật của đồ án, thì 5 câu hỏi 23–27 ở Chương 13 chính là "
            "mũi giáo ghi điểm xuất sắc (điểm A / 9.5+) dành cho những câu hỏi phân loại sinh viên giỏi của Chủ tịch Hội đồng."
        ),
        core_points=[
            "**Luôn nhấn mạnh quy mô đối xứng 1:1 (`6.445 tệp OmniVoice_CFM` đối ứng `6.445 tệp VieNeu_TTS`)**: Chứng minh phép so sánh hoàn toàn công bằng, không thiên vị số lượng mẫu.",
            "**Giải thích bằng cặp đối lập vật lý `ODE trơn liên tục` so với `RVQ bậc thang rời rạc`**: Giải thích gọn gàng vì sao chiều `CFM → RVQ` tổng quát hóa tốt gấp nhiều lần chiều `RVQ → CFM`.",
            "**Khẳng định kỷ luật `0% rò rỉ` ở bước `head_blend_a0.75`**: Tập cân bằng `5.100` dòng hoàn toàn lấy từ phần dữ liệu huấn luyện hợp lệ, tuyệt đối không chạm tới 5 tình nguyện viên nghiệm thu, tập Dev, tập Test `15.980` dòng hay `VieNeu-TTS`.",
        ],
    )

    add_heading_section(
        doc,
        "13.4 Năm (05) Câu Hỏi Phản Biện Nâng Cao Về Thực Nghiệm Hoán Đổi Hai Chiều & Mô Hình v0.9.4 (Câu 23 – Câu 27)",
    )

    def _qa(q_num: int, question: str, intent: str, step1: str, step2: str, step3: str) -> None:
        add_defense_qa(doc, q_num, question, intent, step1, step2, step3)

    _qa(
        23,
        "Tại sao nhóm không dừng lại ở mô hình V7 mà phải tốn công sinh lại 6.445 tệp OmniVoice CFM đối xứng 1:1 và thực hiện thí nghiệm hoán đổi hai chiều lên v0.9.4?",
        "Kiểm tra động lực nghiên cứu khoa học nghiêm túc và tính công bằng khi thiết kế thực nghiệm đối chứng.",
        "Dạ thưa Thầy/Cô, chúng em thực hiện thí nghiệm hoán đổi hai chiều với quy mô đối xứng chính xác `6.445 tệp` để **kiểm chứng tính bất đối xứng giữa hai họ mô hình tạo sinh giọng nói hiện đại và vá triệt để lỗ hổng lọt lưới trước Continuous Flow Matching**.",
        "Ở mô hình `V7` (huấn luyện trên `F5-TTS` + `VieNeu-TTS`), dù tổng thể đạt chuẩn sơ bộ nhưng khi kiểm tra diện rộng trên `15.980` mẫu đối xứng, nhánh `OmniVoice CFM` làm tổng EER bị đội lên `13.72%` (riêng OmniVoice chỉ chặn được `75.00%`). Nếu chỉ sinh thêm vài trăm mẫu vá tạm thì phép so sánh sẽ thiếu công bằng khoa học. Vì vậy, chúng em tái sinh trọn bộ **6.445 tệp `OmniVoice_CFM`** khớp 1:1 từng câu, từng người nói và 5 biến thể codec với `VieNeu_TTS` (nâng tổng kho `Voice_Final` lên **103.189 tệp**), rồi hoán đổi hoàn toàn vai trò `Seen ↔ Unseen`.",
        "Kết quả chứng minh thuyết phục trên tập `15.980` mẫu: mô hình chính thức **`v0.9.4`** kéo tổng EER giảm gần 60% tương đối — từ **`13.72%` (V7) → `6.79%` (V8.0 bán phần) → `5.63%` (`v0.9.4`)**, nâng tỷ lệ chặn giả toàn cục lên **95.01%**.",
    )

    _qa(
        24,
        "Vì sao ở chiều thuận (V7: học VieNeu → kiểm tra OmniVoice) mô hình bị lọt lưới nhiều hơn hẳn chiều nghịch (v0.9.4: học OmniVoice → kiểm tra VieNeu)?",
        "Kiểm tra khả năng giải thích hiện tượng thực nghiệm bằng phương trình toán học gốc của bộ tạo sinh âm thanh.",
        "Dạ thưa Thầy/Cô, sự bất đối xứng này bắt nguồn trực tiếp từ **độ trơn liên tục của phương trình vi phân `Optimal Transport ODE` trong `OmniVoice CFM` so với sai số lượng tử hóa bậc thang `e_q ≠ 0` của `Residual Vector Quantization (RVQ)` trong `VieNeu-TTS`**.",
        "Khi mô hình chỉ học các vết gián đoạn thô hơn (như `V7` học trên `VieNeu-TTS`), mặt phân cách của nó đặt ngưỡng dung sai quá rộng nên bỏ lọt những sóng âm trơn mượt giải bằng `ODE` của `OmniVoice CFM` (chỉ có vi nhiễu cắt cụt `O(Δt²)` cực nhỏ ở tần số cao). Ngược lại, khi `v0.9.4` được huấn luyện trực tiếp để vạch trần cả những vi nhiễu siêu nhỏ của `F5-TTS` và `OmniVoice CFM`, mọi sai số làm tròn bậc thang giữa các bảng mã rời rạc `RVQ` của `VieNeu-TTS` đều trở thành dấu hiệu bất thường rất rõ nét đối với đồ thị `HS-GAL`.",
        "Bằng chứng thực nghiệm khẳng định trọn vẹn lý thuyết này: dù `v0.9.4` hoàn toàn chưa từng thấy `VieNeu-TTS`, nó vẫn đạt **12.05% EER** trên tập benchmark `955` mẫu Dev (`≤ 15.0%` KPI H2) và chặn đứng **92.53% (347/375)** mẫu giả `VieNeu-TTS` trên bộ 5 tình nguyện viên độc lập!",
    )

    _qa(
        25,
        "Sự khác biệt giữa hai lượt huấn luyện Run 1 (54.225 dòng) và Run 2 (54.400 dòng) trong v0.9.4 là gì và tại sao nó vẫn bảo toàn tuyệt đối tính khách quan nghiệm thu?",
        "Kiểm tra tính minh bạch trong quản trị các tập dữ liệu huấn luyện và ranh giới cô lập tình nguyện viên.",
        "Dạ thưa Thầy/Cô, hai lượt huấn luyện chỉ khác nhau đúng **175 dòng của tình nguyện viên thứ 6 dư ra (`SPK_0001`)** nhằm đối chứng tác động của độ đa dạng nguồn thu âm thực tế, trong khi **5 tình nguyện viên nghiệm thu chính thức (`SPK_0003..0007`) vẫn được cô lập 100%**.",
        "Ngay từ đầu đồ án, nhóm thu thập tổng cộng 6 tình nguyện viên độc lập và khóa cứng 5 người (`SPK_0003..0007`, 84 tệp gốc / 420 biến thể giọng thật) làm Bộ Nghiệm Thu Độc Lập Chính Thức. Tình nguyện viên thứ 6 còn lại ngoài bộ nghiệm thu (`SPK_0001`, gồm 75 mẫu thật + 50 mẫu F5 + 50 mẫu OmniVoice = 175 dòng) được tách khỏi `Run 1` (`54.225` dòng thuần `VIVOS` + `Common Voice`) để làm đường cơ sở đối chứng, và được đưa vào `Run 2` (`54.400` dòng) để tận dụng tối đa dữ liệu hợp lệ sẵn có mà không vi phạm bất kỳ ranh giới kiểm thử nào.",
        "Thực nghiệm ghi nhận `Run 1` đã hội tụ rất tốt (`Dev EER = 6.32%`), và `Run 2` tiếp tục cải thiện nhẹ `Dev EER` Pha 2 xuống **`5.95%`**, trước khi đi qua bước hiệu chuẩn `head_blend_a0.75` để đạt **5.63% EER** trên tập Test `15.980` mẫu.",
    )

    _qa(
        26,
        "Tại sao ở Giai đoạn 3 (head_blend_a0.75), nhóm chọn đóng băng 100% khối Wav2Vec 2.0 và trộn tuyến tính đầu phân loại thay vì huấn luyện tiếp toàn mạng thêm nhiều epoch?",
        "Kiểm tra hiểu biết về hiện tượng quá khớp (Overfitting), trôi biểu diễn (Representation Drift) và lý thuyết WiSE-FT.",
        "Dạ thưa Thầy/Cô, chúng em đóng băng 100% khối `Wav2Vec 2.0` và chỉ nội suy tuyến tính đầu phân loại (`0.25 · Pha 2 + 0.75 · Head-Only`) nhằm **chỉnh lại tâm biên quyết định về `θ = 0.0` mà không làm trôi hay quá khớp không gian đặc trưng tự giám sát đã hội tụ ở Pha 2**.",
        "Thực nghiệm bóc tách cho thấy nếu mở khóa toàn mạng chạy tiếp trên một tập con cân bằng nhỏ, các tầng Transformer trên cùng sẽ nhanh chóng quá khớp vào phân phối tập nhỏ đó và đánh mất khả năng tổng quát hóa sang công cụ ngoại lai `VieNeu-TTS`. Dựa trên nguyên lý *Weight-Space Ensembles (`WiSE-FT`)*, việc giữ nguyên hoàn toàn ma trận trích xuất đặc trưng `Wav2Vec 2.0` của `Run 2 Pha 2` và chỉ dịch chuyển tuyến tính vector pháp tuyến của mặt phẳng phân loại với hệ số `α = 0.75` giúp khử sạch độ lệch biên âm mà không tốn thêm bất kỳ chi phí tính toán nào lúc suy luận.",
        "Nhờ `head_blend_a0.75`, mô hình `v0.9.4` vừa đảo chiều chặn lại thành công **72.8% (142/195)** ca `OmniVoice` siêu khó ở Cổng 4 (so với `0.5%` của V7), vừa đạt **94.76%** nhận diện đúng giọng thật trên `420` tệp của 5 tình nguyện viên độc lập.",
    )

    _qa(
        27,
        "Từ kết quả của Chương 13, bài học thiết kế quan trọng nhất để phòng thủ trước các công cụ Zero-Day Voice Cloning xuất hiện trong tương lai là gì?",
        "Kiểm tra khả năng đúc kết quy luật khái quát tầm kiến trúc sư hệ thống an ninh AI.",
        "Dạ thưa Thầy/Cô, bài học cốt lõi nhất là: **muốn phòng thủ vững chắc trước các công cụ nhân bản giọng nói chưa từng biết (`Zero-Day TTS`), tập dữ liệu huấn luyện bắt buộc phải bao phủ đại diện của cả những trường phái tạo sinh có quỹ đạo pha trơn mượt nhất (như `Continuous Flow Matching`), kết hợp cơ chế suy luận gộp điểm kiểm tra đồng thuận đa cửa sổ**.",
        "Về mặt toán học, mọi hệ thống tổng hợp giọng nói hiện tại và sắp ra mắt trên thế giới đều quy về hai cơ chế tái tạo tín hiệu chính: giải phương trình vi phân liên tục (`ODE / SDE Flow & Diffusion`) hoặc giải mã chuỗi lượng tử rời rạc (`Discrete Neural Audio Codec`). Thực nghiệm đối xứng hai chiều của chúng em đã chứng minh khi mô hình làm chủ được biên phân cách tinh vi của họ dòng chảy liên tục (`CFM`), nó đồng thời tạo được hàng rào miễn dịch chéo sang họ mã hóa rời rạc (`RVQ`), miễn là ở tầng suy luận không để một cửa sổ khoảng lặng đơn lẻ làm lọt lưới (`nhờ Consensus Asymmetric Veto`).",
        "Định hướng kiến trúc này giúp `ViTrueVoice v0.9.4` đạt chuẩn sẵn sàng triển khai thực tế: **EER nội bộ 5.63% (≤ 8.0%)**, **EER ngoại lai Unseen TTS 12.05% (≤ 15.0%)**, **trung vị độ trễ 0.705s – 1.101s (≤ 3.0s)**, vận hành Docker cục bộ **0 VNĐ** và bảo vệ bởi **392/392 bài kiểm thử tự động**.",
    )

    add_term_glossary(
        doc,
        terms=[
            ("Zero-Day Voice Cloning", "Unseen Next-Generation Synthesis Attack", "Cuộc tấn công mạo danh sử dụng một công cụ nhân bản giọng nói hoàn toàn mới chưa từng có mặt trong tập dữ liệu huấn luyện của hệ thống phòng thủ."),
            ("Representation Drift", "Feature Space Degradation During Over-Tuning", "Hiện tượng các biểu diễn ngữ âm tổng quát của mạng tiền huấn luyện bị biến dạng khi tinh chỉnh quá nhiều vòng trên một tập dữ liệu hẹp."),
            ("Linear Mode Connectivity", "Weight-Space Convex Interpolation Property", "Tính chất hình học cho phép nối thẳng hai nghiệm mạng nơ-ron cùng nhánh tinh chỉnh bằng phép cộng trọng số tuyến tính mà vẫn nằm trong thung lũng sai số thấp."),
        ],
    )
