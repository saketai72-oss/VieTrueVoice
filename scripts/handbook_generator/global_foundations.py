"""
Phần Đặc Biệt: Bản Đồ Kiến Thức Nền Tảng Toàn Cục & Khung Xương Sống Hệ Thống VieTrueVoice v0.9.4.
Tài liệu học tập nền tảng và cẩm nang bảo vệ đồ án chuyên ngành dành cho sinh viên.
"""

from __future__ import annotations

from .styles import (
    add_bullet_item,
    add_callout_box,
    add_foundation_primer,
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
    omml_sup,
)


def add_global_foundations(doc) -> None:
    """Render the Global Foundations & Architectural Backbone section for VieTrueVoice v0.9.4."""
    add_heading_part(
        doc,
        "PHẦN ĐẶC BIỆT: BẢN ĐỒ KIẾN THỨC NỀN TẢNG TOÀN CỤC & KHUNG XƯƠNG SỐNG HỆ THỐNG VieTrueVoice v0.9.4",
    )

    add_styled_paragraph(
        doc,
        "Trước khi đi sâu vào chi tiết toán học và mã nguồn của từng chương, phần mở đầu này đóng vai trò là "
        "**bản đồ định hướng toàn cục** cho toàn bộ hệ thống **VieTrueVoice v0.9.4**. Mục tiêu của phần này là giúp "
        "sinh viên nắm vững từ gốc rễ bản chất bài toán, không bao giờ nhầm lẫn khái niệm khi Hội đồng đặt câu hỏi "
        "xoáy, đồng thời nhìn thấy bức tranh tổng thể kết nối xuyên suốt từ sóng âm vật lý đến quyết định pháp y số.",
        font_size=10.5,
        italic=True,
        color_rgb=(50, 55, 65),
        space_after=8,
    )

    # =========================================================================
    # G.0 CẨM NANG ĐỌC HIỂU SỔ TAY DÀNH CHO SINH VIÊN
    # =========================================================================
    add_heading_section(doc, "G.0 Cẩm Nang Sử Dụng Sổ Tay Hiệu Quả Để Học Sâu & Tự Tin Phản Biện")

    add_styled_paragraph(
        doc,
        "Cuốn sổ tay này được thiết kế theo phương pháp sư phạm **Từ trực giác đời thực → Kiến thức nền tảng → "
        "Toán học chính xác → Cơ chế thực thi trong `VieTrueVoice v0.9.4`**. Để việc ôn tập đạt hiệu quả cao nhất, "
        "sinh viên hãy tận dụng 5 thành phần trực quan được bố trí nhất quán trong mọi chương:",
    )

    add_bullet_item(
        doc,
        "Luôn xuất hiện **ngay trước khi bước vào một quy trình kỹ thuật phức tạp**. Hộp này giải thích bằng ngôn ngữ "
        "đời thường *vì sao phải có bước xử lý đó*, kèm theo *ví dụ ẩn dụ thực tế dễ hình dung* và danh sách các khái "
        "niệm vật lý/toán học cốt lõi cần nạp trước khi đọc chi tiết.",
        "1. Hộp Kiến Thức Nền Tảng Tiên Quyết (Biểu tượng 🧭)",
    )
    add_bullet_item(
        doc,
        "Mọi biểu thức toán học đều được dựng bằng **công thức chuẩn Microsoft Word OMML** sắc nét, đi kèm mục "
        "*Giải thích ký hiệu trong công thức* cho từng biến số và ví dụ thay số cụ thể để sinh viên hiểu bản chất "
        "thay vì học thuộc lòng máy móc.",
        "2. Thẻ Công Thức Toán Học & Giải Nghĩa Biến Số (Biểu tượng 📐)",
    )
    add_bullet_item(
        doc,
        "Đặt **ngay bên dưới mỗi mục** có xuất hiện từ viết tắt tiếng Anh hoặc thuật ngữ chuyên ngành âm học/học sâu, "
        "theo cấu trúc 3 lớp: *(Từ viết tắt — Tên tiếng Anh đầy đủ — Giải nghĩa tiếng Việt bình dân & vai trò trực tiếp "
        "trong dự án)*.",
        "3. Hộp Giải Nghĩa Từ Viết Tắt & Thuật Ngữ Tức Thời (Biểu tượng 📖)",
    )
    add_bullet_item(
        doc,
        "Các biểu đồ phân phối xác suất, sơ đồ luồng dữ liệu đối xứng, dải thông tần số 5 kênh nén và kiến trúc mạng "
        "được minh họa trực quan ở độ phân giải in ấn 300 DPI kèm chú thích phân tích từng khung hình.",
        "4. Hệ Thống Sơ Đồ Minh Họa Trực Quan (Visual Diagrams)",
    )
    add_bullet_item(
        doc,
        "Tổng hợp các câu hỏi phản biện sắc bén nhất mà giảng viên chấm đồ án thường hỏi tại buổi bảo vệ, kèm theo "
        "luận điểm trả lời ngắn gọn, trúng đích và dẫn chứng bằng con số thực nghiệm chính thức của phiên bản `v0.9.4`.",
        "5. Hộp Ghi Nhớ Quan Trọng & Bí Quyết Bảo Vệ (Biểu tượng ★)",
    )

    # =========================================================================
    # G.1 PHÂN ĐỊNH 3 BÀI TOÁN AI XỬ LÝ TIẾNG NÓI
    # =========================================================================
    add_heading_section(
        doc,
        "G.1 Phân Định Dứt Khoát 3 Bài Toán AI Tiếng Nói: ASR, ASV và Speech Anti-Spoofing (CM)",
    )

    add_foundation_primer(
        doc,
        process_name="Phân biệt 3 bài toán Trí tuệ nhân tạo xử lý giọng nói (ASR vs. ASV vs. Anti-Spoofing)",
        why_needed=(
            "Trong buổi bảo vệ đồ án, Hội đồng rất hay đặt câu hỏi kiểm tra bản chất như: 'Hệ thống của em có biết "
            "được giọng nói này có đúng là của mẹ nạn nhân hay không?' hoặc 'Nếu kẻ lừa đảo đọc một câu thoại mới tinh "
            "thì mô hình có bắt được không?'. Nếu không phân biệt rạch ròi 3 bài toán này, sinh viên rất dễ trả lời lẫn lộn."
        ),
        real_analogy=(
            "Hãy hình dung nhân viên ngân hàng kiểm tra một tờ séc rút tiền mặt tại quầy giao dịch: "
            "(1) Đọc dòng chữ ghi số tiền và nội dung chuyển khoản trên tờ séc chính là bài toán ASR (nói nội dung gì?); "
            "(2) So sánh chữ ký của khách hàng với chữ ký mẫu đã đăng ký lúc mở tài khoản chính là bài toán ASV (của ai?); "
            "(3) Đưa tờ giấy vào máy soi tia cực tím để xem phôi giấy, sợi bảo an và mực in là giấy thật của Ngân hàng Nhà nước "
            "hay giấy in giả bằng máy in phun màu chính là bài toán Speech Anti-Spoofing / CM của VieTrueVoice (thật hay giả, "
            "hoàn toàn không phụ thuộc trên giấy viết câu gì hay chữ ký của ai!)."
        ),
        core_points=[
            (
                "Mỗi tín hiệu giọng nói mang đồng thời 3 lớp thông tin độc lập: Nội dung ngôn ngữ (Linguistic content), "
                "Bản sắc cá nhân người nói (Speaker identity) và Dấu vết vật lý của nguồn phát âm (Production fidelity)."
            ),
            (
                "Các công cụ nhân bản giọng nói thế hệ mới (Zero-Shot Voice Cloning) được huấn luyện chuyên biệt để bắt chước "
                "giống hệt bản sắc cá nhân người nói, khiến hệ thống xác thực danh tính truyền thống (ASV) bị đánh lừa dễ dàng."
            ),
            (
                "Hệ thống phát hiện giả mạo độc lập (Stand-alone Countermeasure — CM) đi tìm sự khác biệt vi mô giữa cơ chế "
                "rung dây thanh đới sinh học của con người và thuật toán tái tạo sóng âm của máy tính."
            ),
        ],
    )

    add_styled_paragraph(
        doc,
        "Trong lĩnh vực Xử lý tiếng nói (*Speech Processing*), ba bài toán dưới đây có mục tiêu toán học, đầu vào "
        "và miền đặc trưng khai thác hoàn toàn khác nhau:",
    )

    add_bullet_item(
        doc,
        "Trả lời câu hỏi **'Người nói đang nói nội dung gì?'** (*Speech-to-Text*). Đầu vào là sóng âm thanh, đầu ra là "
        "chuỗi từ ngữ văn bản. Mô hình ASR được thiết kế để **triệt tiêu sự khác biệt giọng vùng miền, nam/nữ và thật/giả** "
        "nhằm chép lời chính xác nhất. Trong dự án `VieTrueVoice v0.9.4`, ASR không dùng để bắt giả mạo trực tiếp mà đóng "
        "vai trò trợ lý kiểm định chất lượng mẫu sinh tại Cổng lọc số 1 và chép lời tham chiếu cho chế độ Live Cloning.",
        "1. Bài toán ASR (Automatic Speech Recognition — Nhận dạng tiếng nói thành văn bản)",
    )
    add_bullet_item(
        doc,
        "Trả lời câu hỏi **'Giọng nói này thuộc về ai?'** (*Who is speaking?*). Hệ thống bắt buộc phải có bước **Đăng ký "
        "trước (`Enrollment`)**: thu thập giọng thật của Anh A để trích xuất một vector đặc trưng vân giọng cố định "
        "(*Speaker Embedding*, ví dụ vector 192 chiều từ mạng `ECAPA-TDNN`). Khi có cuộc gọi đến, hệ thống đo khoảng cách "
        "góc Cosine xem giọng mới có khớp với vân giọng của Anh A hay không. **Điểm mù chí mạng**: Khi kẻ lừa đảo dùng "
        "AI nhân bản Zero-Shot chỉ từ 5 giây video TikTok của Anh A, giọng giả sinh ra đạt độ tương đồng vân giọng rất cao "
        "(Cosine Similarity ≥ 0,70–0,85), khiến hệ thống ASV truyền thống xác nhận nhầm kẻ lừa đảo chính là Anh A!",
        "2. Bài toán ASV (Automatic Speaker Verification — Xác thực danh tính người nói)",
    )
    add_bullet_item(
        doc,
        "Trả lời câu hỏi **'Âm thanh này phát ra từ bộ máy phát âm sinh học của con người hay do thuật toán AI tổng hợp?'** "
        "(*Biological Human Speech vs. Synthetic/Converted Artifact*). Đây là **trọng tâm 100% của đề tài `VieTrueVoice v0.9.4`**. "
        "Hệ thống hoạt động hoàn toàn **độc lập với danh tính người nói (*Speaker-Independent*)** và **độc lập với nội dung "
        "câu chữ (*Text-Independent*)**: không cần thu thập trước kho vân giọng của người dân, bất kỳ tin nhắn thoại Zalo hay "
        "ghi âm cuộc gọi nào gửi vào đều được thẩm định tức thì dựa trên vi cấu trúc phổ - pha và động học phát âm.",
        "3. Bài toán Speech Anti-Spoofing / CM (Countermeasure — Phát hiện giọng nói giả mạo)",
    )

    add_styled_table(
        doc,
        headers=[
            "Tiêu Chí Đối Chiếu",
            "ASR (Speech-to-Text)",
            "ASV (Speaker Verification)",
            "Speech Anti-Spoofing / CM (VieTrueVoice v0.9.4)",
        ],
        rows=[
            (
                "Câu hỏi cốt lõi",
                "Đang nói nội dung chữ gì?",
                "Đây có phải là giọng của người X đã đăng ký không?",
                "Giọng con người sinh học phát âm hay do máy tính/AI tạo ra?",
            ),
            (
                "Điều kiện tiên quyết",
                "Không cần mẫu giọng trước của người nói.",
                "Bắt buộc có mẫu giọng đăng ký trước (Enrollment) của từng cá nhân.",
                "Không cần mẫu đăng ký trước; thẩm định trực tiếp mọi giọng người lạ.",
            ),
            (
                "Đầu ra toán học",
                "Chuỗi ký tự / từ vựng tiếng Việt.",
                "Độ tương đồng vân giọng Cosine ∈ [-1, 1].",
                "Điểm biên Logit s(x) = z₁ − z₀, nhãn Thật/Giả & xác suất tin cậy [%].",
            ),
            (
                "Đặc trưng âm học giữ lại",
                "Hình bao phổ nguyên âm/phụ âm mang nghĩa từ vựng.",
                "Kích thước thanh quản, âm sắc cá nhân bất biến theo câu nói.",
                "Vi nhiễu pha vocoder, tính liên tục luồng CFM, dao động vi mô dây thanh đới.",
            ),
            (
                "Trước tấn công Zero-Shot Voice Cloning",
                "Vẫn chép lời bình thường cả giọng thật lẫn giọng giả.",
                "Bị đánh lừa nghiêm trọng vì giọng giả mang đúng vân giọng nạn nhân.",
                "Phát hiện và chặn đứng giả mạo (chặn 95,01% trên 15.980 mẫu kiểm thử).",
            ),
            (
                "Vai trò trong dự án VieTrueVoice v0.9.4",
                "Cổng lọc chất lượng WER/CER (Gate 1) & hỗ trợ ASR cho Live Demo.",
                "Cổng lọc độ giống vân giọng ECAPA-TDNN (Gate 2) khi tạo tập dữ liệu.",
                "Mô hình phòng thủ trung tâm SSL-AASIST vận hành trên API, Web & Telegram Bot.",
            ),
        ],
        col_widths=[1.35, 1.65, 1.75, 1.95],
    )

    add_callout_box(
        doc,
        "Nếu giám khảo hỏi: **'Làm sao hệ thống biết đây không phải giọng thật của bố/mẹ người dùng khi hệ thống chưa từng "
        "nghe giọng bố/mẹ họ bao giờ?'**, hãy trả lời dứt khoát: *'Dạ thưa Thầy/Cô, VieTrueVoice giải quyết bài toán Speech "
        "Anti-Spoofing (Countermeasure) chứ không phải bài toán định danh ASV. Con người dù giọng trầm hay bổng đều tạo âm "
        "thanh qua luồng hơi phổi làm rung dây thanh đới hữu cơ với biến thiên vi mô tự nhiên; trong khi mọi động cơ AI như "
        "F5-TTS, OmniVoice CFM hay VieNeu-TTS đều phải tái tạo sóng âm qua mạng nơ-ron và bộ giải mã Vocoder, để lại các bất "
        "thường vi cấu trúc phổ - thời gian. Nhờ đó, mô hình phát hiện trực tiếp dấu vết tổng hợp nhân tạo mà không cần lưu "
        "trữ trước sinh trắc học cá nhân của người dân, vừa tiện lợi tức thì vừa an toàn quyền riêng tư.'*",
        title="BÍ QUYẾT PHẢN BIỆN CỐT LÕI: VÌ SAO VieTrueVoice KHÔNG CẦN ĐĂNG KÝ GIỌNG TRƯỚC?",
    )

    add_term_glossary(
        doc,
        [
            (
                "ASR",
                "Automatic Speech Recognition",
                "Công nghệ nhận dạng tiếng nói tự động chuyển đổi sóng âm thanh thành văn bản chữ viết.",
            ),
            (
                "ASV",
                "Automatic Speaker Verification",
                "Công nghệ xác thực danh tính người nói dựa trên việc so khớp vân giọng với mẫu đã đăng ký trước.",
            ),
            (
                "CM / Anti-Spoofing",
                "Countermeasure / Speech Anti-Spoofing",
                "Biện pháp đối phó chống giả mạo sinh trắc học, chuyên phân loại giọng người thật sinh học với giọng tổng hợp nhân tạo.",
            ),
            (
                "Enrollment",
                "Speaker Enrollment",
                "Quá trình thu thập mẫu giọng nói chuẩn ban đầu của một người để tạo hồ sơ vân giọng trong bài toán ASV.",
            ),
            (
                "Speaker Embedding",
                "Biểu diễn nhúng vân giọng",
                "Vector số thực chiều cố định (ví dụ 192 chiều từ mạng ECAPA-TDNN) nén đặc trưng âm sắc độc nhất của một cá nhân.",
            ),
            (
                "Bonafide",
                "Bona Fide Speech",
                "Thuật ngữ chuẩn quốc tế ISO/IEC chỉ giọng nói thật tự nhiên 100% phát ra trực tiếp từ con người sinh học.",
            ),
            (
                "Spoof",
                "Spoofed / Synthetic Speech",
                "Giọng nói giả mạo được sinh ra hoặc biến đổi bởi thuật toán máy tính nhằm đánh lừa con người hoặc hệ thống bảo mật.",
            ),
        ],
    )

    # =========================================================================
    # G.2 BỐN TRỤ CỘT KIẾN TRÚC CỦA VieTrueVoice v0.9.4
    # =========================================================================
    add_heading_section(doc, "G.2 Bốn Trụ Cột Kiến Trúc Cốt Lõi Của Hệ Thống VieTrueVoice v0.9.4")

    add_foundation_primer(
        doc,
        process_name="Kiến trúc 4 trụ cột khép kín của hệ thống phát hiện giọng giả VieTrueVoice v0.9.4",
        why_needed=(
            "Một mô hình học sâu đơn lẻ không thể tự mình sống sót trong môi trường chống lừa đảo thực tế. Sinh viên cần "
            "nắm được cách 4 tầng kỹ thuật (Mô hình biểu diễn → Dữ liệu đa kênh nén → Gộp điểm đa cửa sổ → Hiệu chuẩn xác "
            "suất & Bảo mật RAM) phối hợp chặt chẽ để biến tensor sóng âm thô thành kết luận pháp y đáng tin cậy."
        ),
        real_analogy=(
            "Giống như một trung tâm xét nghiệm y khoa chuẩn quốc tế gồm 4 khâu liên hoàn: "
            "(1) Kính hiển vi điện tử kết hợp chuyên gia đọc tiêu bản (Wav2Vec 2.0 + đồ thị AASIST); "
            "(2) Bộ mẫu huấn luyện thực chiến trong đủ mọi điều kiện vận chuyển khắc nghiệt (RawBoost + 5 Codecs + TTS đối xứng); "
            "(3) Quy trình lấy 5 lát cắt sinh thiết dọc mẫu bệnh phẩm để không bỏ sót ổ bệnh cũng không kết luận nhầm (Consensus Asymmetric Veto); "
            "(4) Máy quy chuẩn chỉ số xét nghiệm kèm quy trình hủy mẫu sinh học ngay sau khi đọc kết quả (head_blend_a0.75 + Platt T=16.0 + Zero-Persistence)."
        ),
        core_points=[
            "Khối Front-end đóng vai trò 'đôi tai cảm thụ ngôn ngữ' trích xuất đặc trưng âm học giàu ngữ cảnh; khối Back-end đóng vai trò 'bộ não suy luận đồ thị' tìm mối liên kết bất thường giữa thời gian và tần số.",
            "Huấn luyện đối xứng đa kênh nén và đa động cơ TTS giúp thu hẹp khoảng cách lệch miền (Domain Shift) giữa phòng thí nghiệm và mạng Zalo/viễn thông thực tế.",
            "Cơ chế gộp điểm đa cửa sổ ở bước suy luận giải quyết bài toán câu thoại dài ngắn bất kỳ có chứa nhịp nghỉ thở hoặc khoảng lặng cuối câu.",
            "Tầng hiệu chuẩn hậu kỳ đảm bảo điểm số đầu ra phản ánh đúng mức độ tự tin xác suất thực nghiệm mà không làm thay đổi kiến trúc mạng cơ sở.",
        ],
    )

    add_styled_paragraph(
        doc,
        "Phiên bản phát hành chính thức **`VieTrueVoice v0.9.4`** được kiến tạo trên **4 trụ cột kỹ thuật xuyên suốt**, "
        "trong đó mỗi trụ cột giải quyết dứt điểm một điểm nghẽn thực tế của bài toán phát hiện Deepfake tiếng Việt:",
    )

    add_heading_subsection(
        doc,
        "Trụ cột 1: Khối Biểu Diễn Tự Giám Sát Tiếng Việt Wav2Vec 2.0 & Mạng Đồ Thị Không Đồng Nhất Compact AASIST",
    )
    add_styled_paragraph(
        doc,
        "Thay vì sử dụng các đặc trưng phổ thủ công cố định như `MFCC` hay `LFCC` dễ bị phá hủy khi nén âm thanh, "
        "hệ thống kết hợp khối Front-end **`Wav2Vec 2.0` tiếng Việt** (`nguyenvulebinh/wav2vec2-base-vietnamese-250h`, "
        "gồm 7 tầng tích chập CNN trích xuất đặc trưng sóng âm cục bộ và 12 tầng Transformer mã hóa ngữ cảnh thành chuỗi "
        "vector 768 chiều) với khối Back-end **`Compact AASIST`**. Do đã học tự giám sát trên 250 giờ tiếng Việt chuẩn, "
        "`Wav2Vec 2.0` nắm bắt tinh tế quy luật luyến láy của 6 thanh điệu và chuyển tiếp âm vị bản địa. Phía sau nó, "
        "tầng chú ý đồ thị không đồng nhất **`HS-GAL` (*Heterogeneous Spatio-Temporal Graph Attention Layer*)** mô hình "
        "hóa đồng thời các nút thời gian, các nút tần số và một nút tổng hợp trung tâm (*Master Node*) để vạch trần những "
        "điểm lệch pha hoặc làm trơn phổ nhân tạo của bộ tổng hợp giọng nói.",
    )

    add_heading_subsection(
        doc,
        "Trụ cột 2: Kỹ Nghệ Dữ Liệu Bền Vững Kênh Thoại (RawBoost + 5 Codecs) & Sinh Mẫu Kép Đối Xứng 1:1",
    )
    add_styled_paragraph(
        doc,
        "Để mô hình miễn dịch trước méo dạng đường truyền, dữ liệu huấn luyện kết hợp thuật toán tăng cường nhiễu trực "
        "tiếp trên sóng âm **`RawBoost`** (`LnL` nhiễu tích chập tuyến tính/phi tuyến + `ISD` nhiễu xung phụ thuộc tín hiệu) "
        "cùng **5 cấu hình kênh thoại thực tế**: `Clean 16kHz` (âm thanh chuẩn đối chứng), `Zalo AAC-LC 76kbps` (tệp `.m4a` "
        "48kHz mono), `Zalo Opus 24kbps` (tin nhắn thoại `.ogg`), `G.711 A-law` (64kbps @ 8kHz mạng điện thoại cố định) và "
        "`AMR-NB` (4,75–12,2kbps @ 8kHz mạng di động GSM). Về phía nguồn sinh giả mạo, phiên bản `v0.9.4` thiết lập thế "
        "đối xứng kép giữa hai động cơ **Seen TTS** thuộc họ Flow Matching hiện đại nhất: **`F5-TTS-Vietnamese`** (`6.170` "
        "tệp) và **`OmniVoice CFM`** (`6.445` tệp đối xứng 1:1 qua 5 codecs), đồng thời giữ cô lập hoàn toàn động cơ mã hóa "
        "rời rạc **`VieNeu-TTS v3 Turbo`** làm thước đo kiểm định khái quát hóa ngoài phân phối (Giả thuyết H2).",
    )

    add_heading_subsection(
        doc,
        "Trụ cột 3: Gộp Điểm Đa Cửa Sổ Phủ Quyết Đồng Thuận Bất Đối Xứng (Multi-Window Consensus Asymmetric Veto)",
    )
    add_styled_paragraph(
        doc,
        "Một đoạn ghi âm thực tế dài 5–10 giây không có chất lượng đồng đều ở mọi giây: người thật nói chuyện tự nhiên "
        "luôn có lúc dừng lấy hơi giữa câu, trong khi tệp giả mạo từ `OmniVoice CFM` đôi khi để lộ dấu vết nhân tạo cực rõ "
        "ở vùng chuyển tiếp hoặc khoảng lặng cuối câu. Hệ thống cắt đoạn thoại thành tối đa **5 cửa sổ trượt dày 4,0 giây** "
        "(`64.000` mẫu @ 16kHz, bước trượt `1,0 giây` = `16.000` mẫu, đảm bảo tối thiểu ≥ 2 cửa sổ lệch pha với các tệp biên "
        "≥ `50.000` mẫu) và suy luận song song trong **1 lượt truyền xuôi (forward pass) duy nhất**. Sau đó, cơ chế "
        "**`Consensus Asymmetric Veto`** kiểm tra chéo: nếu phát hiện cửa sổ mang dấu vết giả mạo sâu (`min < -12,0`), thuật "
        "toán xét tiếp sự đồng thuận của đa số cửa sổ còn lại (`sorted_s[-2] ≥ +6,0` khi có ≥ 3 cửa sổ) để vừa bắt trọn "
        "mẫu giả CFM rò rỉ, vừa bảo vệ an toàn tuyệt đối cho người thật khi dừng nghỉ lấy hơi.",
    )

    add_heading_subsection(
        doc,
        "Trụ cột 4: Hiệu Chuẩn Đầu Phân Loại head_blend_a0.75, Xác Suất Platt Scaling (T=16.0) & An Ninh Zero-Persistence",
    )
    add_styled_paragraph(
        doc,
        "Ở tầng ra quyết định cuối cùng, mô hình `v0.9.4` áp dụng kỹ thuật nội suy trọng số đầu phân loại Giai đoạn 3 "
        "**`head_blend_a0.75`**: giữ cố định 100% các tầng trích xuất biểu diễn `Wav2Vec 2.0`, chỉ pha trộn tuyến tính "
        "trọng số đầu phân loại giữa mô hình kết thúc Pha 2 (`0,25`) và mô hình vi chỉnh đầu phân loại trên tập cân bằng "
        "(`0,75`) nhằm mở rộng biên an toàn cho cả giọng thật âm vực trầm lẫn mẫu giả khó. Điểm thô `s(x)` sau đó đi qua "
        "bộ hiệu chuẩn nhiệt độ **`Platt Scaling` (`T = 16,0`)** và kẹp trong khoảng **`[0,1%, 99,9%]`** theo chuẩn pháp y "
        "số của NIST (không bao giờ hiển thị độ tin cậy ảo 100%). Toàn bộ luồng xử lý vận hành **100% trên RAM "
        "(Zero-Persistence)**, ẩn danh hóa nhật ký bằng mã băm **`SHA-256`** theo Luật 91/2025/QH15, triển khai qua "
        "Docker cục bộ với chi phí vận hành **`0 VNĐ`** và được bảo vệ bởi **`392/392 bài kiểm thử đơn vị (unit tests)`** "
        "xanh 100%.",
    )

    blend_eq = (
        omml_sub(omml_r("W"), omml_r("final", normal=True))
        + omml_r(" = ", normal=True)
        + omml_r("0,25", normal=True)
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("W"), omml_r("Phase2", normal=True))
        + omml_r(" + ", normal=True)
        + omml_r("0,75", normal=True)
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("W"), omml_r("HeadOnly", normal=True))
    )
    add_omml_equation(
        doc,
        "Nội suy trọng số đầu phân loại Giai đoạn 3 (head_blend_a0.75 trong v0.9.4)",
        blend_eq,
        variables=[
            ("W_final", "Bộ trọng số đầu phân loại chính thức đóng băng trong tệp out/v0.9.4/best_model.pt."),
            ("W_Phase2", "Trọng số sau huấn luyện Pha 2 toàn mạng (mạnh về độ nhạy bắt giả mạo CFM và Unseen TTS)."),
            ("W_HeadOnly", "Trọng số sau 1 epoch hiệu chuẩn riêng khối đầu phân loại trên 5.100 mẫu cân bằng (khử lệch biên âm cho giọng người thật)."),
            ("0,25 và 0,75", "Hệ số pha trộn tối ưu α = 0,75 giữ nguyên 100% backbone Wav2Vec 2.0, dung hòa đồng thời APCER và BPCER."),
        ],
    )

    platt_inner = omml_frac(
        omml_r("1", normal=True),
        omml_r("1 + ", normal=True)
        + omml_sup(
            omml_r("e"),
            omml_delim(
                omml_r("−", normal=True) + omml_frac(omml_r("s"), omml_r("T")),
                beg="(",
                end=")",
            ),
        ),
    )
    platt_eq = (
        omml_sub(omml_r("P", normal=True), omml_r("bona", normal=True))
        + omml_delim(omml_r("s"))
        + omml_r(" = ", normal=True)
        + omml_r("clip", normal=True)
        + omml_delim(
            platt_inner + omml_r(" , 0,001 , 0,999", normal=True),
            beg="[",
            end="]",
        )
    )
    add_omml_equation(
        doc,
        "Hiệu chuẩn xác suất hậu nghiệm Platt Scaling có điều nhiệt (T = 16,0) & Kẹp biên NIST",
        platt_eq,
        variables=[
            ("P_bona(s)", "Xác suất thực nghiệm mẫu âm thanh là giọng người thật (nhân 100% để hiển thị trên giao diện; xác suất giả mạo = 1 − P_bona)."),
            ("s", "Điểm biên Logit thô sau khi gộp đa cửa sổ (s ≥ 0 nghiêng về giọng thật, s < 0 nghiêng về giọng giả)."),
            ("T = 16,0", "Nhiệt độ hiệu chuẩn (tương đương độ dốc hiệu dụng k_eff = 1/16 = 0,0625), ngăn chặn hiện tượng bão hòa giả 99,9% ở các điểm số trung bình."),
            ("[0,001 , 0,999]", "Giới hạn kẹp chuẩn pháp y NIST [0,1%, 99,9%], đảm bảo tính khiêm tốn xác suất trong giám định sinh trắc học."),
        ],
    )

    add_term_glossary(
        doc,
        [
            (
                "SSL",
                "Self-Supervised Learning",
                "Học biểu diễn tự giám sát: mô hình tự học quy luật cấu trúc tiếng nói từ hàng trăm giờ âm thanh không cần nhãn thủ công.",
            ),
            (
                "Wav2Vec 2.0",
                "Kiến trúc trích xuất tiếng nói tự giám sát",
                "Mô hình của Meta AI (bản tiếng Việt 250 giờ) biến sóng âm 16kHz thành chuỗi vector ngữ cảnh 768 chiều.",
            ),
            (
                "AASIST & HS-GAL",
                "Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention",
                "Mạng nơ-ron đồ thị chú ý tích hợp không gian - thời gian, dùng tầng HS-GAL bắt các bất thường chéo giữa trục thời gian và tần số.",
            ),
            (
                "Consensus Asymmetric Veto",
                "Phủ quyết bất đối xứng có kiểm tra đồng thuận",
                "Thuật toán gộp điểm 5 cửa sổ trượt trong v0.9.4: ưu tiên bắt cửa sổ giả mạo âm sâu nhưng bảo vệ giọng thật nếu đa số cửa sổ đồng thuận dương cao.",
            ),
            (
                "head_blend_a0.75",
                "Nội suy trọng số đầu phân loại tỷ lệ 0,75",
                "Kỹ thuật kết hợp tuyến tính 25% đầu phân loại Pha 2 và 75% đầu phân loại vi chỉnh cân bằng trong mô hình phát hành v0.9.4.",
            ),
            (
                "Platt Scaling",
                "Hiệu chuẩn xác suất hồi quy Logistic",
                "Phương pháp ánh xạ điểm số thô không giới hạn của mạng nơ-ron sang giá trị xác suất thực tế nằm trong khoảng (0, 1).",
            ),
            (
                "Zero-Persistence",
                "Kiến trúc không lưu dấu dữ liệu trên đĩa",
                "Nguyên tắc giải mã và suy luận âm thanh hoàn toàn trên bộ nhớ RAM, xóa hủy tức thì mọi vùng đệm sau khi trả kết quả.",
            ),
            (
                "TDD",
                "Test-Driven Development",
                "Phát triển hướng kiểm thử: viết kịch bản kiểm thử tự động trước khi viết mã thực thi (đạt 392/392 unit tests xanh 100%).",
            ),
        ],
    )

    # =========================================================================
    # G.3 TAM GIÁC ĐÁNH ĐỔI KỸ THUẬT CỐT LÕI (CORE ENGINEERING TRILEMMA)
    # =========================================================================
    add_heading_section(
        doc,
        "G.3 Tam Giác Đánh Đổi Kỹ Thuật Cốt Lõi (The Core Engineering Trilemma)",
    )

    add_styled_paragraph(
        doc,
        "Trong môi trường phòng thí nghiệm lý tưởng (tệp âm thanh sạch không nén, kiểm tra trên đúng công cụ TTS đã học, "
        "chạy offline không giới hạn thời gian), việc đạt sai số dưới 2% là điều dễ dàng. Tuy nhiên, khi triển khai một "
        "hệ thống phòng chống lừa đảo thực chiến cho người dùng Việt Nam, kỹ sư bắt buộc phải giải quyết đồng thời "
        "**Tam giác Đánh đổi Kỹ thuật (Engineering Trilemma)** gồm 3 đỉnh luôn kéo căng lẫn nhau:",
    )

    add_bullet_item(
        doc,
        "Kẻ lừa đảo phát tán giọng giả qua Zalo (`AAC-LC 76k`, `Opus 24k`) hoặc mạng viễn thông (`G.711`, `AMR-NB` băng "
        "hẹp `8kHz`) làm mất sạch dải tần cao. Nếu chỉ huấn luyện trên âm thanh sạch, mô hình sẽ mù tịt khi gặp tin nhắn "
        "thoại nén. Ngược lại, nếu làm trơn quá mức để chịu nén, mô hình lại mất độ nhạy bắt vi nhiễu. Trong `v0.9.4`, "
        "nhờ huấn luyện đối xứng 5 codecs kết hợp `RawBoost`, hệ thống đạt **`5,63%` EER** trên `15.980` mẫu kiểm thử nội "
        "bộ (vượt xa trần KPI `≤ 8,0%`).",
        "Đỉnh 1 — Độ bền vững trước biến dạng nén kênh thoại (Codec Distortion Robustness — H1)",
    )
    add_bullet_item(
        doc,
        "Công nghệ nhân bản giọng nói thay đổi từng tháng. Nếu ép mạng học quá sâu dấu vết riêng của `F5-TTS` và "
        "`OmniVoice CFM` (Overfitting), sai số nội bộ có thể giảm sát 1% nhưng khi gặp kiến trúc hoàn toàn lạ như "
        "`VieNeu-TTS v3 Turbo`, EER sẽ vọt lên trên 20%. Nhờ giữ đóng băng tri thức nền `Wav2Vec 2.0` ở Pha 1, mở khóa "
        "tốc độ học phân tầng cực nhỏ ở Pha 2 và hiệu chuẩn `head_blend_a0.75`, mô hình `v0.9.4` đạt **`12,05%` EER** "
        "trên `955` mẫu `VieNeu-TTS` OOD và **`6,90%` EER** trên `375` mẫu 5 tình nguyện viên (vượt chuẩn KPI `≤ 15,0%`).",
        "Đỉnh 2 — Khả năng khái quát hóa trước động cơ TTS chưa từng thấy (Unseen TTS Generalization — H2)",
    )
    add_bullet_item(
        doc,
        "Để tăng thêm 1–2% độ chính xác, nhiều bài báo học thuật ghép nối 5–10 mô hình khổng lồ (*Heavy Ensemble*), làm "
        "thời gian suy luận kéo dài 10–25 giây và tiêu tốn hàng chục GB VRAM — bất khả thi khi người dân cần kiểm tra "
        "nhanh cuộc gọi khẩn cấp trên máy chủ tiết kiệm chi phí. `VieTrueVoice v0.9.4` giải quyết bằng kiến trúc đơn mô "
        "hình tinh gọn chạy gom lô 5 cửa sổ song song, đạt trung vị độ trễ **`1,101 giây`** (benchmark 30 lượt chuẩn) và "
        "**`0,705 giây`** (trên 140 lượt log thực tế) — nhanh gấp ~3–4 lần ngưỡng mục tiêu `≤ 3,0 giây`.",
        "Đỉnh 3 — Tốc độ phản hồi thời gian thực trên phần cứng phổ thông (Real-Time Latency — NFR1 ≤ 3,0s)",
    )

    add_styled_table(
        doc,
        headers=[
            "Đỉnh Tam Giác Kỹ Thuật",
            "Hệ Lụy Nếu Tối Ưu Cực Đoan Một Chiều",
            "Giải Pháp Cân Bằng Trong VieTrueVoice v0.9.4",
            "Mục Tiêu KPI",
            "Kết Quả Đạt Được (v0.9.4)",
        ],
        rows=[
            (
                "1. Độ bền nén kênh thoại (H1 / In-domain)",
                "Quá khớp vào nhiễu nén làm tăng báo nhầm người thật qua micro sạch.",
                "Ghép cặp 5 Codecs đồng bộ qua base_utt + RawBoost (LnL + ISD) + head_blend_a0.75.",
                "In-domain EER ≤ 8,0% (giảm ≥ 30% EER nén)",
                "5,63% EER trên 15.980 mẫu (thắng đều cả 5/5 codecs: 4,88%–6,11%)",
            ),
            (
                "2. Khái quát hóa Unseen TTS (H2 / OOD)",
                "Học vẹt dấu vết vocoder đã biết, thất bại trước kiến trúc TTS thế hệ mới.",
                "Huấn luyện 2 pha phân tầng LR + Seen đối xứng (F5 + OmniVoice CFM) + Consensus Veto.",
                "Unseen Zero-Shot TTS EER ≤ 15,0%",
                "12,05% EER (955 mẫu VieNeu Dev) & 6,90% EER (375 mẫu 5-SPK)",
            ),
            (
                "3. Độ trễ thời gian thực (NFR1)",
                " Ghép nhiều mô hình nặng gây nghẽn RAM/GPU, người dùng bỏ cuộc vì chờ lâu.",
                "Giải mã FFmpeg pipe trên RAM + Pre-warming + Mini-batch 5 cửa sổ trong 1 forward pass.",
                "Trung vị độ trễ ≤ 3,0 giây / lượt",
                "Trung vị 1,101s (benchmark 30 ca) & 0,705s (140 lượt thực tế)",
            ),
        ],
        col_widths=[1.30, 1.45, 1.65, 1.10, 1.20],
        highlight_row_pred=lambda idx, _: True,
    )

    add_term_glossary(
        doc,
        [
            (
                "Engineering Trilemma",
                "Tam giác đánh đổi kỹ thuật",
                "Bài toán tối ưu hóa 3 mục tiêu xung khắc nhau (Độ bền nén — Khái quát hóa OOD — Độ trễ thấp), đòi hỏi thiết kế cân bằng thay vì hy sinh một đỉnh.",
            ),
            (
                "In-domain",
                "Trong phân phối huấn luyện",
                "Đánh giá trên người nói mới và câu nói mới, nhưng thuộc các họ công cụ TTS và kênh nén đã có mặt trong quy trình huấn luyện.",
            ),
            (
                "OOD",
                "Out-of-Distribution",
                "Ngoài phân phối huấn luyện: kiểm thử trên công cụ TTS có kiến trúc toán học hoàn toàn mới chưa từng xuất hiện lúc học.",
            ),
            (
                "Overfitting",
                "Hiện tượng quá khớp (học vẹt)",
                "Mô hình ghi nhớ máy móc nhiễu cục bộ của tập Train dẫn tới điểm Train rất cao nhưng thất bại khi gặp dữ liệu mới.",
            ),
            (
                "Median / P50 Latency",
                "Độ trễ trung vị (Phân vị thứ 50)",
                "Mốc thời gian mà ít nhất 50% số lượt truy vấn hoàn thành nhanh hơn mức đó; phản ánh tốc độ điển hình chính xác hơn trung bình cộng khi có nhiễu mạng.",
            ),
        ],
    )

    # =========================================================================
    # G.4 BẢNG TỪ ĐIỂN THAM CHIẾU NHANH TOÀN DỰ ÁN (MASTER LEXICON)
    # =========================================================================
    add_heading_section(
        doc,
        "G.4 Bảng Từ Điển Tham Chiếu Nhanh Toàn Dự Án (Master Quick-Reference Lexicon)",
    )

    add_styled_paragraph(
        doc,
        "Bảng tổng hợp dưới đây đóng vai trò như **tờ phao tra cứu nhanh (Cheat Sheet)** chứa các khái niệm, ký hiệu "
        "và thông số khóa cứng quan trọng nhất xuyên suốt từ Chương 1 đến Chương 13 của hệ thống `VieTrueVoice v0.9.4`:",
    )

    lexicon_rows = [
        (
            "Bonafide / Lớp 1",
            "Bona Fide Presentation",
            "Giọng người thật sinh học tự nhiên; gán nhãn số 1, mang kỳ vọng điểm biên Logit dương (s ≥ 0).",
        ),
        (
            "Spoof / Lớp 0",
            "Spoof Attack Presentation",
            "Giọng nhân tạo tổng hợp/nhân bản bằng AI; gán nhãn số 0, mang kỳ vọng điểm biên Logit âm (s < 0).",
        ),
        (
            "s(x) = z₁(x) − z₀(x)",
            "Raw Logit Margin Score",
            "Điểm số biên thô quyết định tại ngưỡng mặc định θ = 0,0 trước khi đưa qua hàm quy đổi xác suất.",
        ),
        (
            "APCER (hay FAR)",
            "Attack Presentation Classification Error Rate",
            "Tỷ lệ lọt lưới giả mạo (mẫu Spoof có s ≥ θ bị nhận nhầm là thật) — rủi ro mất tiền trực tiếp.",
        ),
        (
            "BPCER (hay FRR)",
            "Bona Fide Presentation Classification Error Rate",
            "Tỷ lệ báo động giả (mẫu Bonafide có s < θ bị từ chối nhầm là giả) — gây phiền hà người dùng thật.",
        ),
        (
            "EER",
            "Equal Error Rate",
            "Tỷ lệ sai số cân bằng tại ngưỡng θ_EER nơi APCER = BPCER; v0.9.4 đạt 5,63% (In-domain) và 12,05% (Unseen H2).",
        ),
        (
            "minDCF",
            "Minimum Detection Cost Function",
            "Hàm chi phí rủi ro tối thiểu chuẩn ASVspoof/NIST phạt nặng lỗi bỏ lọt lừa đảo gấp 10 lần lỗi báo nhầm (C_fa = 10, C_miss = 1).",
        ),
        (
            "F5-TTS & OmniVoice CFM",
            "Dual-Seen Zero-Shot TTS Engines",
            "Hai công cụ nhân bản giọng nói họ Flow Matching dùng trong huấn luyện v0.9.4 (6.170 tệp F5-TTS & 6.445 tệp OmniVoice đối xứng).",
        ),
        (
            "VieNeu-TTS v3 Turbo",
            "Unseen Zero-Shot OOD Engine (H2)",
            "Động cơ Qwen LLM + NeuCodec 48kHz cô lập 100% khỏi Train/Dev của v0.9.4 để chấm điểm khả năng bắt công cụ lạ (955 mẫu Dev & 375 mẫu 5-SPK).",
        ),
        (
            "5 SPK Nghiệm Thu",
            "Official Isolated Acceptance Benchmark",
            "Năm tình nguyện viên SPK_0003..0007 (84 tệp sạch × 5 codecs = 420 tệp thật) cô lập tuyệt đối 100% để nghiệm thu độc lập.",
        ),
        (
            "Voice_Final (103.189 tệp)",
            "Immutable Acceptance Archive",
            "Kho dữ liệu nghiệm thu chuẩn hóa gồm 70.174 tệp bonafide, 13.955 tệp spoof/v7 và 19.060 tệp spoof/v8 kèm băm SHA-256.",
        ),
        (
            "64.000 mẫu (4,0 giây)",
            "Fixed Input Tensor Length @ 16kHz",
            "Độ dài sóng âm chuẩn bắt buộc của khối Wav2Vec 2.0 + AASIST (4,0 giây × 16.000 mẫu/giây).",
        ),
        (
            "Repeat Padding (np.tile)",
            "Cyclic Waveform Concatenation",
            "Quy tắc bắt buộc nối lặp tuần hoàn đoạn thoại ngắn cho đủ 64.000 mẫu; nghiêm cấm đệm số 0 (Zero-Padding).",
        ),
        (
            "EBU R128 (−23 LUFS)",
            "Perceptual Loudness Standard",
            "Chuẩn hóa độ to cảm nhận phát thanh quốc tế kết hợp chuẩn hóa Z-score (μ = 0, σ = 1) triệt tiêu đường tắt âm lượng.",
        ),
        (
            "Zalo Dual Profile",
            "aac_zalo_76k & opus_zalo_24k",
            "Hai cấu hình nén thực tế của Zalo: gửi tệp âm thanh đính kèm AAC-LC 76kbps (.m4a) và ghi âm tin nhắn thoại Opus 24kbps (.ogg).",
        ),
        (
            "PSTN & GSM Narrowband",
            "g711_alaw & amr_nb (8kHz)",
            "Hai kênh thoại viễn thông băng hẹp 8.000 Hz chỉ giữ lại dải tần 300–3.400 Hz, xóa trắng toàn bộ phổ tần cao > 3,4 kHz.",
        ),
        (
            "RawBoost (LnL + ISD)",
            "Waveform Data Augmentation",
            "Tăng cường nhiễu tích chập tuyến tính/phi tuyến và nhiễu xung phụ thuộc tín hiệu ngay trong lúc nạp batch huấn luyện.",
        ),
        (
            "AM-Softmax (s=30, m=0,20)",
            "Additive Margin Softmax + Weighted CE",
            "Hàm mất mát biên góc cộng kết hợp trọng số lớp động w_c = N / (2 · N_c) ép các vector đặc trưng gom cụm chặt và tách biên xa.",
        ),
        (
            "Consensus Asymmetric Veto",
            "5-Window Inference Aggregation",
            "Gộp 5 cửa sổ trượt 4,0s (hop 1,0s): bắt nhạy cửa sổ giả âm sâu (< −12,0) đồng thời bảo vệ giọng thật có đa số cửa sổ ≥ +6,0.",
        ),
        (
            "Borderline Zone (|s − θ| ≤ 8,0)",
            "Forensic Uncertainty Guardrail",
            "Vùng nghi vấn quanh ngưỡng quyết định: tự động bật cảnh báo màu hổ phách yêu cầu xác minh lại bằng cuộc gọi video/trực tiếp.",
        ),
        (
            "Zero-Persistence & SHA-256",
            "Biometric Privacy Compliance",
            "Xử lý in-memory 100% trên RAM và chỉ ghi log bằng mã băm một chiều SHA-256 tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15.",
        ),
        (
            "392/392 Unit Tests",
            "Automated TDD Quality Gate",
            "Bộ 392 bài kiểm thử đơn vị tự động bảo chứng toàn bộ công thức DSP, chia tập không rò rỉ, mạng nơ-ron, gộp cửa sổ và API.",
        ),
    ]

    add_styled_table(
        doc,
        headers=[
            "Thuật Ngữ / Ký Hiệu",
            "Tên Tiếng Anh / Chuẩn Tham Chiếu",
            "Bản Chất Kỹ Thuật & Con Số Mốc Trong VieTrueVoice v0.9.4",
        ],
        rows=lexicon_rows,
        col_widths=[1.55, 1.85, 3.30],
    )
