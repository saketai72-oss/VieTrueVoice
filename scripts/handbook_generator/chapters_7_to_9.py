# -*- coding: utf-8 -*-
"""
Chương 7, 8, 9 của Sổ Tay Kỹ Thuật & Phản Biện Hội Đồng ViTrueVoice v0.9.4:
- Chương 7: Đa dạng sinh học giọng nói (Deep-Voice F0), Độ bền vững dịch cao độ & Cô lập nghiệm thu 5 tình nguyện viên
- Chương 8: Tổng hợp kết quả thực nghiệm chính thức v0.9.4 trên toàn bộ ma trận kiểm định
- Chương 9: Kiến trúc hệ thống C4, Docker cục bộ 0 VNĐ, Áp dụng Gói A AWS & Đạo đức sinh trắc học
"""

from __future__ import annotations

from pathlib import Path

from docx.shared import Pt

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
    omml_sup,
)


def add_chapters_7_to_9(doc, figs: dict | None = None) -> None:
    """Biên soạn Chương 7, 8 và 9 chuẩn v0.9.4 kèm hộp kiến thức nền tảng, OMML, sơ đồ và từ điển."""

    # =========================================================================
    # CHƯƠNG 7: ĐA DẠNG SINH HỌC GIỌNG NÓI, DỊCH CAO ĐỘ & CÔ LẬP NGHIỆM THU 5 SPK
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 7",
        "Đa Dạng Sinh Học Giọng Nói (Deep-Voice F0), Độ Bền Vững Dịch Cao Độ & Cô Lập Nghiệm Thu 5 Tình Nguyện Viên",
    )

    add_styled_paragraph(
        doc,
        "Một mô hình chống giả mạo chỉ đáng tin cậy khi không nhầm lẫn giọng nói trầm ấm tự nhiên của đàn ông trưởng thành thành âm thanh "
        "tổng hợp nhân tạo, đồng thời không bị đánh lừa khi kẻ tấn công chỉnh cao độ lên xuống vài bán cung để né bộ lọc. "
        "Chương 7 phân tích bản chất âm học của tần số cơ bản `F0`, lỗ hổng tấn công dịch cao độ (`Pitch-Shifting Attack`), "
        "chiến lược tăng cường dữ liệu 2 chiều kết hợp nới biên góc `AM-Softmax (m = 0.20)`, và kỷ luật cô lập tuyệt đối 5 tình nguyện viên nghiệm thu độc lập.",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 7.1 Âm học giọng trầm & Tấn công dịch cao độ Pitch-Shifting
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "7.1 Bản Chất Sinh Học Giọng Trầm (F0), Lỗ Hổng Dịch Cao Độ −6 Bán Cung & Giải Pháp Tăng Cường Thuần Thuật Toán",
    )

    add_foundation_primer(
        doc,
        process_name="Phân tích cao độ thanh đới (F0), Formants & Phòng vệ trước tấn công dịch cao độ",
        why_needed=(
            "Trong thực tế triển khai, giọng nói người dùng cực kỳ đa dạng: từ giọng nữ cao đến giọng nam siêu trầm (F0 quanh 85–110 Hz) "
            "thu qua micro điện thoại giá rẻ trong phòng có tiếng vang. Nếu mô hình chỉ quen giọng chuẩn phòng thu VIVOS (130–220 Hz) hoặc thiếu "
            "biến thiên cao độ trong lúc huấn luyện, hai sự cố sẽ xảy ra: (1) Báo nhầm giọng trầm ngoài đời là giọng giả; và (2) Bị qua mặt khi "
            "kẻ gian dùng phần mềm hạ cao độ giọng AI xuống 6 bán cung (−6 semitones)."
        ),
        real_analogy=(
            "Hãy hình dung một bảo vệ chỉ quen nhìn người có chiều cao trung bình 1m65–1m75 mặc áo đồng phục sáng màu. "
            "Khi gặp một vận động viên cao lớn mặc áo khoác tối màu đi từ ngoài mưa vào, người bảo vệ dễ nghi ngờ nhầm là kẻ lạ đột nhập; "
            "ngược lại, nếu kẻ gian cố tình đi khom người thấp xuống để ngụy trang, bảo vệ thiếu kinh nghiệm lại cho qua. "
            "Thay vì phát cho mỗi người một chiếc thẻ đặc cách dễ bị làm giả (bù trừ tĩnh), cách đúng đắn là huấn luyện bảo vệ quan sát cấu trúc khuôn mặt "
            "dưới đủ mọi tư thế và chiều cao (**Tăng cường dữ liệu hai chiều**)."
        ),
        core_points=[
            "**Tần số cơ bản `F0` (Fundamental Frequency / Pitch)**: Tốc độ rung đóng mở của dây thanh đới tính bằng Hertz (`Hz`). Giọng nữ trưởng thành thường đạt `165–255 Hz`, giọng nam phổ thông đạt `100–160 Hz`, còn nhóm giọng nam trầm sâu (`Deep Voice`) có `F0` xuống vùng `85–110 Hz`, khiến các vạch hài âm xếp khít nhau hơn.",
            "**Các dải cộng hưởng `Formants` (`F1, F2, F3`)**: Là các đỉnh năng lượng đặc trưng do hình dáng khoang họng, miệng và mũi tạo thành khi âm thanh đi qua. Dù người nói nói trầm hay cao, tỷ lệ tương đối của các `Formants` và vi dao động pha dây thanh đới sinh học vẫn không mất đi.",
            "**Lệch miền micro ngoài đời (`Out-of-Domain Acoustic Shift`)**: Phòng thu chuẩn có độ vang `RT60` rất thấp và đáp tuyến micro phẳng; trong khi điện thoại thực tế tạo vang phòng và suy hao tần số khác hẳn, làm khuếch đại sai số ở nhóm giọng trầm.",
            "**Nghiên cứu bóc tách (`Ablation Study`)**: Phép kiểm chứng khoa học cô lập từng biến số (cao độ `F0`, vang phòng, loại micro, góc phạt `m`) để bác bỏ nguyên nhân cảm tính và tìm đúng gốc rễ thuật toán.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Chuỗi thực nghiệm bóc tách pháp y âm học (`Forensic Audio Audit`) của dự án đã làm sáng tỏ 3 phát hiện kỹ thuật mang tính bước ngoặt, "
        "định hình trực tiếp kiến trúc huấn luyện của phiên bản chính thức **`ViTrueVoice v0.9.4`**:",
    )

    add_bullet_item(
        doc,
        "Khi đo phổ năng lượng trên các mẫu giọng trầm thu từ điện thoại thực tế, hơn `60%–65%` năng lượng tập trung dưới `250–300 Hz`. "
        "Tuy nhiên, thực nghiệm đối chứng chứng minh **`F0` thấp không phải là nguyên nhân duy nhất** khiến mô hình đời đầu nhạy cảm: chính sự cộng hưởng "
        "giữa âm vực trầm, đáp tuyến micro điện thoại không phẳng và áp lực góc phạt quá khắt khe (`AM-Softmax m = 0,35` ở phiên bản thử nghiệm cũ) "
        "đã đẩy các mẫu giọng trầm hợp lệ sát ra rìa vùng quyết định `θ = 0,0`.",
        "1. Bác bỏ giả thuyết đơn nhân tố (F0 không phải thủ phạm duy nhất)",
    )
    add_bullet_item(
        doc,
        "Thử nghiệm kiểm tra tấn công đối kháng thực tế bằng cách dịch cao độ các mẫu giọng giả xuống nửa quãng tám (`−6 bán cung / semitones`) "
        "cho thấy phiên bản cũ từng sụp đổ mạnh về độ phân tách: chỉ số `ROC-AUC` tụt từ `0,9895` xuống còn `0,6717`, kéo theo `EER` tăng vọt lên `43%` "
        "và tỷ lệ lọt lưới giả `APCER` chạm `62%`! Đồng thời, việc dùng các bộ lọc bù điểm tĩnh thủ công lúc suy luận đã làm phá vỡ phân phối xác suất đầu ra.",
        "2. Phát hiện lỗ hổng nghiêm trọng trước tấn công hạ cao độ −6 bán cung (`Pitch-Shift −6st`)",
    )
    add_bullet_item(
        doc,
        "Thay vì can thiệp thô bạo lúc suy luận hay thu thập tràn lan dữ liệu tình nguyện viên mới, hệ thống giải quyết triệt để từ gốc lúc huấn luyện bằng 2 biện pháp: "
        "(a) **Tăng cường dịch cao độ hai chiều thuần thuật toán (`Bidirectional Pitch & Codec Data Augmentation`)** trong tập Train kết hợp cùng `RawBoost` "
        "và 5 kênh nén thoại; (b) **Nới biên độ phạt góc `AM-Softmax` từ `m = 0,35` về mức cân bằng `m = 0,20` (`s = 30,0`)** để mở rộng vùng an toàn cho các biến thể giọng trầm tự nhiên mà vẫn giữ chặt ranh giới chống giả.",
        "3. Giải pháp triệt để v0.9.4: Tăng cường dịch cao độ hai chiều & Nới biên góc m = 0,20",
    )

    pitch_eq = (
        omml_sub(omml_r("f"), omml_r("new", normal=True))
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("f"), omml_r("0", normal=True))
        + omml_r(" · ", normal=True)
        + omml_sup(
            omml_r("2", normal=True),
            omml_frac(omml_r("n"), omml_r("12", normal=True)),
        )
    )
    add_omml_equation(
        doc,
        "Công thức biến đổi tần số cơ bản theo thang bán cung (Semitone Pitch-Shift Law)",
        pitch_eq,
        variables=[
            ("f_0", "Tần số cơ bản ban đầu của sóng giọng nói tính bằng Hz (ví dụ giọng nam phổ thông 130 Hz hoặc giọng giả gốc)."),
            ("n", "Số bán cung dịch chuyển âm thanh (`n < 0` là hạ trầm, ví dụ `n = −6` tương đương giảm đi đúng nửa quãng tám; `n > 0` là nâng cao thanh)."),
            ("f_new", "Tần số mới sau biến đổi: khi `n = −6`, hệ số nhân bằng `2^(−0,5) ≈ 0,7071`, tức giọng 130 Hz bị kéo trầm xuống còn ~91,9 Hz."),
        ],
    )

    add_term_glossary(
        doc,
        [
            ("F0 / Pitch", "Fundamental Frequency", "Tần số cơ bản của dao động dây thanh đới, quyết định cảm giác giọng trầm hay bổng khi nghe."),
            ("Formants (F1, F2, F3)", "Acoustic Resonance Peaks", "Các đỉnh tần số cộng hưởng của ống thanh quản tạo nên màu sắc riêng cho từng nguyên âm và âm sắc cá nhân."),
            ("Semitone (Bán cung)", "1/12 of an Octave", "Đơn vị đo bước nhảy cao độ âm nhạc; 12 bán cung tương ứng tăng hoặc giảm gấp đôi tần số (1 quãng tám)."),
            ("Pitch-Shift Augmentation", "Bidirectional Frequency Scaling", "Kỹ thuật mô phỏng tăng/giảm cao độ hai chiều ngay trên dữ liệu huấn luyện nhằm giúp mạng nơ-ron miễn nhiễm với chiêu trò bóp méo giọng nói."),
            ("ROC-AUC", "Area Under the Receiver Operating Characteristic Curve", "Diện tích dưới đường cong đánh giá khả năng xếp hạng tách biệt giữa lớp Giọng Thật và Giọng Giả (từ 0,50 đoán mò tới 1,00 lý tưởng)."),
        ],
    )

    # -------------------------------------------------------------------------
    # 7.2 Kỷ luật cô lập 5 Tình nguyện viên nghiệm thu độc lập & Thử nghiệm LOSO
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "7.2 Kỷ Luật Cô Lập Tuyệt Đối 5 Tình Nguyện Viên Nghiệm Thu Độc Lập & Bài Học Thử Nghiệm LOSO",
    )

    add_foundation_primer(
        doc,
        process_name="Kiểm định loại trừ người nói (LOSO) & Kỷ luật niêm phong bộ dữ liệu nghiệm thu độc lập",
        why_needed=(
            "Trong nghiên cứu AI chống giả mạo sinh trắc học, sai lầm lớn nhất làm mất giá trị khoa học của đồ án là để dữ liệu của những người "
            "nằm trong bộ nghiệm thu cuối cùng lọt vào tập huấn luyện hoặc bước chọn ngưỡng. Mục này giải thích minh bạch cách đồ án phân tách ranh giới "
            "6 tình nguyện viên thu âm trực tiếp và kết quả kiểm chứng thực nghiệm từ giao thức tiền đăng ký LOSO."
        ),
        real_analogy=(
            "Tưởng tượng trường đại học thành lập một đề thi thực hành chuẩn quốc gia với **5 giám khảo độc lập** chấm bài cuối khóa. "
            "Danh tính và bộ câu hỏi của 5 giám khảo này được niêm phong tuyệt đối bên ngoài lớp ôn thi. Do chỉ cần 5 người cho hội đồng nghiệm thu "
            "nên 1 tình nguyện viên thứ 6 còn dư ngoài danh sách được đưa vào kho bài tập ôn luyện hợp lệ, còn 5 người nghiệm thu kia vẫn sạch bóng 100% đến tận ngày chấm điểm."
        ),
        core_points=[
            "**Kiểm định chéo loại trừ từng người (`Leave-One-Speaker-Out — LOSO`)**: Lần lượt huấn luyện trên tất cả các người nói trừ 1 người, rồi chấm điểm trên chính người bị giữ lại để đo trung thực khả năng khái quát hóa giữa các cá nhân.",
            "**Đặc tả tiền đăng ký (`Pre-registered Protocol`)**: Mọi ngưỡng đạt/không đạt và tiêu chí đánh giá phải được chốt bằng văn bản trước khi bấm nút chạy GPU, nghiêm cấm nhìn kết quả rồi sửa tiêu chuẩn.",
            "**Vệ sinh dữ liệu (`Data Hygiene`)**: Rà soát kiểm tra toàn bộ tệp âm thanh qua chữ ký băm `SHA-256` để bảo đảm 0% tệp mô phỏng hoặc tệp kiểm thử bị lẫn vào kho huấn luyện.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Từ giai đoạn chuẩn bị hạ tầng dữ liệu, dự án tiến hành thí nghiệm thăm dò **`LOSO` 4 Folds (`48 lượt chạy`)** tuân thủ nghiêm ngặt đặc tả tiền đăng ký: "
        "kết quả xác nhận tuy có xu hướng chuyển giao điểm số dương trên người nói bị giữ lại, nhưng đổi lại làm `Dev EER` và tỷ lệ lọt lưới `APCER` toàn cục "
        "vượt quá ngưỡng an ninh cho phép (`0/4 Folds` đạt chuẩn an toàn). Thực nghiệm này cung cấp **bằng chứng khoa học vững chắc** củng cố cho nguyên tắc cốt lõi "
        "bất khả xâm phạm (`STUBBORN_FACT`) của toàn đồ án:",
    )

    add_bullet_item(
        doc,
        "Từ tổng số **6 tình nguyện viên** đã ký Phiếu đồng thuận sinh trắc học thu âm trực tiếp (`SPK_0001`, `SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`), "
        "nhóm khóa cứng **5 tình nguyện viên (`SPK_0003..0007`, gồm `84` clip giọng thật gốc × `5` biến thể codec = `420` tệp bonafide, cộng `1.125` tệp spoof ghép cặp = `1.545` tệp)** "
        "làm **Bộ Nghiệm Thu Độc Lập Chính Thức** — cô lập **100%** khỏi tập Train, tập Dev, hiệu chuẩn đầu phân loại `head_blend_a0.75`, hiệu chuẩn `Platt Scaling` và bước chọn ngưỡng `θ = 0,0`.",
        "1. Niêm phong tuyệt đối 5 Tình nguyện viên nghiệm thu (`SPK_0003..0007`)",
    )
    add_bullet_item(
        doc,
        "Do bộ nghiệm thu độc lập đã khóa đủ 5 tình nguyện viên theo thiết kế ban đầu, tình nguyện viên thứ 6 còn dư ngoài bộ nghiệm thu "
        "(`SPK_0001`, gồm `175` dòng qua 5 kênh truyền: `75` bonafide + `50` `F5-TTS` + `50` `OmniVoice CFM`) được đưa vào tập huấn luyện chính thức "
        "(`train_v8_f5_omni_with_spk1.csv`, tổng quy mô **`54.400` dòng**, song song đối chứng với tập công khai `54.225` dòng `train_v8_f5_omni_no_spk1.csv`).",
        "2. Bố trí tình nguyện viên thứ 6 dư ra (`SPK_0001`) vào tập Train chính thức",
    )
    add_bullet_item(
        doc,
        "Kho lưu trữ `Voice_Final` (`103.189` tệp âm thanh) cùng 5 tệp manifest chuẩn `19 cột` đều trải qua quy trình rà soát mã băm `SHA-256`, "
        "tách cô lập mọi tệp nháp thử nghiệm và kiểm tra tự động `0%` chồng lấn người nói lẫn văn bản giữa tập huấn luyện và 5 tình nguyện viên nghiệm thu.",
        "3. Đảm bảo vệ sinh dữ liệu & Không rò rỉ 100% (`0% Leakage`)",
    )

    add_callout_box(
        doc,
        "Nếu Hội đồng hỏi: **\"Làm sao đảm bảo mô hình `v0.9.4` không học vẹt giọng của các bạn tình nguyện viên?\"**, hãy khẳng định dứt khoát: "
        "*\"Dạ thưa Thầy/Cô, đồ án tách rạch ròi 2 lớp bảo vệ dữ liệu: 5 tình nguyện viên `SPK_0003..0007` (tổng 1.545 tệp qua 5 kênh codec cho cả giọng thật lẫn 3 công cụ giả mạo) "
        "được niêm phong hoàn toàn khỏi toàn bộ quá trình huấn luyện, hiệu chuẩn `head_blend_a0.75` và chọn ngưỡng; còn 1 tình nguyện viên thứ 6 dư ngoài danh sách (`SPK_0001`, 175 tệp) "
        "được đưa vào tập Train `54.400` dòng và kiểm chứng đối chứng song song với Run 1 thuần dữ liệu công khai `54.225` dòng.\"*",
        title="BÍ QUYẾT PHẢN BIỆN CHƯƠNG 7: MINH BẠCH RANH GIỚI 6 TÌNH NGUYỆN VIÊN & ĐỘ BỀN CAO ĐỘ",
    )

    add_term_glossary(
        doc,
        [
            ("LOSO", "Leave-One-Speaker-Out Cross-Validation", "Phương pháp kiểm định khoa học giữ riêng hoàn toàn từng người nói ra ngoài lúc huấn luyện để đo năng lực chuyển giao thực chất sang người mới."),
            ("Pre-registered Protocol", "Đặc tả tiền đăng ký khoa học", "Kế hoạch thực nghiệm chốt cứng giả thuyết, dữ liệu và ngưỡng đạt chuẩn từ trước khi chạy để ngăn chặn việc chỉnh tiêu chí chạy theo kết quả."),
            ("Data Hygiene", "Vệ sinh dữ liệu huấn luyện", "Quy trình kiểm toán định kỳ bằng mã băm SHA-256 và đối soát ranh giới tập chia nhằm loại bỏ 100% rò rỉ nhãn hoặc tệp lỗi."),
            ("Isolated Acceptance Set", "Bộ nghiệm thu cô lập hoàn toàn", "Tập 5 tình nguyện viên `SPK_0003..0007` không bao giờ tham gia huấn luyện, điều chỉnh siêu tham số hay hiệu chuẩn xác suất."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 8: TỔNG HỢP KẾT QUẢ THỰC NGHIỆM CHÍNH THỨC v0.9.4
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 8",
        "Tổng Hợp Kết Quả Thực Nghiệm Chính Thức v0.9.4 Trên Toàn Bộ Ma Trận Kiểm Định",
    )

    add_styled_paragraph(
        doc,
        "Chương 8 tổng hợp đầy đủ các bảng số liệu thực nghiệm đã kiểm chứng từ mã nguồn đánh giá (`scripts/eval_v8_1_benchmark.py` và "
        "`benchmarks/v8_1_vs_v7_benchmark.json`), bao trùm cả 4 trục đánh giá: (1) Tiến hóa kiến trúc qua các nhánh thực nghiệm đối chứng, "
        "(2) Đánh giá quy mô lớn `15.980` mẫu In-domain qua đủ 5 kênh truyền, (3) Kiểm chứng Giả thuyết H2 trên động cơ ngoại lai `VieNeu-TTS v3 Turbo`, "
        "và (4) Ma trận nghiệm thu độc lập 5 tình nguyện viên (`1.545` tệp).",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 8.1 Hướng dẫn đọc ma trận kiểm định & Tiến hóa kiến trúc
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "8.1 Phương Pháp Đọc Ma Trận Kiểm Định Đa Trục & Bảng Tiến Hóa Các Thế Hệ Mô Hình",
    )

    add_foundation_primer(
        doc,
        process_name="Đọc hiểu Ma trận đánh giá đa trục (In-domain 15.980 vs. OOD 955 vs. Nghiệm thu 5 SPK 1.545)",
        why_needed=(
            "Tại buổi bảo vệ, bảng kết quả gồm nhiều chiều (EER theo codec, EER theo công cụ TTS, tỷ lệ chặn tại ngưỡng θ = 0.0, BPCER trên người thật). "
            "Nếu không phân biệt rõ vai trò của từng tập kiểm định, sinh viên rất dễ đọc nhầm số liệu giữa tập In-domain và tập ngoại lai OOD."
        ),
        real_analogy=(
            "Giống như đánh giá chất lượng một chiếc xe ô tô điện trước khi thương mại hóa: "
            "(1) Đường thử tiêu chuẩn dài 15.980 km đủ 5 loại mặt đường từ cao tốc phẳng đến đường đất đá lồi lõm (`Test In-domain 15.980` qua 5 codecs); "
            "(2) Thử nghiệm đổ đèo bất ngờ bằng một loại trạm sạc chuẩn mới chưa từng lập trình sẵn (`Unseen VieNeu-TTS 955 mẫu — H2 OOD`); "
            "(3) Mời 5 tài xế tình nguyện hoàn toàn độc lập lái thử ngoài đời thực trên mọi cung đường (`Bộ 5 SPK nghiệm thu 1.545 tệp`)."
        ),
        core_points=[
            "**Tập Kiểm Thử Nội Bộ (`In-domain Test = 15.980` mẫu / lát cắt không trùng câu mồi `eval_only = 15.665` mẫu)**: Đo sức bền toàn diện trước cả 2 công cụ đã học (`F5-TTS` + `OmniVoice CFM`) qua 5 cấu hình kênh nén (`Clean`, `Zalo AAC 76k`, `Zalo Opus 24k`, `G.711`, `AMR-NB`). Mục tiêu `H1`: `EER ≤ 8,0%`.",
            "**Tập Kiểm Định Ngoại Lai (`Unseen OOD = 955` mẫu `VieNeu-TTS` + `2.000` mẫu thật Dev)**: Đo năng lực bắt động cơ chưa từng xuất hiện trong lúc học. Mục tiêu `H2`: `EER ≤ 15,0%`.",
            "**Bộ Nghiệm Thu Độc Lập 5 Tình Nguyện Viên (`5 SPK = 1.545` tệp = `420` Bonafide + `375` F5 + `375` OmniVoice + `375` VieNeu)**: Đo hiệu năng thực chiến trên giọng người Việt thu âm trực tiếp cô lập 100%, kiểm tra cả bản gốc sạch (`309` tệp) lẫn tổng hợp đủ 5 biến thể kênh thoại.",
            "**Chỉ số tổng hợp (`Pooled`) vs. Chỉ số trung bình từng người (`Macro`)**: `Pooled` gộp tất cả các clip vào một phân phối lớn để tính `EER`; `Macro` tính riêng trên từng cá nhân rồi mới lấy trung bình để không bị một người nhiều clip lấn át.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Bảng 8.1 tóm tắt hành trình tiến hóa thực nghiệm của đồ án từ bài toán cơ sở cổ điển đến phiên bản phát hành chính thức **`ViTrueVoice v0.9.4`** "
        "(chạy dưới cơ chế gộp chuẩn sản xuất `Consensus Asymmetric Veto` trên ma trận đánh giá `15.980` mẫu đối xứng và tập kiểm chứng ngoại lai H2):",
    )

    add_styled_table(
        doc,
        headers=[
            "Thế Hệ / Nhánh Thử Nghiệm",
            "Đặc Trưng Kỹ Thuật Chính",
            "In-Domain Test EER (15.980 mẫu)",
            "Chặn Giả Mạo Tại θ = 0.0",
            "Kiểm Định Unseen H2 (OOD)",
        ],
        rows=[
            (
                "Nhánh A (Baseline Clean-Only)",
                "SSL-AASIST chỉ học âm thanh phòng thu sạch (không nén, không RawBoost)",
                "14,85% (AMR-NB) – 16,20% (G.711)",
                "Sụp đổ qua kênh 8kHz",
                "EER = 26,34% (Không đạt H2)",
            ),
            (
                "Nhánh B0 (Có Codec, Không RawBoost)",
                "Bổ sung nén 5 kênh thoại nhưng tắt tăng cường nhiễu sóng RawBoost",
                "10,12% (AMR-NB) – 11,05% (G.711)",
                "Cải thiện trung bình",
                "EER = 23,10%",
            ),
            (
                "Nhánh B (Đề xuất gốc Giai đoạn đầu)",
                "SSL-AASIST + Nén kênh thoại + RawBoost (F5-TTS đơn lẻ)",
                "3,28% (tập Clean) – 8,84% (AMR-NB)",
                "Giảm 40,5% – 47,6% lỗi (H1 PASS)",
                "EER = 21,88%",
            ),
            (
                "Thế hệ V7 Best (Dual-Seen F5 + VieNeu)",
                "Seen = {F5-TTS, VieNeu-TTS} + Consensus Asymmetric Veto",
                "13,72% EER (OmniVoice bị lọt 25%)",
                "87,22% tổng thể (Omni 75,00%)",
                "Đảo chiều Omni 195 ca khó chỉ đạt 0,5%",
            ),
            (
                "Thế hệ V8.0 Legacy (Bán phần CFM)",
                "Seen = {F5-TTS, OmniVoice 1.885 tệp} + Layer-Wise Grafting",
                "6,79% EER (OmniVoice 8,84%)",
                "90,33% tổng thể (Omni 82,41%)",
                "Dữ liệu CFM chưa đủ đối xứng 1:1",
            ),
            (
                "**ViTrueVoice v0.9.4 (Chính thức)**",
                "**Seen đối xứng 6.445 Omni + F5, 2-Run + `head_blend_a0.75` + Consensus Veto**",
                "**5,63% EER** (`eval_only`: **5,61%**) — ĐẠT ≤ 8,0%",
                "**95,01%** (`F5`: **98,49%**, `Omni`: **91,52%**)",
                "**12,05% EER** (`VieNeu 955` — **H2 PASS ≤ 15%**) | G4: **72,8%**",
            ),
        ],
        col_widths=[1.45, 1.80, 1.25, 1.15, 1.05],
        highlight_row_pred=lambda idx, _: idx == 5,
    )

    add_styled_paragraph(
        doc,
        "*(Ghi chú: Hai cột đầu của Baseline Nhánh A/B0/B đo trên tập đối chứng giai đoạn W05 gồm F5-TTS và mạng thoại nén; từ V7 trở đi toàn bộ hệ thống được "
        "chấm điểm đồng nhất trên ma trận đối xứng lớn `15.980` mẫu gồm cả `F5-TTS` lẫn `OmniVoice CFM` tại `benchmarks/v8_1_vs_v7_benchmark.json`).*",
        font_size=9.2,
        italic=True,
        color_rgb=(85, 90, 100),
        space_after=6,
    )

    # -------------------------------------------------------------------------
    # 8.2 Kết quả chi tiết 15.980 mẫu qua 5 Codecs & Kiểm định H2
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "8.2 Kết Quả Chi Tiết Trên 15.980 Mẫu Test Qua 5 Kênh Nén & Kiểm Định Ngoại Lai H2 (VieNeu-TTS)",
    )

    add_styled_paragraph(
        doc,
        "Bảng 8.2 bóc tách hiệu năng của mô hình chính thức **`v0.9.4`** (`asymmetric_veto`, `θ = 0,0`) trên toàn bộ **`15.980` tệp kiểm thử nội bộ** "
        "(`13.735` mẫu giọng thật + `1.125` `F5-TTS` + `1.120` `OmniVoice CFM`) qua từng kênh truyền thực tế. Toàn bộ cả 5 biến thể nén đều đạt "
        "`EER` dao động từ **`4,88%` đến `6,11%`**, giữ vững biên độ an toàn sâu bên dưới ngưỡng `≤ 8,0%` của Giả thuyết H1:",
    )

    add_styled_table(
        doc,
        headers=[
            "Biến Thể Kênh Truyền / Phân Tập",
            "Quy Mô Mẫu (Thật / Giả)",
            "EER v0.9.4 (%)",
            "Tỷ Lệ Chặn Spoof (%)",
            "BPCER Báo Nhầm Thật (%)",
        ],
        rows=[
            (
                "1. Kênh Chuẩn Không Nén (`clean_16khz`)",
                "2.789 Thật / 449 Giả",
                "**5,52%**",
                "95,55%",
                "6,96%",
            ),
            (
                "2. Kênh Zalo Tệp Đính Kèm (`aac_zalo_76k`)",
                "2.789 Thật / 449 Giả",
                "**5,79%**",
                "95,77%",
                "9,14%",
            ),
            (
                "3. Kênh Zalo Tin Nhắn Thoại (`opus_zalo_24k`)",
                "2.789 Thật / 449 Giả",
                "**6,02%**",
                "94,65%",
                "6,85%",
            ),
            (
                "4. Kênh Điện Thoại Cố Định PSTN (`g711_alaw`)",
                "2.789 Thật / 449 Giả",
                "**6,11%**",
                "93,32%",
                "5,18%",
            ),
            (
                "5. Kênh Di Động GSM Băng Hẹp (`amr_nb`)",
                "2.789 Thật / 449 Giả",
                "**4,88%**",
                "95,77%",
                "5,40%",
            ),
            (
                "Nhánh Công Cụ Seen: `F5-TTS-Vietnamese`",
                "13.735 Thật / 1.125 Giả",
                "**2,81%**",
                "**98,49%** (1.108/1.125)",
                "6,73%",
            ),
            (
                "Nhánh Công Cụ Seen: `OmniVoice CFM`",
                "13.735 Thật / 1.120 Giả",
                "**7,95%**",
                "**91,52%** (1.025/1.120)",
                "6,73%",
            ),
            (
                "**TỔNG HỢP TOÀN BỘ TẬP TEST (`full_15980`)**",
                "**13.735 Thật / 2.245 Giả**",
                "**5,63%** (`minDCF = 0,3842`)",
                "**95,01%** (2.133/2.245)",
                "**6,73%** (924/13.735)",
            ),
        ],
        col_widths=[2.05, 1.25, 1.15, 1.15, 1.10],
        highlight_row_pred=lambda idx, _: idx == 7,
    )

    add_styled_paragraph(
        doc,
        "Đối với **Giả thuyết H2** (kiểm định trên công cụ chưa từng xuất hiện trong tập Train hay Dev là **`VieNeu-TTS v3 Turbo`** dùng kiến trúc mã hóa "
        "rời rạc `NeuCodec`) và **Cổng 4 (`OmniVoice Reversal`)**:",
    )
    add_bullet_item(
        doc,
        "Trên `unseen_vieneu_benchmark.csv` (`955` mẫu giả `VieNeu-TTS` qua 5 codecs đối chiếu với `2.000` mẫu thật Dev), mô hình `v0.9.4` dưới chế độ "
        "`Consensus Asymmetric Veto` đạt **`EER = 12,05%` (`≤ 15,0%` H2 PASS)**, chặn đứng **`79,58%` (`760/955`)** mẫu giả tại ngưỡng `θ = 0,0` "
        "(điểm trung bình mẫu giả = `−9,46`, trung vị = `−14,08`, trong khi điểm trung bình giọng thật Dev = `+14,10` và `BPCER = 6,00%`).",
        "1. Cổng 3 — Kiểm định H2 Unseen `VieNeu-TTS v3 Turbo` (955 mẫu Dev)",
    )
    add_bullet_item(
        doc,
        "Trên lát cắt `195` mẫu giả `OmniVoice CFM` khó nhất từng vượt qua mô hình V7 (`V7` chỉ chặn được `0/195` với `max` và `1/195` với `veto`), "
        "mô hình `v0.9.4` đảo chiều chặn lại thành công **`72,82%` (`142/195`)** dưới `asymmetric_veto` và **`74,36%` (`145/195`)** dưới `mean`.",
        "2. Cổng 4 — Tỷ lệ đảo chiều các ca `OmniVoice` siêu khó (`195` mẫu)",
    )

    # -------------------------------------------------------------------------
    # 8.3 Ma trận nghiệm thu độc lập 5 Tình nguyện viên (1.545 tệp & 309 Clean)
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "8.3 Ma Trận Nghiệm Thu Độc Lập 5 Tình Nguyện Viên Cô Lập 100% (`SPK_0003..0007` — 1.545 Tệp / 5 Codecs)",
    )

    add_styled_paragraph(
        doc,
        "Để bảo chứng hiệu năng thực tiễn hoàn toàn tách biệt khỏi các kho dữ liệu học thuật công khai, **5 tình nguyện viên nghiệm thu độc lập (`SPK_0003..0007`)** "
        "được kiểm tra qua ma trận đầy đủ **5 người nói × 4 nguồn âm thanh** (`Giọng thật Bonafide`, `F5-TTS`, `OmniVoice CFM`, `VieNeu-TTS`) "
        "trên cả hai lát cắt: **bản gốc sạch không nén (`309` tệp)** và **toàn bộ 5 biến thể kênh thoại (`1.545` tệp)**.",
    )

    add_styled_table(
        doc,
        headers=[
            "Hạng Mục Nghiệm Thu 5 SPK (`asymmetric_veto`, θ = 0.0)",
            "Cột 1: Giọng Thật (`Bonafide`)",
            "Cột 2: Seen `F5-TTS`",
            "Cột 3: Seen `OmniVoice CFM`",
            "Cột 4: Unseen `VieNeu-TTS` (H2)",
        ],
        rows=[
            (
                "**Toàn Bộ 5 Kênh Codec (`1.545` tệp)**\n*(Clean, Zalo AAC, Zalo Opus, G.711, AMR-NB)*",
                "**94,76% đúng (398/420)**\n`BPCER = 5,24%` | Điểm TB `+14,44`",
                "**100,00% chặn (375/375)**\n`APCER = 0,00%` | EER **2,67%**",
                "**83,47% chặn (313/375)**\n`APCER = 16,53%` | EER **11,67%**",
                "**92,53% chặn (347/375)**\n`APCER = 7,47%` | EER **6,90%**",
            ),
            (
                "**Lát Cắt Bản Gốc Sạch (`309` tệp)**\n*(84 Thật + 75 F5 + 75 Omni + 75 VieNeu)*",
                "**95,24% đúng (80/84)**\n*(Chế độ `max`: **98,81%** 83/84; 4 SPK `0004..0007`: **100%** 64/64)*",
                "**100,00% chặn (75/75)**\nKhông lọt 1 mẫu nào",
                "**88,00% chặn (66/75)**\nChặn tốt ngay trên âm thanh gốc",
                "**94,67% chặn (71/75)**\nChặn xuất sắc công cụ lạ",
            ),
        ],
        col_widths=[1.75, 1.25, 1.20, 1.25, 1.25],
        highlight_row_pred=lambda idx, _: True,
    )

    add_styled_paragraph(
        doc,
        "Chi tiết kết quả nhận diện giọng người thật **trên từng tình nguyện viên độc lập (`84` tệp gốc sạch của `SPK_0003..0007`)** "
        "tại `benchmarks/v8_1_vs_v7_benchmark.json` chứng minh sự ổn định đồng đều trên nhiều chất giọng nam/nữ khác nhau (Bảng 8.4):",
    )

    add_styled_table(
        doc,
        headers=[
            "Tình Nguyện Viên Cô Lập 100%",
            "Số Clip Gốc Kiểm Định",
            "Số Clip Đúng (v0.9.4 Veto)",
            "Tỷ Lệ Đạt (`Pass Rate`)",
            "Điểm Biên Thô Trung Bình",
        ],
        rows=[
            ("`SPK_0003`", "20", "16", "80,00%", "**+9,13** *(chế độ `max`: 19/20 = 95,0%)*"),
            ("`SPK_0004`", "14", "14", "**100,00%**", "**+15,51**"),
            ("`SPK_0005`", "20", "20", "**100,00%**", "**+14,88**"),
            ("`SPK_0006`", "10", "10", "**100,00%**", "**+20,80**"),
            ("`SPK_0007`", "20", "20", "**100,00%**", "**+14,90**"),
            ("**Tổng hợp 4 SPK tiêu chuẩn (`0004..0007`)**", "**64**", "**64**", "**100,00% (64/64)**", "Biên dương an toàn ổn định"),
            ("**Tổng hợp cả 5 SPK Nghiệm Thu (`0003..0007`)**", "**84**", "**80**", "**95,24%** *(max: **98,81%**)*", "*(G1 tham chiếu `SPK_0001`: 14/15 = **93,33%**, mean +12,28)*"),
        ],
        col_widths=[1.65, 1.0, 1.15, 1.35, 1.55],
        highlight_row_pred=lambda idx, _: idx in (5, 6),
    )

    if figs and "fig8" in figs:
        add_figure(
            doc,
            figs["fig8"],
            "Hình 8.1: Tổng quan hiệu năng kiểm định chính thức ViTrueVoice v0.9.4. Khung A (Trái): So sánh EER qua 5 biến thể kênh thoại trên 15.980 mẫu "
            "giữa V7 Best (13,72%), V8.0 Legacy (6,79%) và v0.9.4 Chính thức (5,63%) vượt xa ngưỡng mục tiêu ≤ 8,0%. Khung B (Phải): Tỷ lệ nhận diện đúng "
            "giọng thật (94,76%) và chặn đứng 3 công cụ giả mạo (F5-TTS 100%, OmniVoice 83,47%, Unseen VieNeu-TTS 92,53%) trên 1.545 tệp của 5 tình nguyện viên độc lập.",
        )

    add_callout_box(
        doc,
        "**TỔNG KẾT BẰNG CHỨNG ĐỊNH LƯỢNG ĐẠT 100% KPI ĐỒ ÁN (v0.9.4)**:\n"
        "• **Giả thuyết H1 (PASS)**: Giảm > 40% EER nén ở giai đoạn bóc tách gốc và đạt **`5,63% EER ≤ 8,0%`** trên ma trận lớn `15.980` mẫu qua cả 5 codecs (`4,88% – 6,11%`).\n"
        "• **Giả thuyết H2 (PASS)**: Đạt **`12,05% EER ≤ 15,0%`** trên `955` mẫu Unseen `VieNeu-TTS v3 Turbo` (chặn `79,6%`) và chặn **`92,53%`** trên bộ 5 tình nguyện viên.\n"
        "• **Nghiệm thu độc lập (PASS)**: Trên `1.545` tệp cô lập 100% của 5 tình nguyện viên (`SPK_0003..0007`), nhận diện đúng người thật **`94,76%`** (gốc **`95,24%`**, `max` **`98,81%`**) "
        "và chặn đứng giả mạo từ **`83,47%`** (`OmniVoice CFM`) tới **`100,00%`** (`F5-TTS`).",
        title="BẢNG VÀNG CHỈ SỐ CHỨNG MINH THÀNH CÔNG KHOA HỌC CỦA VITRUEVOICE v0.9.4",
    )

    add_term_glossary(
        doc,
        [
            ("In-Domain vs. OOD", "Phân biệt miền kiểm thử", "`In-domain` đánh giá trên người nói/câu nói mới thuộc họ TTS đã học; `OOD (Out-of-Distribution)` đánh giá trên động cơ TTS mới hoàn toàn chưa từng gặp."),
            ("Paired Codec Matrix", "Ma trận kiểm thử ghép cặp 5 kênh nén", "Bộ kiểm định nhân bản mỗi câu thoại gốc sang đủ 5 biến thể kênh truyền (`Clean`, `AAC`, `Opus`, `G.711`, `AMR-NB`) liên kết qua `base_utt`."),
            ("Macro vs. Pooled Metric", "Cách tổng hợp chỉ số nhiều người nói", "`Pooled` gộp tất cả clip rồi tính chung 1 tỷ lệ; `Macro` tính riêng trên từng cá nhân trước rồi mới lấy trung bình."),
            ("Wilson Score Interval", "Khoảng tin cậy tỷ lệ nhị phân Wilson", "Phương pháp tính khoảng tin cậy 95% chính xác hơn công thức chuẩn tắc khi tỷ lệ thành công tiến sát 95%–100% trên cỡ mẫu vừa."),
            ("Margin Gap (Δ_margin)", "Khoảng cách tách biệt trung bình Hai lớp", "Hiệu số `μ_bonafide − μ_spoof` đo độ rộng vùng đệm an toàn giữa đám mây điểm giọng thật và đám mây điểm giọng giả."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 9: KIẾN TRÚC C4, DOCKER CỤC BỘ 0 VNĐ, AWS GÓI A & ĐẠO ĐỨC SINH TRẮC HỌC
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 9",
        "Kiến Trúc Hệ Thống C4, Docker Cục Bộ 0 VNĐ, Áp Dụng Gói A AWS & Đạo Đức Sinh Trắc Học",
    )

    add_styled_paragraph(
        doc,
        "Để đưa mô hình `SSL-AASIST v0.9.4` từ phòng thí nghiệm thành hệ thống ứng dụng an ninh tin cậy cho người dùng mạng xã hội Việt Nam, "
        "kiến trúc triển khai phải giải quyết đồng thời 3 bài toán: đóng gói chuẩn hóa để chạy ổn định với **chi phí `0 VNĐ`**, "
        "bảo vệ **quyền riêng tư sinh trắc học theo Luật 91/2025/QH15**, và tích hợp bài bản các nguyên lý kiến trúc - an ninh từ **3 chứng chỉ AWS Academy Gói A**.",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=7,
    )

    # -------------------------------------------------------------------------
    # 9.1 Kiến trúc C4 Mức 2 & Giao diện Dual-Mode Lab
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "9.1 Kiến Trúc C4 Mức 2 (Container Diagram), Hai Chế Độ Lab Web & Telegram Bot",
    )

    add_foundation_primer(
        doc,
        process_name="Kiến trúc phần mềm C4 Mức 2, Đóng gói Docker, API phi trạng thái & Xử lý trên RAM",
        why_needed=(
            "Nhiều sinh viên xây dựng mô hình AI chính xác nhưng khi trình diễn bị lỗi 'chạy trên máy em được mà qua máy khác hỏng thư viện', "
            "hoặc lưu tạm tệp ghi âm của người dân lên ổ cứng gây rủi ro lộ dữ liệu sinh trắc học. Mục này giúp bạn nắm chắc tư duy kiến trúc hệ thống hiện đại."
        ),
        real_analogy=(
            "Hãy hình dung **Docker** giống như một **container vận tải tiêu chuẩn quốc tế**: dù đặt lên tàu thủy ở Việt Nam hay xe tải ở Mỹ thì toàn bộ hàng hóa bên trong "
            "(Python 3.12, PyTorch 2.6, FFmpeg, trọng số `v0.9.4`) vẫn vận hành đồng nhất không sai một phiên bản thư viện nào. Còn cơ chế **Zero-Persistence trên RAM** "
            "giống như chiếc máy soi hành lý tại sân bay: chiếu tia quét trực tiếp trên băng chuyền xong là màn hình xóa trắng, không in giữ lại ảnh chụp đồ đạc riêng tư của hành khách."
        ),
        core_points=[
            "**Mô hình kiến trúc C4 (Context → Containers → Components → Code)**: Bản vẽ phân rã kiến trúc theo 4 cấp độ thu phóng; ở Mức 2 (`Container Diagram`), đồ án chia rạch ròi dịch vụ Web/API, tiến trình Bot Telegram, lõi suy luận AI và kho trọng số chỉ đọc.",
            "**Đóng gói đa dịch vụ `Docker Compose`**: Khởi chạy đồng bộ cụm 2 container độc lập (`vitruevoice-api` và `vitruevoice-bot`) giao tiếp nội bộ qua mạng bridge cô lập chỉ bằng một lệnh `docker compose up -d`.",
            "**API phi trạng thái (`Stateless REST API`)**: Máy chủ FastAPI không lưu phiên đăng nhập hay lịch sử âm thanh của người dùng giữa các lượt gọi, giúp mở rộng tải ngang dễ dàng.",
            "**Đường ống nhị phân trên RAM (`io.BytesIO` + `FFmpeg Pipe`)**: Tệp âm thanh người dùng gửi tới được giữ nguyên dưới dạng luồng byte trong RAM, giải mã thẳng sang tensor float32 rồi giải phóng bộ nhớ ngay khi trả kết quả.",
            "**Hàm băm mật mã một chiều (`SHA-256`)**: Biến đổi dữ liệu nhị phân bất kỳ thành chuỗi 64 ký tự lục giác duy nhất để ghi log đối soát mà không ai có thể dịch ngược lại thành giọng nói gốc.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Hệ thống `ViTrueVoice v0.9.4` được tổ chức theo mô hình **C4 Mức 2 (`Container Diagram`)** gồm 4 thành phần phối hợp đồng bộ:",
    )
    add_bullet_item(
        doc,
        "Máy chủ web hiệu năng cao cung cấp các endpoint công nghiệp (`/api/v1/predict`, `/health`, `/metrics`, `/playground`), đồng thời tích hợp "
        "cơ chế **`Pre-warming`** nạp sẵn `out/v0.9.4/best_model.pt` (`sha256: 30a383256458740e...`) qua hàm thống nhất `resolve_default_checkpoint()`, "
        "giới hạn tốc độ (`Rate Limiting`), kiểm tra kích thước tải lên (`≤ 15 MB`) và xác thực chữ ký nhị phân `Magic Bytes`.",
        "1. Container `vitruevoice-api` (FastAPI Core Engine — Port `8000`)",
    )
    add_bullet_item(
        doc,
        "Xây dựng theo hệ thiết kế phòng Lab Pháp y số **Dual-Theme 1-Click (Dark Mode / Light Mode)** đạt độ tương phản chuẩn **`WCAG AAA`**, tích hợp 2 chế độ tương tác:\n"
        "• **Chế độ 1 (`Playground & Verification`)**: Thẩm định tức thì tệp ghi âm tải lên hoặc thu trực tiếp từ micro trình duyệt WebRTC (`noiseSuppression=false`, `top_db=25`), "
        "trực quan hóa phổ sóng âm, điểm `Logit`, xác suất hiệu chuẩn `Platt Scaling` và cảnh báo vùng biên.\n"
        "• **Chế độ 2 (`Live VoiceStudio CFM Cloning & Forensics Audit`)**: Cho phép người dùng chọn giọng mẫu tham chiếu hoặc thu âm trực tiếp, "
        "sinh ngay giọng giả Zero-Shot bằng động cơ `OmniVoice CFM` rồi đẩy luồng âm thanh clone qua lõi `SSL-AASIST v0.9.4` (`apply_dither=False`) để kiểm chứng trực quan ngay tại chỗ.",
        "2. Giao Diện Pháp Y Web Forensics UI (Gradio / Web Playground)",
    )
    add_bullet_item(
        doc,
        "Tiến trình chạy ngầm (`asyncio` daemon) kết nối Telegram Bot API. Người dân chỉ cần chuyển tiếp tin nhắn thoại `.ogg/.opus` hoặc tệp âm thanh từ "
        "Zalo/Telegram cho Bot; Bot gửi luồng byte qua mạng nội bộ Docker bridge (`http://vitruevoice-api:8000`) và phản hồi kết quả cảnh báo lừa đảo trong ~`0,7–1,1 giây`.",
        "3. Container `vitruevoice-bot` (Telegram Voice Verification Daemon)",
    )
    add_bullet_item(
        doc,
        "Thực hiện chuỗi bước: kiểm tra `Magic Bytes` → giải mã `FFmpeg Pipe` trên `RAM` → cắt tối đa 5 cửa sổ trượt `64.000` mẫu → "
        "chạy mô hình `SSL-AASIST v0.9.4` (`head_blend_a0.75`) → gộp điểm `Consensus Asymmetric Veto` → hiệu chuẩn `Platt Scaling (T = 16,0)` → ghi nhật ký ẩn danh `SHA-256`.",
        "4. Lõi Suy Luận Sinh Trắc Học (`src/models/` + `src/preprocessing/`)",
    )

    c4_path = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\C4.png")
    if c4_path.exists():
        add_figure(
            doc,
            c4_path,
            "Hình 9.1: Sơ đồ Kiến trúc Hệ thống ViTrueVoice (C4 Model Level 2 Container Diagram) — Minh họa tương tác giữa Người dùng Web/Telegram, "
            "Container vitruevoice-api, Container vitruevoice-bot và luồng kiểm định an ninh In-Memory.",
            width_inches=6.2,
        )

    if figs and "fig9" in figs:
        add_figure(
            doc,
            figs["fig9"],
            "Hình 9.2: Kiến trúc triển khai Docker Compose cục bộ chi phí 0 VNĐ áp dụng chuẩn bảo mật AWS Gói A và luồng xử lý Zero-Persistence 100% trên RAM.",
        )

    # -------------------------------------------------------------------------
    # 9.2 Vận hành 0 VNĐ & Áp dụng 3 chứng chỉ AWS Academy Gói A
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "9.2 Vận Hành Docker Cục Bộ Chi Phí 0 VNĐ & Cách Áp Dụng Thực Chất 3 Chứng Chỉ AWS Academy Gói A",
    )

    add_styled_paragraph(
        doc,
        "Đề tài đặt ra hai yêu cầu thực tế song hành: **(1) Toàn bộ hệ thống trong giai đoạn đồ án sinh viên phải vận hành với chi phí bằng `0 VNĐ` "
        "(tuyệt đối không phát sinh hóa đơn thuê máy chủ trả phí)**; và **(2) Bắt buộc vận dụng bài bản kiến thức từ bộ 3 chứng chỉ `AWS Academy Gói A`** "
        "(*Cloud Foundations*, *Cloud Security Foundations*, *Cloud Architecting*) vào thiết kế hệ thống. Nhóm giải quyết hài hòa cả hai yêu cầu bằng mô hình "
        "**`0 VNĐ Local Cloud-Native Execution + Static Cloud-Ready IaC`** (Bảng 9.1):",
    )

    add_styled_table(
        doc,
        headers=[
            "Chứng Chỉ AWS Academy Gói A (3 Khóa)",
            "Nguyên Lý Kiến Trúc / Bảo Mật Cốt Lõi",
            "Áp Dụng Thực Tế Tại Cụm Docker Cục Bộ (Chi Phí 0 VNĐ)",
            "Tệp Thiết Kế Sẵn Sàng Đám Mây (`Cloud-Ready Templates`)",
        ],
        rows=[
            (
                "1. **AWS Academy Cloud Foundations**\n*(Nền tảng Đám mây & Kinh tế học TCO)*",
                "Đóng gói dịch vụ phi trạng thái, tách biệt cấu hình môi trường, dự toán Tổng chi phí sở hữu (`TCO`) theo nhu cầu tải.",
                "Đóng gói toàn bộ cụm API + Bot qua `Dockerfile` & `docker-compose.yml` chạy ngay trên máy trạm/laptop địa phương với hóa đơn **0 VNĐ**.",
                "`deploy/aws/pricing_calculator_w08.md`: Mô phỏng 3 kịch bản chi phí AWS (`ap-southeast-1`), tính TCO quy mô `1.000 users/ngày` (~`125,94 USD/tháng`, tức ~`20–73 VNĐ/lượt quét` tùy cấu hình Spot).",
            ),
            (
                "2. **AWS Academy Cloud Security Foundations**\n*(Đặc quyền Tối thiểu IAM & Bảo vệ Dữ liệu)*",
                "Nguyên tắc đặc quyền tối thiểu (`Least Privilege`), tách bí mật khỏi mã nguồn, vòng đời tự hủy dữ liệu tạm và không chạy quyền `root`.",
                "Chạy container dưới tài khoản giới hạn quyền **`appuser` (non-root)**; gắn thư mục trọng số `:ro` (**Read-Only**); tách `BOT_TOKEN` / `API_KEY` qua `.env`; kiểm tra `Magic Bytes`; băm `SHA-256`.",
                "`deploy/aws/iam_policy.json` (khóa quyền tối thiểu theo từng ARN S3/ECR/CloudWatch) & `deploy/aws/s3_lifecycle_policy.json` (tự động xóa tuyệt đối mọi tệp tạm sau 1 ngày).",
            ),
            (
                "3. **AWS Academy Cloud Architecting**\n*(Cô lập Mạng VPC, Healthcheck & Tự phục hồi)*",
                "Phân tầng mạng riêng tư (`Private Subnet`), tự động kiểm tra sức khỏe (`Healthcheck`), tự khởi động lại khi gặp sự cố và hạ tầng dưới dạng mã (`IaC`).",
                "Cô lập giao tiếp giữa `vitruevoice-bot` và `vitruevoice-api` trong **mạng Docker Bridge nội bộ**; gắn `HEALTHCHECK /health` chu kỳ 30s và cơ chế `restart: unless-stopped`.",
                "`scripts/aws_deploy_ec2.sh`: Kịch bản tự động hóa (`IaC` Bash 6 bước) sẵn sàng triển khai lên máy chủ GPU `EC2 g4dn.xlarge` (`NVIDIA T4`) kèm NVIDIA Container Toolkit khi cần mở rộng.",
            ),
        ],
        col_widths=[1.50, 1.55, 1.85, 1.80],
        highlight_row_pred=lambda idx, _: True,
    )

    tco_eq = (
        omml_sub(omml_r("Cost"), omml_r("scan", normal=True))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_sub(omml_r("TCO"), omml_r("EC2+S3+ECR+CW", normal=True)),
            omml_sub(omml_r("N"), omml_r("req/tháng", normal=True)),
        )
    )
    add_omml_equation(
        doc,
        "Công thức dự toán chi phí đơn vị trên mỗi lượt thẩm định khi mở rộng lên AWS Cloud (Tham chiếu Tài chính — Cloud Foundations)",
        tco_eq,
        variables=[
            ("TCO_EC2+S3+ECR+CW", "Tổng chi phí hàng tháng dự kiến trên vùng `ap-southeast-1` Singapore (ở quy mô `0 VNĐ` cục bộ hiện tại, đại lượng này bằng đúng `0`)."),
            ("N_req/tháng", "Tổng sản lượng yêu cầu thẩm định (ví dụ `150.000 lượt/tháng` tương đương `5.000 lượt/ngày` tại `deploy/aws/pricing_calculator_w08.md`)."),
            ("Cost_scan", "Chi phí lý thuyết trên mỗi lượt kiểm tra (~`20–73 VNĐ/lượt` khi thuê GPU `g4dn.xlarge Spot`, tiết kiệm `68%` so với On-Demand)."),
        ],
    )

    # -------------------------------------------------------------------------
    # 9.3 Đạo đức sinh trắc học & Luật 91/2025/QH15
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "9.3 Tuân Thủ Đạo Đức Sinh Trắc Học, Luật Bảo Vệ Dữ Liệu Cá Nhân 91/2025/QH15 & An Ninh STRIDE",
    )

    add_styled_paragraph(
        doc,
        "Theo **Luật Bảo vệ Dữ liệu Cá nhân số `91/2025/QH15`** và **Nghị định `356/2025/NĐ-CP`**, dữ liệu giọng nói tự nhiên của công dân thuộc nhóm "
        "**Dữ liệu cá nhân nhạy cảm (Sinh trắc học)**. Nếu một hệ thống chống lừa đảo lại tự ý lưu trữ bản ghi âm người dùng trên máy chủ, chính máy chủ đó "
        "sẽ trở thành kho nguyên liệu cho tin tặc đánh cắp làm giọng giả! ViTrueVoice khóa cứng 4 hàng rào an ninh tuân thủ:",
    )
    add_bullet_item(
        doc,
        "Mọi gói tin âm thanh gửi qua REST API hay Telegram Bot được nạp trực tiếp vào bộ đệm `io.BytesIO` trên RAM và giải mã thông qua đường ống `FFmpeg Pipe`. "
        "Mọi đối tượng nhị phân tạm thời bị giải phóng ngay lập tức trong khối `finally` ngay sau ~`0,7–1,1 giây` trả kết quả.",
        "1. Nguyên tắc Zero-Persistence (0 byte giọng nói lưu trên đĩa)",
    )
    add_bullet_item(
        doc,
        "Tệp nhật ký theo dõi hiệu năng (`benchmarks/latency_log.json`) chỉ được phép ghi cặp giá trị `[mã băm SHA-256 64 ký tự, dấu thời gian UTC, độ trễ mili-giây, phiên bản mô hình]`. "
        "Tuyệt đối không lưu tên tệp gốc, ID người dùng Telegram hay số điện thoại.",
        "2. Ẩn danh hóa nhật ký bằng hàm băm một chiều SHA-256",
    )
    add_bullet_item(
        doc,
        "Hàm `load_audio` đọc trực tiếp những byte chữ ký đầu tệp (`RIFF/WAVE`, `OggS`, `ftyp`, `ID3`, `#!AMR`) thay vì tin vào đuôi tệp `.wav`/`.m4a`, "
        "đồng thời áp dụng giới hạn tốc độ (`20 req/phút/IP`), chặn tệp `> 15 MB` và xác thực payload webhook bằng `HMAC-SHA256`.",
        "3. Phòng vệ tấn công giả mạo tệp tin (Magic Bytes + STRIDE Hardening)",
    )
    add_bullet_item(
        doc,
        "Cả 6 tình nguyện viên thu âm tham gia đồ án đều đã ký văn bản đồng ý tự nguyện cung cấp mẫu giọng cho mục đích nghiên cứu học thuật phi thương mại, "
        "tách bạch quyền sử dụng và cam kết xóa hủy dữ liệu cá nhân theo đúng thời hạn đồ án.",
        "4. Minh bạch văn bản đồng thuận sinh trắc học (`Informed Consent`)",
    )

    add_callout_box(
        doc,
        "Khi Hội đồng hỏi: **\"Đề tài yêu cầu áp dụng kiến thức gói A AWS nhưng hệ thống lại chạy miễn phí 0 VNĐ trên máy cục bộ, vậy nhóm đã áp dụng cụ thể ở đâu?\"**, "
        "hãy trả lời tự tin 2 vế rõ ràng: *\"Dạ thưa Thầy/Cô, để bảo đảm chi phí vận hành thực tế đúng `0 VNĐ` cho đồ án sinh viên, cụm `vitruevoice-api` và `vitruevoice-bot` "
        "chạy hoàn toàn cục bộ trên Docker Compose; tuy nhiên chúng em đã áp dụng trọn vẹn cả 3 khóa AWS Academy Gói A vào chính cấu trúc Docker này và bộ khuôn mẫu `Cloud-Ready` đi kèm: "
        "(1) **Cloud Foundations**: đóng gói phi trạng thái và tính bảng TCO tại `deploy/aws/pricing_calculator_w08.md`; "
        "(2) **Cloud Security Foundations**: container `appuser` non-root, volume trọng số chỉ đọc `:ro`, tách bí mật `.env`, `iam_policy.json` đặc quyền tối thiểu và `s3_lifecycle_policy.json` tự hủy sau 24 giờ; "
        "(3) **Cloud Architecting**: cô lập mạng nội bộ Docker Bridge mô phỏng VPC Private Subnet, `HEALTHCHECK /health` tự phục hồi và kịch bản IaC `scripts/aws_deploy_ec2.sh` sẵn sàng nâng cấp lên `EC2 g4dn.xlarge` chỉ bằng một lệnh.\"*",
        title="BÍ QUYẾT PHẢN BIỆN CHƯƠNG 9: ÁP DỤNG THỰC CHẤT 3 KHÓA AWS GÓI A Ở MỨC CHI PHÍ 0 VNĐ",
    )

    add_term_glossary(
        doc,
        [
            ("C4 Model (Level 2)", "Context, Containers, Components, Code", "Phương pháp vẽ kiến trúc phần mềm chuẩn mực; Mức 2 (`Container`) mô tả các khối dịch vụ độc lập như API, Bot và lõi mô hình."),
            ("Docker Compose", "Multi-Container Orchestration Tool", "Công cụ định nghĩa và khởi chạy đồng bộ nhiều container phần mềm (API + Bot + mạng nội bộ) chỉ bằng một lệnh duy nhất."),
            ("Stateless API", "Representational State Transfer without Session Memory", "Giao diện lập trình không lưu trạng thái người dùng giữa các lượt gọi, giúp tăng bảo mật và dễ nhân bản mở rộng."),
            ("Magic Bytes", "File Signature Header Bytes", "Các byte nhận dạng đặc thù nằm ở đầu tệp tin nhị phân giúp xác định đúng định dạng âm thanh thực sự mà không bị đánh lừa bởi phần mở rộng tên tệp."),
            ("IAM Least Privilege", "Identity & Access Management — Nguyên tắc đặc quyền tối thiểu", "Kỷ luật bảo mật chỉ cấp vừa đủ quyền tối thiểu cho một tiến trình/container hoạt động (như `appuser` non-root và gắn trọng số `:ro`)."),
            ("IaC", "Infrastructure as Code", "Quản lý và cấp phát hạ tầng máy chủ, chính sách lưu trữ, phân quyền bằng tệp mã nguồn khai báo (`JSON`, `YAML`, `Shell`) thay vì bấm tay."),
            ("TCO", "Total Cost of Ownership", "Tổng chi phí sở hữu và vận hành toàn bộ hệ thống (tính toán, lưu trữ, băng thông mạng, giám sát) trong một đơn vị thời gian."),
            ("WCAG AAA", "Web Content Accessibility Guidelines Level AAA", "Tiêu chuẩn quốc tế mức cao nhất về độ tương phản màu sắc và khả năng tiếp cận giao diện web cho mọi đối tượng người dùng."),
        ],
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
