"""
Chương 10, 11, 12 của Sổ Tay Kỹ Thuật & Phản Biện Hội Đồng ViTrueVoice v0.9.4:
- Chương 10: Tối ưu độ trễ suy luận thời gian thực (NFR1 ≤ 3.0 giây) & Hiệu suất phần cứng
- Chương 11: Cẩm nang 22 câu hỏi phản biện trọng tâm trước Hội đồng bảo vệ (Chuẩn hóa v0.9.4)
- Chương 12: Hệ thống hóa từ khóa khoa học (7 trục Taxonomy) & Cẩm nang đọc bài báo quốc tế
"""

from __future__ import annotations

from .styles import (
    add_bullet_item,
    add_callout_box,
    add_defense_qa,
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


def add_chapters_10_to_12(doc, figs: dict | None = None) -> None:
    """Render Chapters 10, 11, and 12 with primers, native OMML math, v0.9.4 metrics, and glossaries."""
    _ = figs  # Reserved for optional figure hooks from top-level document builder

    # =========================================================================
    # CHƯƠNG 10: TỐI ƯU ĐỘ TRỄ SUY LUẬN THỜI GIAN THỰC (NFR1 ≤ 3.0 GIÂY)
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 10",
        "Tối Ưu Độ Trễ Suy Luận Thời Gian Thực (NFR1 ≤ 3.0 Giây) & Hiệu Suất Phần Cứng",
    )

    add_foundation_primer(
        doc,
        process_name="Kỹ thuật tối ưu độ trễ thời gian thực (Latency) & Độ phức tạp tính toán phần cứng",
        why_needed=(
            "Trong tình huống lừa đảo mạo danh người thân qua Zalo hoặc cuộc gọi khẩn cấp, nạn nhân thường bị kẻ gian "
            "thúc ép chuyển tiền trong vài chục giây. Dù mô hình AI có tỷ lệ lỗi thấp đến đâu (như 5.63% EER của v0.9.4) "
            "nhưng nếu người dùng phải chờ 15–30 giây mới nhận được kết quả cảnh báo thì hệ thống mất đi giá trị phòng vệ thực tiễn. "
            "Vì vậy, Yêu cầu Phi chức năng số 1 (NFR1) của đồ án khóa cứng chỉ tiêu trung vị độ trễ phản hồi toàn trình ≤ 3.0 giây."
        ),
        real_analogy=(
            "Hãy hình dung hai hình ảnh quen thuộc: (1) Khởi động xe máy vào buổi sáng trời lạnh (Cold-Start) tốn vài giây đề máy "
            "để bơm xăng và làm nóng động cơ, nhưng khi xe đã nổ êm ở chế độ chờ (Warm-Start) thì chỉ cần nhích ga là vọt đi ngay; "
            "(2) Thang máy chở cùng lúc 5 người lên tầng 10 trong 1 chuyến duy nhất (Vectorized Batch) nhanh gấp nhiều lần so với bắt "
            "từng người đi lẻ 5 chuyến liên tiếp (Sequential Loop)."
        ),
        core_points=[
            "**Khởi động lạnh (`Cold-Start`) so với Khởi động ấm (`Warm-Start`)**: Khi máy chủ vừa bật, lượt suy luận đầu tiên thường chậm bất thường (3–6 giây) vì PyTorch phải khởi tạo ngữ cảnh `CUDA Runtime`, biên dịch hạt nhân `cuDNN` và cấp phát vùng nhớ đệm trên card đồ họa. Chạy nháp một tensor giả (`Dummy Tensor Pre-warming`) ngay lúc khởi động máy chủ giúp gánh hết chi phí này trước khi người dùng đầu tiên truy cập.",
            "**Độ phức tạp thuật toán (`Big-O`) — `O(N log N)` của FFT so với `O(L² · d)` của Transformer Attention**: Phép biến đổi phổ nhanh `FFT` trên `N = 64.000` mẫu âm thanh chỉ cần xấp xỉ `N · log₂(N) ≈ 1,02 triệu` phép tính. Ngược lại, cơ chế Tự chú ý (`Self-Attention`) trong 12 tầng Transformer của `Wav2Vec 2.0` có độ phức tạp bậc hai `O(L² · d)` theo số khung thời gian `L`. Khóa cố định mỗi cửa sổ đúng `4,0 giây` (`L = 199` khung, `d = 768`) giúp ngăn chặn sự bùng nổ chi phí bậc hai khi gặp tệp ghi âm dài.",
            "**Cấp phát bộ nhớ `VRAM` & Nghẽn cổ chai giao tiếp `CPU–GPU PCIe`**: Âm thanh tải từ mạng nằm trên `RAM` của `CPU`. Muốn `GPU` tính toán, dữ liệu phải đi qua khe cắm `PCIe` sang `VRAM`. Nếu truyền nhỏ lẻ nhiều lần hoặc giải mã qua ổ cứng, thời gian chờ vận chuyển dữ liệu còn lâu hơn thời gian nhân ma trận của `GPU`.",
            "**Vòng lặp tuần tự (`Sequential Loop`) so với Gom lô Vector hóa (`Vectorized Mini-Batch Tensor`)**: Một đoạn tin nhắn thoại dài 8 giây được cắt thành 5 cửa sổ trượt. Thay vì gọi mô hình chạy lặp 5 lần nối tiếp nhau (`5 × T_single`), việc xếp chồng 5 cửa sổ thành một khối tensor `(5, 64000)` cho phép hàng nghìn nhân `CUDA` tính toán đồng thời trong **1 lượt truyền tiến (`forward pass`) duy nhất**.",
        ],
    )

    add_heading_section(
        doc,
        "10.1 Phân Rã Toán Học Độ Trễ Toàn Trình (End-to-End Latency) & Độ Phức Tạp Khối Mạng",
    )
    add_styled_paragraph(
        doc,
        "Để tối ưu tốc độ một cách khoa học thay vì chỉnh sửa cảm tính, ViTrueVoice bóc tách tổng thời gian phản hồi "
        "từ lúc máy chủ FastAPI hoặc Telegram Bot nhận gói tin âm thanh cho tới lúc trả về kết quả JSON thành 4 thành phần độc lập:",
    )

    eq_lat_xml = (
        omml_sub(omml_r("T"), omml_r("total", normal=True))
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("T"), omml_r("decode", normal=True))
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("T"), omml_r("DSP", normal=True))
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("T"), omml_r("forward", normal=True))
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("T"), omml_r("post", normal=True))
        + omml_r(" ≤ 3,0 s", normal=True)
    )
    add_omml_equation(
        doc,
        formula_title="Phương trình phân rã độ trễ suy luận toàn trình (End-to-End Latency Budget)",
        omml_body_xml=eq_lat_xml,
        variables=[
            ("T_total", "Tổng độ trễ toàn trình đo từ lúc nhận luồng byte âm thanh đến khi xuất phản hồi JSON (mục tiêu NFR1 ≤ 3,0 giây)."),
            ("T_decode", "Thời gian nhận diện chữ ký số `Magic Bytes` và giải mã đa định dạng (WAV, MP3, M4A, AAC, Opus, AMR) về sóng PCM 16 kHz đơn kênh trên bộ nhớ RAM."),
            ("T_DSP", "Thời gian cắt khoảng lặng đầu/cuối, chuẩn hóa biên độ, nối lặp `Repeat Padding` và trích xuất lô đa cửa sổ trượt kích thước `(K, 64000)` với `1 ≤ K ≤ 5`."),
            ("T_forward", "Thời gian truyền khối tensor qua khe cắm `PCIe` và chạy suy luận mạng `SSL-AASIST v0.9.4` trong chế độ `torch.inference_mode()`."),
            ("T_post", "Thời gian gộp điểm bằng thuật toán `Consensus Asymmetric Veto`, hiệu chuẩn xác suất `Platt Scaling (T = 16,0)` và ghi nhật ký băm ẩn danh `SHA-256`."),
        ],
    )

    add_styled_paragraph(
        doc,
        "Trong 4 thành phần trên, `T_forward` phụ thuộc trực tiếp vào độ phức tạp tính toán của mặt trước tự giám sát "
        "`Wav2Vec 2.0` (gồm 7 tầng tích chập `CNN` hạ mẫu với bước nhảy tổng cộng `320 mẫu` và 12 tầng `Transformer Encoder` chiều ẩn `d = 768`) "
        "cùng mặt sau đồ thị không đồng nhất `Compact AASIST`. Khi khóa cứng chiều dài mỗi cửa sổ ở mức `N = 64.000` mẫu (`4,0 giây` tại `16 kHz`), "
        "số khung biểu diễn đi vào khối Transformer luôn cố định chính xác tại `L = 199` khung:",
    )

    eq_comp_xml = (
        omml_sub(omml_r("C"), omml_r("FFT", normal=True))
        + omml_r(" = ", normal=True)
        + omml_r("O", normal=True)
        + omml_delim(
            omml_r("N") + omml_r(" · ", normal=True) + omml_sub(omml_r("log", normal=True), omml_r("2", normal=True)) + omml_r("N")
        )
        + omml_r(" ,     ", normal=True)
        + omml_sub(omml_r("C"), omml_r("Attn", normal=True))
        + omml_r(" = ", normal=True)
        + omml_r("O", normal=True)
        + omml_delim(
            omml_r("K") + omml_r(" · ", normal=True) + omml_sup(omml_r("L"), omml_r("2", normal=True)) + omml_r(" · ", normal=True) + omml_r("d")
        )
    )
    add_omml_equation(
        doc,
        formula_title="Đối sánh độ phức tạp tiệm cận giữa Biến đổi FFT và Tự chú ý Transformer theo cửa sổ trượt",
        omml_body_xml=eq_comp_xml,
        variables=[
            ("N = 64.000", "Số mẫu âm thanh cố định của mỗi cửa sổ trượt 4,0 giây ở tần số lấy mẫu chuẩn 16.000 Hz."),
            ("L = 199", "Số khung thời gian sau khối tích chập CNN của Wav2Vec 2.0, tính bởi `⌊(64.000 − 400) / 320⌋ + 1 = 199` khung."),
            ("d = 768", "Số chiều vector đặc trưng ẩn tại mỗi tầng Transformer của mô hình `wav2vec2-base-vietnamese-250h`."),
            ("K ≤ 5", "Số lượng cửa sổ trượt tối đa được lấy mẫu đều trên toàn bộ đoạn thoại. Nhờ chia thành `K` cửa sổ cố định thay vì đưa nguyên đoạn dài `5·L` vào mạng, chi phí giảm từ `(5·L)² = 25·L²` xuống chỉ còn `5·L²` (tiết kiệm gấp 5 lần phép tính và bộ nhớ VRAM!)."),
        ],
    )

    add_heading_section(
        doc,
        "10.2 Bốn (04) Kỹ Thuật Tối Ưu Hóa Độ Trễ Cốt Lõi Trong ViTrueVoice v0.9.4",
    )
    add_styled_paragraph(
        doc,
        "Hệ thống sản xuất của ViTrueVoice (`src/app/server.py`, `src/preprocessing/audio_loader.py` và `src/preprocessing/pooling.py`) "
        "triển khai đồng bộ 4 kỹ thuật tối ưu hóa phần cứng và phần mềm để ép tổng độ trễ xuống dưới 1 giây:",
    )

    add_heading_subsection(
        doc,
        "10.2.1 Kỹ Thuật 1: Khởi Tạo Singleton Mô Hình & Làm Ấm Trước Bằng Tensor Giả (Dummy Tensor Pre-warming)",
    )
    add_bullet_item(
        doc,
        "Trọng số chính thức `out/v0.9.4/best_model.pt` được hàm `resolve_default_checkpoint()` nạp **duy nhất một lần** vào không gian bộ nhớ "
        "theo mẫu thiết kế `Singleton` ngay khi tiến trình máy chủ khởi chạy, tuyệt đối không nạp lại tệp `.pt` ở từng lượt gọi API.",
        bold_prefix="Nạp trọng số Singleton một lần",
    )
    add_bullet_item(
        doc,
        "Ngay sau khi chuyển sang trạng thái `model.eval()`, hệ thống tự động tạo một tensor giả lập kích thước chuẩn `(1, 64000)` "
        "đặt trong ngữ cảnh `torch.inference_mode()` để chạy thông toàn bộ đồ thị `Wav2Vec 2.0 + Compact AASIST`. "
        "Bước làm ấm này buộc trình điều khiển NVIDIA khởi tạo xong `CUDA Context`, biên dịch sẵn hạt nhân `cuDNN` và mở khóa bộ cấp phát bộ nhớ đệm (`PyTorch Caching Allocator`) trước khi mở cổng nhận truy cập.",
        bold_prefix="Làm ấm hạt nhân bằng Dummy Tensor `(1, 64000)`",
    )
    add_bullet_item(
        doc,
        "Sử dụng ngữ cảnh `with torch.inference_mode():` (cấp tối ưu cao hơn cả `torch.no_grad()` trong PyTorch `2.6`) giúp tắt hoàn toàn "
        "bộ đếm phiên bản tensor (`version counter`) và siêu dữ liệu đồ thị đạo hàm, giảm cả thời gian CPU điều phối lẫn dung lượng VRAM tiêu thụ.",
        bold_prefix="Tắt triệt để đồ thị đạo hàm với `torch.inference_mode()`",
    )

    add_heading_subsection(
        doc,
        "10.2.2 Kỹ Thuật 2: Giải Mã Âm Thanh Đa Định Dạng Trực Tiếp Trên RAM (In-Memory FFmpeg Pipe)",
    )
    add_bullet_item(
        doc,
        "Thay vì ghi tệp âm thanh người dùng tải lên xuống ổ cứng rồi gọi câu lệnh đọc lại từ đĩa (gây trễ I/O 20–80 ms và để lại dấu vết dữ liệu sinh trắc học), "
        "hàm `load_audio` đọc trực tiếp chuỗi byte thô trong bộ đệm `io.BytesIO` trên RAM.",
        bold_prefix="Xử lý luồng byte hoàn toàn trên bộ nhớ `io.BytesIO`",
    )
    add_bullet_item(
        doc,
        "Bộ phân tích chữ ký nhị phân đầu tệp (`Magic Bytes`: `RIFF/WAVE`, `OggS`, `ID3`, `ftyp`, `#!AMR`) nhận diện tức thì định dạng thật sự "
        "mà không phụ thuộc đuôi tệp tin, sau đó đẩy luồng dữ liệu qua đường ống `FFmpeg stdin/stdout pipe` để chuẩn hóa về mảng `float32` đơn kênh `16.000 Hz` trong vài chục mili-giây.",
        bold_prefix="Nhận diện `Magic Bytes` & giải mã qua đường ống `FFmpeg Pipe`",
    )

    add_heading_subsection(
        doc,
        "10.2.3 Kỹ Thuật 3: Vector Hóa Đa Cửa Sổ Thành Mini-Batch `(5, 64000)` Trong 1 Lượt Forward Duy Nhất",
    )
    add_styled_paragraph(
        doc,
        "Đây là quyết định kiến trúc mang lại bước nhảy tốc độ lớn nhất cho thuật toán cắt đa cửa sổ (`src/preprocessing/pooling.py`). "
        "Hàm `extract_window_batch` cắt tối đa `K = 5` cửa sổ trượt chồng lấp (`win = 64.000`, `hop = 16.000`, bật `dense_slicing = True`) "
        "và xếp chồng chúng bằng `torch.stack(windows, dim=0)` thành một tensor liên tục `(5, 64000)`. Hàm `batch_window_forward` đẩy toàn bộ khối này "
        "qua GPU trong **1 lượt truyền tiến duy nhất** thay vì chạy vòng lặp `for` 5 lần:",
    )

    eq_batch_xml = (
        omml_sub(omml_r("T"), omml_r("batch", normal=True))
        + omml_delim(omml_r("K"))
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("T"), omml_r("PCIe", normal=True))
        + omml_delim(omml_r("K"))
        + omml_r(" + ", normal=True)
        + omml_sub(omml_r("T"), omml_r("GPU", normal=True))
        + omml_delim(omml_r("K"))
        + omml_r(" ≪ ", normal=True)
        + omml_r("K")
        + omml_r(" · ", normal=True)
        + omml_delim(
            omml_sub(omml_r("T"), omml_r("PCIe", normal=True))
            + omml_delim(omml_r("1", normal=True))
            + omml_r(" + ", normal=True)
            + omml_sub(omml_r("T"), omml_r("GPU", normal=True))
            + omml_delim(omml_r("1", normal=True))
        )
    )
    add_omml_equation(
        doc,
        formula_title="Định luật tiết kiệm độ trễ nhờ gộp lô song song đa cửa sổ trên GPU",
        omml_body_xml=eq_batch_xml,
        variables=[
            ("T_batch(K)", "Thời gian suy luận thực tế khi gom tất cả `K` cửa sổ thành 1 mini-batch `(K, 64000)` chạy trong 1 lượt gọi mô hình."),
            ("T_PCIe(K)", "Chi phí khởi tạo giao dịch truyền dữ liệu từ RAM sang VRAM qua bus `PCIe` (chỉ tốn 1 lần mở giao dịch thay vì `K` lần)."),
            ("T_GPU(K)", "Thời gian các nhân Tensor/CUDA thực thi phép nhân ma trận song song. Trên `NVIDIA RTX 3050 4GB`, `K = 5` cửa sổ vẫn nằm gọn trong băng thông nhân song song nên `T_batch(5)` chỉ mất trung vị **66,3 ms** (`P90 = 68,2 ms`)."),
        ],
    )

    add_heading_subsection(
        doc,
        "10.2.4 Kỹ Thuật 4: Tinh Gọn Chiều Đồ Thị Compact AASIST & Kỷ Luật Quản Trị Bộ Nhớ FP16 / FP32",
    )
    add_bullet_item(
        doc,
        "Khối `Compact AASIST` chiếu biểu diễn `768 chiều` của `Wav2Vec 2.0` xuống không gian nút thời gian – tần số thu gọn trước khi đi vào "
        "các tầng chú ý đồ thị không đồng nhất `HS-GAL` và `Master Node`, giúp giảm hơn 60% số phép nhân ma trận dư thừa mà vẫn giữ trọn độ nhạy phát hiện vi nhiễu pha.",
        bold_prefix="Thu gọn chiều không gian đồ thị `Compact AASIST`",
    )
    add_bullet_item(
        doc,
        "Trong pha huấn luyện trên card đồ họa phổ thông `RTX 3050 4GB VRAM`, hệ thống kết hợp độ chính xác hỗn hợp tự động (`AMP FP16`) "
        "với tích lũy đạo hàm (`batch_size = 8`, `accum_steps = 2`, tương đương lô hiệu dụng `16`) để giữ mức chiếm dụng VRAM ổn định ở `2,8–3,2 GB`. "
        "Khi sang pha suy luận thời gian thực, đầu phân loại tính điểm ở `FP32` chuẩn xác nhằm tránh sai số làm tròn gần ngưỡng quyết định `θ = 0,0`.",
        bold_prefix="Kỷ luật bộ nhớ `FP16` khi huấn luyện & `FP32` chính xác khi suy luận",
    )

    add_heading_section(
        doc,
        "10.3 Bảng Kết Quả Thực Đo Độ Trễ Đã Kiểm Chứng Của Hệ Thống v0.9.4",
    )
    add_styled_paragraph(
        doc,
        "Bảng 10.1 tổng hợp đầy đủ các mốc đo độ trễ thực nghiệm của ViTrueVoice `v0.9.4` từ bước nghe thủ công ban đầu đến "
        "các kịch bản kiểm định API, nhật ký vận hành thực tế và tốc độ thuần của mô hình trên phần cứng GPU:",
    )

    add_styled_table(
        doc,
        headers=[
            "Cấp Độ / Kịch Bản Đo Kiểm",
            "Phạm Vi Bao Phủ Kỹ Thuật",
            "Nguồn Dữ Liệu Kiểm Chứng",
            "Trung Vị (P50)",
            "So Với Trần NFR1 (≤ 3.0s)",
        ],
        rows=[
            (
                "Baseline Thủ Công (Trước đề tài)",
                "Người dùng tự nghe tai trực tiếp 72 lượt (hoặc gọi xác minh người thân 2–5 phút)",
                "`benchmarks/human_baseline_metrics.csv`",
                "5,310 giây",
                "Vượt trần (Chậm & EER 34,72%)",
            ),
            (
                "Benchmark Chính Thức 30 Ca API / Bot",
                "Toàn trình HTTP/Bot + giải mã FFmpeg in-memory + 5 cửa sổ trượt + Platt + SHA-256 log",
                "`benchmarks/latency_benchmark.csv` (30 lượt chuẩn)",
                "**1,101 giây**",
                "**ĐẠT — Nhanh gấp ~2,7 lần trần 3.0s**",
            ),
            (
                "Telemetry Vận Hành Cục Bộ Thực Tế",
                "Toàn trình API sản xuất ghi nhận qua 140 lượt thẩm định thực tế ẩn danh SHA-256",
                "`benchmarks/latency_log.json` (140 lượt chạy)",
                "**0,705 giây**",
                "**ĐẠT — Nhanh gấp ~4,3 lần trần 3.0s**",
            ),
            (
                "Lượt Truyền Tiến Thuần Mô Hình GPU",
                "1 forward pass gộp lô `(5, 64000)` của `SSL-AASIST v0.9.4` trên GPU `RTX 3050 4GB`",
                "`scripts/benchmark_latency.py --pooling`",
                "**66,3 ms** (`P90 = 68,2 ms`)",
                "**ĐẠT — Nhanh gấp ~45 lần trần 3.0s**",
            ),
        ],
        col_widths=[1.45, 1.85, 1.35, 1.0, 1.05],
        highlight_row_pred=lambda idx, _: idx in (1, 2, 3),
    )

    add_callout_box(
        doc,
        "Khi Hội đồng hỏi về tốc độ xử lý, sinh viên cần phân biệt rành mạch hai con số để thể hiện sự chính xác kỹ thuật: "
        "**(1) Độ trễ toàn trình tính cả tải tệp, giải mã FFmpeg trên RAM và trả JSON** đạt trung vị **1,101 giây** trên bộ 30 ca chuẩn "
        "và **0,705 giây** trên 140 lượt chạy thực tế; **(2) Riêng lượt chạy mạng nơ-ron đa cửa sổ `(5, 64000)` trên GPU RTX 3050 4GB** "
        "chỉ mất **66,3 mili-giây** (`P90 = 68,2 ms`). Cả hai đều bỏ xa ngưỡng yêu cầu **NFR1 ≤ 3,0 giây**!",
        title="MẸO PHẢN BIỆN CHƯƠNG 10: PHÂN BIỆT RÕ ĐỘ TRỄ TOÀN TRÌNH VÀ ĐỘ TRỄ THUẦN GPU",
    )

    add_term_glossary(
        doc,
        terms=[
            ("NFR", "Non-Functional Requirement", "Yêu cầu phi chức năng — quy định chất lượng vận hành hệ thống (như độ trễ ≤ 3,0 giây, bảo mật không lưu vết) bên cạnh độ chính xác nhận diện."),
            ("Latency", "End-to-End Inference Latency", "Độ trễ suy luận toàn trình — tổng thời gian chờ từ lúc gửi đoạn thoại đến lúc nhận về nhãn Thật/Giả trên giao diện."),
            ("Cold-Start", "Cold-Start Latency", "Hiện tượng lượt gọi đầu tiên sau khi bật máy chủ bị trễ nhiều giây do phần cứng GPU và thư viện phần mềm chưa khởi tạo xong bộ nhớ đệm."),
            ("Pre-warming", "Dummy Tensor Warm-up", "Kỹ thuật chạy nháp một tensor giả lập `(1, 64000)` ngay lúc bật máy chủ để làm nóng toàn bộ hạt nhân tính toán trước khi phục vụ người dùng."),
            ("Big-O Complexity", "Asymptotic Computational Complexity", "Ký hiệu toán học đo tốc độ tăng số phép tính khi kích thước đầu vào lớn lên, ví dụ `O(N log N)` hoặc `O(L² · d)`."),
            ("FFT", "Fast Fourier Transform", "Thuật toán Biến đổi Fourier Nhanh chuyển tín hiệu âm thanh từ miền thời gian sang miền tần số với chi phí siêu nhẹ `O(N log N)`."),
            ("VRAM", "Video Random Access Memory", "Bộ nhớ chuyên dụng tốc độ cao nằm ngay trên card đồ họa GPU để chứa trọng số mô hình và các khối tensor đang tính toán."),
            ("Vectorization / Batching", "Vectorized Mini-Batch Processing", "Kỹ thuật gom nhiều cửa sổ dữ liệu thành một mảng đa chiều duy nhất `(5, 64000)` để GPU xử lý song song trong một nhịp lệnh."),
            ("P50 / Median & P90", "50th & 90th Percentile Latency", "`P50` (trung vị) là mốc thời gian mà 50% số lượt chạy nhanh hơn mốc đó; `P90` là mốc mà 90% số lượt chạy đều hoàn tất nhanh hơn, giúp đánh giá độ ổn định khi tải cao."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 11: CẨM NANG 22 CÂU HỎI PHẢN BIỆN TRỌNG TÂM (CHUẨN HÓA v0.9.4)
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 11",
        "Cẩm Nang 22 Câu Hỏi Phản Biện Trọng Tâm Trước Hội Đồng Bảo Vệ (Chuẩn Hóa v0.9.4)",
    )

    add_foundation_primer(
        doc,
        process_name="Công thức vàng 3 bước trả lời phản biện trước Hội đồng chấm đồ án",
        why_needed=(
            "Tại buổi bảo vệ đồ án tốt nghiệp, quỹ thời gian hỏi – đáp chỉ kéo dài 10–15 phút cho hàng chục quyết định kỹ thuật. "
            "Nếu sinh viên trả lời lan man, kể lể lịch sử dài dòng mới vào ý chính, Giảng viên phản biện rất dễ ngắt lời hoặc đánh giá "
            "sinh viên không nắm chắc bản chất cốt lõi của hệ thống mình xây dựng."
        ),
        real_analogy=(
            "Hãy trả lời Hội đồng giống như một bác sĩ báo cáo hội chẩn cấp cứu: (1) Nêu ngay chẩn đoán kết luận trong câu mở đầu, "
            "(2) Giải thích ngắn gọn cơ chế sinh lý dẫn tới chẩn đoán đó, và (3) Đưa ngay tờ phiếu xét nghiệm có chỉ số định lượng "
            "để chứng minh không thể bác bỏ."
        ),
        core_points=[
            "**Bước 1 — Chốt thẳng kết luận trực diện trong 1 câu đầu tiên**: Mở lời bằng câu khẳng định rõ ràng (*\"Dạ thưa Thầy/Cô, nhóm em thiết kế cơ chế X nhằm giải quyết trực tiếp bài toán Y...\"*), tuyệt đối không vòng vo.",
            "**Bước 2 — Giải thích bản chất vật lý / toán học dễ hiểu**: Lý giải tại sao hiện tượng đó xảy ra (do đứt gãy pha sóng âm, do nén mất mát codec, do đạo hàm hàm mất mát hay do ranh giới phân phối dữ liệu) bằng ngôn từ mạch lạc, chuẩn thuật ngữ.",
            "**Bước 3 — Đưa con số thực nghiệm `v0.9.4` đã kiểm chứng làm bằng chứng thép**: Khép lại câu trả lời bằng số liệu thực đo chính xác của phiên bản `v0.9.4` (`5.63%` EER trên `15.980` mẫu, `12.05%` EER trên Unseen `VieNeu-TTS`, `94.76%–100%` trên bộ 5 tình nguyện viên độc lập, độ trễ `0.705s–1.101s`, `392/392` unit tests xanh, vận hành Docker cục bộ `0 VNĐ`).",
        ],
    )

    add_heading_section(
        doc,
        "11.1 Toàn Văn 22 Câu Hỏi & Đáp Án Chuẩn Mực 3 Bước (Cập Nhật Đầy Đủ Số Liệu v0.9.4)",
    )
    add_styled_paragraph(
        doc,
        "Mỗi câu hỏi dưới đây được cấu trúc thống nhất gồm **Câu hỏi của Hội đồng**, **Ý đồ kiểm tra của Giảng viên** "
        "và **Trả lời chuẩn mực 3 bước** bám sát hoàn toàn kiến trúc cùng số liệu nghiệm thu chính thức `v0.9.4`:",
    )

    def _qa(q_num: int, question: str, intent: str, step1: str, step2: str, step3: str) -> None:
        add_defense_qa(doc, q_num, question, intent, step1, step2, step3)

    # Q1: Anti-spoofing CM vs ASV
    _qa(
        1,
        "Bài toán chống giả mạo giọng nói (Anti-spoofing CM) của đề tài khác gì so với nhận dạng / xác thực người nói (ASV)?",
        "Kiểm tra xem sinh viên có phân biệt rành mạch bài toán phát hiện giọng nói nhân tạo độc lập với bài toán so khớp danh tính vân giọng hay không.",
        "Dạ thưa Thầy/Cô, ViTrueVoice giải quyết bài toán **Phát hiện giả mạo tiếng nói độc lập (`Stand-alone Anti-spoofing Countermeasure - CM`)**, hoàn toàn khác mục tiêu với hệ thống Xác thực người nói (`Automatic Speaker Verification - ASV`).",
        "Hệ thống `ASV` trả lời câu hỏi *\"Người đang nói có đúng là anh Nguyễn Văn A đã đăng ký vân giọng từ trước hay không?\"* thông qua khoảng cách cosine giữa hai vector đặc trưng người nói (`Speaker Embedding`). Ngược lại, khối `CM` của chúng em trả lời câu hỏi *\"Sóng âm này phát ra từ dây thanh quản sinh học của con người thật hay do thuật toán AI tổng hợp ra?\"* dựa trên các vi nhiễu pha và hài âm mà hoàn toàn không cần biết người nói tên là gì hay phải thu thập mẫu giọng đăng ký trước.",
        "Nhờ kiến trúc `CM` độc lập người nói, ViTrueVoice `v0.9.4` bảo vệ tức thì bất kỳ người dân nào nhận tin nhắn thoại lạ trên Zalo/Telegram mà không cần kho vân giọng quốc gia, đạt **5.63% EER** trên `15.980` mẫu kiểm thử của những người nói chưa từng xuất hiện trong tập huấn luyện.",
    )

    # Q2: Vietnamese Wav2Vec2-250h vs English XLSR or MFCC/LFCC
    _qa(
        2,
        "Tại sao nhóm chọn mô hình tự giám sát tiếng Việt (wav2vec2-base-vietnamese-250h) thay vì XLSR đa ngữ/tiếng Anh hoặc đặc trưng thủ công MFCC/LFCC?",
        "Kiểm tra lý do khoa học của việc chọn biểu diễn học tự giám sát bản địa cho ngôn ngữ có thanh điệu như tiếng Việt.",
        "Dạ thưa Thầy/Cô, chúng em chọn `wav2vec2-base-vietnamese-250h` vì tiếng Việt là ngôn ngữ đơn âm tiết có **6 thanh điệu** phức tạp, nơi các công cụ nhân bản giọng nói dễ bộc lộ sai lệch vi mô nhất ở đường cong tần số cơ bản `F0` và chuyển tiếp nguyên âm.",
        "Các đặc trưng thủ công như `MFCC` hay `LFCC` dùng hệ bộ lọc tần số cố định và lấy log biên độ nên đánh mất phần lớn thông tin pha tinh vi, lại dễ bị sụp đổ khi kênh thoại Zalo/GSM cắt mất dải tần trên `3.400 Hz`. Trong khi đó, mô hình `XLSR` đa ngữ phải chia sẻ dung lượng tham số cho hàng chục ngôn ngữ không thanh điệu; còn `wav2vec2-base-vietnamese-250h` được tiền huấn luyện tự giám sát chuyên biệt trên `250 giờ` tiếng Việt chuẩn nên nắm bắt cực nhạy cấu trúc hài âm của thanh hỏi, thanh ngã và thanh nặng.",
        "Thực nghiệm đối chứng trong đồ án chứng minh mô hình `SSL-AASIST` dùng `wav2vec2-base-vietnamese-250h` kéo giảm sai số vượt trội so với baseline `LFCC+GMM`, đưa `In-domain EER` trên toàn bộ 5 biến thể kênh nén của `v0.9.4` xuống mức **4.88% – 6.11%** (trung bình gộp **5.63%**).",
    )

    # Q3: Repeat Padding 64k vs Zero-Padding
    _qa(
        3,
        "Tại sao khi đoạn thoại ngắn hơn 4.0 giây (< 64.000 mẫu), hệ thống bắt buộc nối lặp (Repeat Padding) thay vì đệm số 0 (Zero-Padding)?",
        "Kiểm tra sự am hiểu về xử lý tín hiệu số (DSP) và nguy cơ rò rỉ đặc trưng giả (artifact) do tiền xử lý sai cách.",
        "Dạ thưa Thầy/Cô, chúng em khóa cứng kỹ thuật **Nối lặp (`Repeat Padding` qua `np.tile` / `torch.tile`)** và nghiêm cấm `Zero-Padding` để bảo toàn tính liên tục phổ – thời gian cho khối tích chập của `Wav2Vec 2.0` và đồ thị `AASIST`.",
        "Nếu chèn một chuỗi số `0` vào đuôi đoạn âm thanh ngắn, tại ranh giới chuyển tiếp sẽ xuất hiện một vách đứt gãy biên độ đột ngột (gây hiện tượng rung `Gibbs` làm loang năng lượng giả lên toàn bộ các dải tần số cao), đồng thời tạo ra vùng năng lượng bằng `0` nhân tạo khiến mạng đồ thị `HS-GAL` học nhầm độ dài đoạn thoại thay vì học dấu vết giả mạo.",
        "Quy tắc `Repeat Padding` đủ chính xác `64.000 mẫu` (`4.0 giây @ 16 kHz`) là một bất biến kỹ thuật được kiểm tra tự động trong bộ **`392/392 bài kiểm thử đơn vị (unit tests)`**, giúp các mẫu thoại ngắn dưới 4 giây trong bộ nghiệm thu 5 tình nguyện viên đạt tỷ lệ nhận diện đúng tới **100% (64/64)** trên 4 người nói đối chứng `SPK_0004..0007`.",
    )

    # Q4: Dynamic Weighted CE without WeightedRandomSampler + OMML
    _qa(
        4,
        "Tại sao hàm mất mát Weighted Cross-Entropy phải tính động theo tần suất tập Train và tuyệt đối không dùng chung với WeightedRandomSampler?",
        "Kiểm tra kiến thức toán học về tối ưu hóa trên dữ liệu mất cân bằng lớp (Class Imbalance) trong học sâu.",
        "Dạ thưa Thầy/Cô, chúng em tính động trọng số lớp theo tỷ lệ nghịch tần suất mẫu thực tế qua hàm `loss_weights_from_counts` và cấm tuyệt đối việc bật đồng thời `WeightedRandomSampler` nhằm ngăn chặn lỗi **Bù trừ kép (`Double Penalty`)**.",
        "Tập huấn luyện chính thức `54.400` dòng có tỷ lệ giọng thật nhiều hơn giọng giả khoảng `6,4 : 1`. Khi đặt trọng số mất mát tỉ lệ nghịch `w_c = N / (2 · N_c)`, tổng đóng góp đạo hàm kỳ vọng của lớp Giọng thật và lớp Giọng giả trong mỗi epoch đã cân bằng chính xác `1 : 1`. Nếu còn dùng thêm `WeightedRandomSampler` để ép mỗi mini-batch có tỷ lệ mẫu `50 : 50`, lớp thiểu số sẽ bị nhân hệ số khuếch đại hai lần liên tiếp, làm lệch nghiêm trọng biên quyết định `θ = 0.0`.",
        "Nhờ cơ chế trọng số động không bù trừ kép kết hợp `AM-Softmax (s = 30.0, m = 0.20)`, mô hình `v0.9.4` hội tụ mượt mà trên tập `54.400` dòng, đạt cân bằng tối ưu giữa khả năng chặn giả (**95.01%**) và tỷ lệ báo nhầm người thật thấp (**BPCER = 6.73%**).",
    )

    eq_wce_xml = (
        omml_sub(omml_r("w"), omml_r("c"))
        + omml_r(" = ", normal=True)
        + omml_frac(
            omml_r("N"),
            omml_r("2", normal=True) + omml_r(" · ", normal=True) + omml_sub(omml_r("N"), omml_r("c")),
        )
        + omml_r(" ,     ", normal=True)
        + omml_sub(omml_r("L"), omml_r("WCE", normal=True))
        + omml_r(" = − ", normal=True)
        + omml_subsup(omml_r("∑", normal=True), omml_r("c=0", normal=True), omml_r("1", normal=True))
        + omml_sub(omml_r("w"), omml_r("c"))
        + omml_r(" · ", normal=True)
        + omml_sub(omml_r("y"), omml_r("c"))
        + omml_r(" · ", normal=True)
        + omml_r("log", normal=True)
        + omml_delim(omml_sub(omml_r("p"), omml_r("c")))
    )
    add_omml_equation(
        doc,
        formula_title="Trọng số lớp động nghịch đảo tần suất trong hàm mất mát Weighted Cross-Entropy",
        omml_body_xml=eq_wce_xml,
        variables=[
            ("N", "Tổng số mẫu âm thanh trong tập huấn luyện thực tế (ví dụ `N = 54.400` dòng ở tập Train chính thức `v0.9.4`)."),
            ("N_c", "Số lượng mẫu thuộc lớp `c` (`c = 0`: Giọng giả `Spoof`, `c = 1`: Giọng thật `Bonafide`)."),
            ("w_c", "Trọng số phạt động của lớp `c`, đảm bảo `N_0 · w_0 = N_1 · w_1 = N / 2` mà không cần lấy mẫu lặp `WeightedRandomSampler`."),
        ],
    )

    # Q5: Hard Speaker-Disjoint & Hard Text-Disjoint
    _qa(
        5,
        "Ràng buộc Hard Speaker-Disjoint và Hard Text-Disjoint ngăn chặn hiện tượng học vẹt lối tắt (Shortcut Learning) như thế nào?",
        "Kiểm tra tính trung thực học thuật và phương pháp thiết kế tập dữ liệu chống rò rỉ thông tin (Data Leakage).",
        "Dạ thưa Thầy/Cô, hai ràng buộc này cô lập tuyệt đối cả **danh tính người nói** lẫn **nội dung câu chữ** giữa các tập `Train`, `Dev` và `Test` để buộc mạng nơ-ron phải học dấu vết vật lý của thuật toán tổng hợp thay vì học thuộc lòng giọng người hay văn bản.",
        "Nếu cùng một người nói xuất hiện ở cả Train và Test, mô hình sẽ nhớ âm sắc thanh quản của người đó; còn nếu cùng một câu văn xuất hiện ở cả hai tập (hoặc vừa làm câu mẫu `prompt` vừa làm câu tổng hợp `eval`), mô hình sẽ nhớ chuỗi âm vị của câu chữ đó. Chúng em áp dụng lọc một chiều nghiêm ngặt: khóa nguyên vẹn tập `Test` → xóa mọi câu trùng khỏi `Dev` → xóa mọi câu trùng khỏi `Train`, đồng thời tách rời hoàn toàn tệp `prompt` tham chiếu khỏi tệp đánh giá.",
        "Toàn bộ 5 tệp manifest chuẩn 19 cột của `v0.9.4` (tổng kho `Voice_Final` **103.189 tệp**) đều vượt qua kịch bản kiểm toán tự động với **0% rò rỉ người nói** và **0% rò rỉ văn bản**.",
    )

    # Q6: normalize_for_eval only for WER/CER while TTS gets raw text
    _qa(
        6,
        "Tại sao hàm chuẩn hóa văn bản normalize_for_eval chỉ dùng cho cổng lọc WER/CER và khử trùng lặp, trong khi công cụ TTS phải nhận văn bản thô?",
        "Kiểm tra sự tinh tế khi xử lý ngôn ngữ tự nhiên tiếng Việt cho hệ thống Text-to-Speech và đánh giá ASR.",
        "Dạ thưa Thầy/Cô, chúng em tách bạch hai luồng văn bản vì **chấm điểm nhận dạng chữ (`ASR WER/CER`) cần đồng nhất mặt chữ viết**, trong khi **tổng hợp tiếng nói (`TTS`) cần giữ nguyên dấu câu và nhịp nghỉ ngữ âm tự nhiên**.",
        "Trong tiếng Việt, cùng một âm tiết như *\"hòa\"* hay *\"hoà\"* có thể khác vị trí đặt dấu thanh hoặc bảng mã Unicode (`NFD` so với `NFC`). Hàm `normalize_for_eval` chuẩn hóa về `NFC`, chỉnh vị trí dấu thanh cuối từ qua `_fix_tone_token` (không làm hỏng các vần như *\"toàn\"*) và loại câu chứa chữ số `has_digits` để tính `WER/CER` công bằng. Ngược lại, nếu đưa chuỗi đã lột sạch dấu phẩy, dấu chấm và chữ viết hoa vào `F5-TTS` hay `OmniVoice CFM`, mô hình TTS sẽ đọc liền một mạch không ngắt nghỉ, tạo ra lỗi nhịp điệu nhân tạo rất dễ bị phát hiện (làm bài toán trở nên dễ giả tạo).",
        "Nhờ giữ nguyên văn bản thô có đầy đủ dấu câu cho đầu vào TTS và chỉ dùng `normalize_for_eval` tại Cổng lọc 1, toàn bộ **6.445 mẫu `OmniVoice_CFM`** và **6.170 mẫu `F5-TTS`** đạt độ tự nhiên ngữ điệu rất cao, tạo ra thử thách sát thực tế nhất cho mô hình phòng thủ.",
    )

    # Q7: Zalo Dual-Profile + PSTN & Narrowband Codec Paradox
    _qa(
        7,
        "Cấu hình kênh nén kép Zalo (AAC-LC 76k & Opus 24k) cùng mạng viễn thông PSTN (G.711, AMR-NB) hoạt động ra sao, và vì sao kênh băng hẹp đôi khi lại giúp bắt giả tốt hơn?",
        "Kiểm tra hiểu biết chuyên sâu về nén âm thanh viễn thông và giải thích quy luật thực nghiệm trên 5 biến thể kênh truyền.",
        "Dạ thưa Thầy/Cô, hệ thống mô phỏng chính xác 5 môi trường truyền dẫn thực tế tại Việt Nam qua các bộ mã hóa chuẩn liên kết đồng bộ theo `base_utt`, và phát hiện ra **hiệu ứng tương phản lỗi pha trên kênh băng hẹp 8 kHz**.",
        "Hai cấu hình mục tiêu của Zalo gồm `Profile A (aac_zalo_76k, AAC-LC 76 kbps @ 48 kHz mono)` và `Profile B (opus_zalo_24k, Opus 24 kbps OGG)` dùng biến đổi `MDCT` tâm thính giác làm mượt nhẹ phổ cao tần. Trong khi đó, kênh thoại truyền thống `G.711 A-law` và `AMR-NB 8 kHz` không chỉ cắt băng thông về `300–3.400 Hz` mà `AMR-NB` còn dùng bộ dự đoán tuyến tính kích thích mã (`CELP`) thiết kế riêng cho thanh quản sinh học con người. Khi sóng âm tổng hợp AI đi qua bộ lọc `CELP`, sự lệch pha vi mô giữa sóng nhân tạo và mô hình thanh quản tuyến tính gây ra méo cộng hưởng rõ rệt.",
        "Số liệu thực nghiệm trên `15.980` mẫu Test của `v0.9.4` chứng minh đúng quy luật vật lý này: kênh `AMR-NB 8 kHz` đạt EER thấp kỷ lục **4.88%**, trong khi các kênh khó hơn như `Zalo AAC-LC 76k` (**5.79%**) và `Zalo Opus 24k` (**6.02%**) vẫn nằm sâu dưới trần mục tiêu `≤ 8.0%`.",
    )

    # Q8: 2-Phase training + Stage 3 head_blend_a0.75
    _qa(
        8,
        "Tại sao nhóm phải huấn luyện 2 pha (Pha 1 đóng băng SSL, Pha 2 vi chỉnh phân tầng) rồi kết hợp hiệu chuẩn đầu phân loại Giai đoạn 3 (head_blend_a0.75)?",
        "Kiểm tra tư duy huấn luyện mạng tiền huấn luyện lớn (Transfer Learning) và kỹ thuật hiệu chuẩn không gian trọng số.",
        "Dạ thưa Thầy/Cô, quy trình 3 chặng này vừa ngăn chặn hiện tượng **Quên thảm khốc (`Catastrophic Forgetting`)** trên backbone `Wav2Vec 2.0`, vừa khử triệt để **độ lệch biên âm (`Negative Classifier Bias`)** ở tầng phân loại cuối.",
        "Ở **Pha 1**, đầu phân loại đồ thị `AASIST` mới khởi tạo ngẫu nhiên nên đạo hàm rất lớn; đóng băng `Wav2Vec 2.0` (`LR = 1e-4` cho AASIST) giúp làm ấm đồ thị mà không phá hỏng tri thức tiếng Việt 250 giờ. Sang **Pha 2**, mở khóa toàn mạng với tốc độ học phân tầng cực nhỏ (`SSL LR = 1e-6`, `AASIST LR = 1e-5`) giúp mạng học sâu dấu vết `OmniVoice CFM`. Tuy nhiên, sau Pha 2, biên phân loại tuyến tính hơi dịch sang vùng âm để ép chặt mẫu giả CFM. Vì vậy ở **Giai đoạn 3 (`head_blend_a0.75`)**, chúng em đóng băng nguyên vẹn 100% khối `Wav2Vec 2.0`, chỉ vi chỉnh nhẹ đầu phân loại 1 epoch trên tập cân bằng `5.100` dòng rồi nội suy tuyến tính `25% Pha 2 + 75% Head-Only`.",
        "Kỹ thuật `head_blend_a0.75` giữ trọn năng lực chặn `OmniVoice CFM` (**91.52%** trên tập Test `15.980` mẫu) đồng thời kéo tỷ lệ nhận diện đúng giọng thật người nói trầm và 5 tình nguyện viên đối chứng lên **93.3% – 95.2%** (`100%` trên `SPK_0004..0007`), đưa tổng EER về mức tốt nhất **5.63%**.",
    )

    # Q9: Consensus Asymmetric Veto vs Max (8.33%) & Mean (6.24%) -> 5.63% + OMML
    _qa(
        9,
        "Tại sao thuật toán Consensus Asymmetric Veto vượt qua cả Max-Pooling (8.33% EER) lẫn Mean-Pooling (6.24% EER) để đạt 5.63% EER?",
        "Kiểm tra đóng góp thuật toán cốt lõi ở tầng suy luận đa cửa sổ trượt.",
        "Dạ thưa Thầy/Cô, `Consensus Asymmetric Veto` khắc phục đồng thời điểm mù lọt lưới giả của `Max-Pooling` và điểm mù báo nhầm người thật của `Mean-Pooling` bằng cơ chế **kiểm tra đồng thuận hai cửa sổ độc lập**.",
        "Khi cắt một đoạn thoại thành `K ≤ 5` cửa sổ: (1) Nếu dùng `Max-Pooling` đơn thuần, một mẫu giả `OmniVoice CFM` có 4 cửa sổ đầu mang điểm âm sâu (`-22`) nhưng cửa sổ cuối rơi vào nhịp nghỉ im lặng mang điểm dương nhẹ (`+7`) sẽ bị lấy giá trị cực đại `+7` và lọt lưới; (2) Ngược lại, nếu dùng `Mean-Pooling`, một người thật có 1 nhịp lấy hơi đầu câu bị điểm âm sâu (`-18`) sẽ kéo tụt trung bình cộng của cả đoạn xuống dưới `0`. Thuật toán `Consensus Asymmetric Veto` quy định: khi phát hiện ít nhất một cửa sổ nghi giả mạnh (`min < −12,0`), hệ thống chỉ bảo vệ là giọng thật nếu **cửa sổ cao thứ nhì cũng đạt `≥ +6,0`** (tức có ít nhất 2 cửa sổ độc lập cùng khẳng định giọng thật); bằng không, hệ thống loại bỏ cửa sổ cao nhất gây nhiễu và lấy trung bình cắt ngọn (`trimmed mean`) để chặn đứng mẫu giả!",
        "Trên cùng một mô hình `v0.9.4` và tập kiểm thử độc lập `15.980` mẫu, `Max-Pooling` đạt `8.33%` EER, `Mean-Pooling` đạt `6.24%` EER (`BPCER` vọt lên `8.80%`), còn **`Consensus Asymmetric Veto` đạt đỉnh cao `5.63%` EER** với tỷ lệ chặn giả **95.01%** và `BPCER` giữ ở mức thấp **6.73%**.",
    )

    eq_veto_xml = (
        omml_sub(omml_r("s"), omml_r("veto", normal=True))
        + omml_r(" = ", normal=True)
        + omml_sub(omml_r("s"), omml_delim(omml_r("K−1")))
        + omml_r("  (nếu ", normal=True)
        + omml_sub(omml_r("s"), omml_delim(omml_r("1", normal=True)))
        + omml_r(" < −12,0 và ", normal=True)
        + omml_sub(omml_r("s"), omml_delim(omml_r("K−1")))
        + omml_r(" ≥ +6,0) ;   ", normal=True)
        + omml_frac(
            omml_r("1", normal=True),
            omml_r("K − 1"),
        )
        + omml_subsup(omml_r("∑", normal=True), omml_r("i=1", normal=True), omml_r("K−1"))
        + omml_sub(omml_r("s"), omml_delim(omml_r("i")))
        + omml_r("  (nếu ngược lại khi ", normal=True)
        + omml_sub(omml_r("s"), omml_delim(omml_r("1", normal=True)))
        + omml_r(" < −12,0)", normal=True)
    )
    add_omml_equation(
        doc,
        formula_title="Quy tắc gộp điểm đa cửa sổ có kiểm tra đồng thuận Consensus Asymmetric Veto (khi K ≥ 3)",
        omml_body_xml=eq_veto_xml,
        variables=[
            ("s_(1) ≤ s_(2) ≤ … ≤ s_(K)", "Dãy điểm thô của `K` cửa sổ trượt sau khi sắp xếp tăng dần (`s_(1)` là cửa sổ thấp nhất, `s_(K−1)` là cửa sổ cao thứ nhì, `s_(K)` là cửa sổ cao nhất)."),
            ("−12,0 và +6,0", "Hai ngưỡng gác cổng bất đối xứng: `s_(1) < −12,0` báo hiệu xuất hiện phân đoạn mang dấu vết giả mạo rõ rệt; `s_(K−1) ≥ +6,0` xác nhận có tối thiểu 2 cửa sổ độc lập đồng thuận là giọng người thật. Nếu mọi cửa sổ đều `≥ −12,0`, hàm trả về `s_(K)` (`Max-Pooling`) để bảo vệ tối đa giọng thật."),
        ],
    )

    # Q10: Threshold locked at theta = 0.0 (APCER vs BPCER cost trade-off)
    _qa(
        10,
        "Tại sao hệ thống khóa cứng ngưỡng quyết định tại θ = 0.0 và bài toán đánh đổi chi phí giữa APCER với BPCER được xử lý ra sao?",
        "Kiểm tra nhận thức về quản trị rủi ro an ninh (Security Cost Trade-off) và tính liêm chính khi chọn ngưỡng vận hành.",
        "Dạ thưa Thầy/Cô, chúng em khóa cứng ngưỡng vận hành tiên nghiệm tại **`θ = 0.0`** (`s ≥ 0.0` là Giọng thật, `s < 0.0` là Giọng giả) để đảm bảo ưu tiên chặn lừa đảo mà tuyệt đối không gian lận tinh chỉnh ngưỡng trên tập Test.",
        "Trong bối cảnh phòng chống tội phạm tài chính, hậu quả của lỗi **Bỏ sót giọng giả (`APCER`)** là nạn nhân mất trắng tài sản, nghiêm trọng hơn rất nhiều so với lỗi **Báo nhầm giọng thật (`BPCER`)** — vốn chỉ yêu cầu người dùng gọi xác minh lại qua kênh khác. Điểm thô `s = z_bonafide − z_spoof` có tâm đối xứng toán học tự nhiên tại `θ = 0.0`. Thay vì dịch ngưỡng sau khi nhìn tập kiểm thử, chúng em đưa sự cân bằng về đúng tâm `0.0` ngay từ khâu hiệu chuẩn đầu phân loại `head_blend_a0.75` kết hợp `Consensus Asymmetric Veto`.",
        "Tại đúng ngưỡng cứng `θ = 0.0`, ViTrueVoice `v0.9.4` chặn đứng **95.01%** mẫu giả mạo (`APCER = 4.99%`) trong khi vẫn giữ tỷ lệ báo nhầm người thật ở mức thấp **BPCER = 6.73%** trên `15.980` mẫu Test (và chỉ **5.24% BPCER** trên `420` tệp giọng thật của 5 tình nguyện viên độc lập).",
    )

    # Q11: Platt Scaling (T=16.0) & NIST [0.1%, 99.9%] clamp + OMML
    _qa(
        11,
        "Cơ chế hiệu chuẩn Platt Scaling (T = 16.0) và kẹp biên NIST [0.1%, 99.9%] ngăn chặn hiện tượng 'độ tự tin ảo' như thế nào?",
        "Kiểm tra hiểu biết về hiệu chuẩn xác suất hậu nghiệm (Probability Calibration) và đạo đức giám định số pháp y.",
        "Dạ thưa Thầy/Cô, chúng em áp dụng phép co giãn nhiệt độ **`Platt / Temperature Scaling` với `T = 16.0`** kèm **vùng cảnh báo biên `|s| ≤ 8.0`** và **kẹp trần chuẩn pháp y `NIST [0.1%, 99.9%]`** để loại bỏ hoàn toàn các con số phần trăm tự tin giả tạo.",
        "Do mô hình huấn luyện với `AM-Softmax (s = 30.0)`, điểm hiệu số logit `s` trải rộng trên miền `[-50, +50]`. Nếu đưa thẳng vào hàm `Sigmoid` tiêu chuẩn (`T = 1.0`), một mẫu mập mờ ngay sát biên như `s = +5.0` đã bị vọt lên `99.3%` độ tin cậy, gây ngộ nhận nguy hiểm cho người dùng! Chia cho nhiệt độ `T = 16.0` (`k = 0.0625`) kèm khấu trừ phương sai liên cửa sổ (`khi độ lệch chuẩn giữa các cửa sổ > 6.0`) giúp các điểm vùng biên `|s| ≤ 8.0` chỉ hiển thị xác suất thận trọng `50% – 62%` và gắn nhãn `BORDERLINE`. Đồng thời, chuẩn giám định pháp y của `NIST` khẳng định không một phép đo sinh trắc học nào tuyệt đối `100%`, nên xác suất hiển thị luôn được kẹp trong `[0.1%, 99.9%]`.",
        "Cơ chế này được đồng bộ nhất quán 100% trên cả API FastAPI, giao diện Web Forensics và Telegram Bot của phiên bản `v0.9.4` thông qua module dùng chung `src/app/decision.py`.",
    )

    eq_platt_xml = (
        omml_sub(omml_r("P"), omml_r("calib", normal=True))
        + omml_delim(omml_r("y = 1 | s", normal=True))
        + omml_r(" = ", normal=True)
        + omml_r("clip", normal=True)
        + omml_delim(
            omml_frac(
                omml_r("1", normal=True),
                omml_r("1 + ", normal=True)
                + omml_sup(
                    omml_r("e"),
                    omml_r("−", normal=True)
                    + omml_frac(omml_r("s − θ"), omml_r("T")),
                ),
            )
            + omml_r(" ,  0,001 ,  0,999", normal=True)
        )
    )
    add_omml_equation(
        doc,
        formula_title="Hàm hiệu chuẩn xác suất hậu nghiệm Platt / Temperature Scaling và kẹp biên pháp y NIST",
        omml_body_xml=eq_platt_xml,
        variables=[
            ("s", "Điểm thô sau khi gộp đa cửa sổ trượt (`Pooled Raw Score`), mang dấu dương cho Giọng thật và dấu âm cho Giọng giả."),
            ("θ = 0,0", "Ngưỡng quyết định cố định của hệ thống; tại `s = θ`, xác suất trả về đúng bằng `0,50 (50,0%)`."),
            ("T = 16,0", "Hệ số nhiệt độ hiệu chuẩn khớp với thang đo `AM-Softmax [-50, +50]`, chống bão hòa sớm ở vùng cận biên."),
            ("[0,001 ; 0,999]", "Khoảng kẹp xác suất tương ứng `[0,1% ; 99,9%]` tuân thủ nguyên tắc trung thực giám định số của `NIST`."),
        ],
    )

    # Q12: Hypothesis H2 Unseen TTS (VieNeu 12.05% Dev EER & 92.53% 5-SPK block) & why Kokoro excluded
    _qa(
        12,
        "Giả thuyết H2 (Tổng quát hóa sang công cụ Unseen TTS) được chứng minh ra sao trên VieNeu-TTS v3 Turbo và vì sao Kokoro-TTS bị loại bỏ?",
        "Kiểm tra tính chặt chẽ khoa học trong việc chọn công cụ kiểm định ngoại lai Zero-Shot Voice Cloning.",
        "Dạ thưa Thầy/Cô, Giả thuyết `H2` (yêu cầu `EER ≤ 15.0%` trước công cụ nhân bản giọng nói chưa từng thấy) đã **ĐẠT THÀNH CÔNG** trên `VieNeu-TTS v3 Turbo` với **12.05% EER**, và `Kokoro-TTS` bị loại khỏi bộ nghiệm thu chính thức vì không phải công cụ nhân bản giọng nói Zero-Shot thực thụ.",
        "Mối đe dọa thực tế của tội phạm lừa đảo mạo danh là thu 3–5 giây giọng thật của nạn nhân rồi nhại lại đúng âm sắc người đó (`Zero-Shot Voice Cloning`). Qua kiểm toán kỹ thuật, `Kokoro-TTS` chỉ là bộ đọc văn bản đa giọng cố định có sẵn (`Preset Multi-speaker TTS`), không nhận tệp âm thanh mẫu để nhại giọng nạn nhân nên không phản ánh đúng kịch bản tấn công mạo danh. Ngược lại, ở phiên bản `v0.9.4`, mô hình chỉ học trên hai công cụ dòng chảy `F5-TTS` và `OmniVoice CFM`, còn công cụ Zero-Shot `VieNeu-TTS v3 Turbo` (kiến trúc `Acoustic LM + NeuCodec RVQ` hoàn toàn khác họ) được cô lập 100% làm Unseen TTS.",
        "Khi đối mặt lần đầu với `VieNeu-TTS v3 Turbo`, mô hình `v0.9.4` đạt **12.05% EER** trên tập benchmark `955` mẫu Dev (vượt xa KPI `≤ 15.0%`) và chặn đứng **92.53% (347/375 tệp)** trên bộ nghiệm thu 5 tình nguyện viên qua cả 5 biến thể kênh nén.",
    )

    # Q13: 5 Acceptance Volunteers 100% isolated (neutral mention of 6th volunteer SPK_0001)
    _qa(
        13,
        "Năm (05) tình nguyện viên nghiệm thu (SPK_0003..0007) được cô lập như thế nào và kết quả trên 1.545 tệp kiểm định đạt mức nào?",
        "Kiểm tra nguyên tắc bất khả xâm phạm của tập kiểm định độc lập thu thập thực tế ngoài đời.",
        "Dạ thưa Thầy/Cô, **5 tình nguyện viên (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`)** được khóa cứng làm **Bộ Nghiệm Thu Độc Lập Chính Thức** với mức cô lập tuyệt đối **100%** khỏi toàn bộ quá trình huấn luyện, thẩm định Dev, chọn ngưỡng và hiệu chuẩn.",
        "Trong tổng số 6 tình nguyện viên thu thập có phiếu đồng thuận, ngay từ khâu quy hoạch dữ liệu, 5 tình nguyện viên `SPK_0003..0007` (84 tệp gốc × 5 biến thể codec = `420` tệp giọng thật, kèm `375` tệp giả cho mỗi công cụ `F5-TTS`, `OmniVoice CFM`, `VieNeu-TTS`, tổng cộng **`1.545` tệp**) được niêm phong riêng để đo lường khả năng tổng quát hóa thực tế; còn tình nguyện viên thứ 6 dư ra ngoài bộ 5 người nghiệm thu (`SPK_0001`, 175 mẫu) được phân bổ vào tập Train chính thức `54.400` dòng cùng với `VIVOS` và `Common Voice`.",
        "Trên toàn bộ `1.545` tệp nghiệm thu độc lập của 5 tình nguyện viên qua 5 codecs, `v0.9.4` đạt tỷ lệ nhận diện đúng giọng thật **94.76% (398/420)**, chặn đứng **100.0% (375/375)** mẫu giả `F5-TTS`, chặn **83.47% (313/375)** mẫu giả `OmniVoice CFM` và chặn **92.53% (347/375)** mẫu giả chưa từng thấy `VieNeu-TTS`.",
    )

    # Q14: Deep-voice pitch robustness (-6st augmentation & m=0.20)
    _qa(
        14,
        "Hệ thống giải quyết bài toán bền vững trước giọng nam trầm và tấn công hạ cao độ âm học (-6 semitones) như thế nào?",
        "Kiểm tra cách nhóm khắc phục lỗ hổng dịch tần số cơ bản (Pitch-shift) bằng thuật toán thay vì gán nhãn thủ công.",
        "Dạ thưa Thầy/Cô, chúng em giải quyết đồng thời bằng **tăng cường dữ liệu dịch cao độ hai chiều (bao gồm hạ sâu `-6 semitones` cho cả giọng thật lẫn giọng giả)** kết hợp **điều chỉnh biên góc `AM-Softmax` về `m = 0.20`**.",
        "Trong nghiên cứu bóc tách trước đó, chúng em phát hiện nếu kẻ tấn công dùng phase-vocoder hạ cao độ giọng giả xuống `-6 bán cung (-6st)`, các hài âm co cụm lại ở dải tần thấp dễ đánh lừa mạng nơ-ron chưa từng học biến thể trầm; ngược lại, nếu đặt biên phạt góc `AM-Softmax` quá gắt (`m = 0.35`), những người đàn ông có giọng trầm tự nhiên (`F0 < 100 Hz`) lại dễ bị đẩy sang miền điểm âm. Việc tiền sinh các mẫu tăng cường dịch pitch hai chiều kết hợp nới biên `m = 0.20` giúp mặt phân cách bao trọn vùng giọng trầm tự nhiên nhưng vẫn nhận diện được vết méo pha do kéo giãn cao độ nhân tạo.",
        "Nhờ giải pháp thuần thuật toán này, ở phiên bản `v0.9.4`, nhóm người nói giọng trầm đạt tỷ lệ nhận diện đúng **93.3% (14/15)** ở cả 3 chế độ pooling mà không làm suy giảm độ nhạy chặn giả trên tập `15.980` mẫu.",
    )

    # Q15: How NFR1 <= 3.0s latency is achieved (0.705s - 1.101s)
    _qa(
        15,
        "Làm thế nào hệ thống vừa cắt đa cửa sổ trượt vừa giải mã đa định dạng mà vẫn giữ độ trễ 0.705s – 1.101s (≤ 3.0s NFR1)?",
        "Kiểm tra kỹ năng kỹ thuật hệ thống (Systems Engineering) khi đưa mô hình học sâu lớn lên môi trường thời gian thực.",
        "Dạ thưa Thầy/Cô, tốc độ **0,705 giây – 1,101 giây** đạt được nhờ triệt tiêu hoàn toàn hai nút cổ chai lớn nhất là **đọc/ghi ổ cứng** và **vòng lặp suy luận tuần tự trên GPU**.",
        "Thứ nhất, mô hình được nạp sẵn theo mẫu `Singleton` và làm ấm hạt nhân `CUDA` bằng `Dummy Tensor (1, 64000)` ngay lúc khởi động container. Thứ hai, luồng âm thanh được giải mã trực tiếp trên bộ nhớ `io.BytesIO` qua đường ống `FFmpeg Pipe` không chạm đĩa cứng. Thứ ba, cả 5 cửa sổ trượt được xếp chồng thành một khối tensor duy nhất `(5, 64000)` để chạy gọn trong **1 lượt truyền tiến duy nhất** dưới chế độ `torch.inference_mode()`.",
        "Kết quả kiểm định thực tế: lượt chạy mô hình trên GPU `RTX 3050 4GB` chỉ tốn trung vị **66,3 ms** (`P90 = 68,2 ms`); tổng thời gian toàn trình đạt trung vị **1,101 giây** trên bộ 30 ca benchmark chuẩn và **0,705 giây** trên 140 lượt vận hành thực tế — nhanh gấp **~3 đến ~45 lần** yêu cầu `NFR1 ≤ 3,0 giây`.",
    )

    # Q16: Law 91/2025/QH15 & Decree 356/2025/ND-CP compliance
    _qa(
        16,
        "Hệ thống tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP bằng những cơ chế kỹ thuật cụ thể nào?",
        "Kiểm tra tính tuân thủ pháp luật Việt Nam về dữ liệu sinh trắc học nhạy cảm.",
        "Dạ thưa Thầy/Cô, giọng nói là dữ liệu sinh trắc học nhạy cảm nên toàn bộ kiến trúc API và Bot của chúng em thực thi nghiêm ngặt nguyên tắc **Không lưu vết (`Zero-Persistence`)** kết hợp **Ẩn danh hóa một chiều `SHA-256`**.",
        "Cụ thể ở tầng mã nguồn: (1) Mọi luồng âm thanh tải lên Web API được đọc vào bộ đệm RAM `io.BytesIO`, nhận diện định dạng qua `Magic Bytes` rồi giải phóng khỏi bộ nhớ ngay khi trả kết quả (đối với Telegram Bot hoặc luồng clone tạm, khối `try...finally` cưỡng bức xóa hủy tệp tạm tức thì); (2) Tệp nhật ký vận hành `benchmarks/latency_log.json` tuyệt đối không lưu tên tệp, địa chỉ IP, số điện thoại hay ID người dùng, mà chỉ lưu mã băm mật mã một chiều `SHA-256` của nội dung byte kèm số đo độ trễ phục vụ kiểm toán kỹ thuật.",
        "Nhờ đó, ngay cả trong kịch bản máy chủ ứng dụng bị xâm nhập trái phép, kẻ tấn công thu được **0 byte giọng nói thô** và không thể khôi phục danh tính bất kỳ người dùng nào, đáp ứng trọn vẹn Luật `91/2025/QH15` và Nghị định `356/2025/NĐ-CP`.",
    )

    # Q17: AWS Academy Package A (3 courses) + 0 VND local operating cost
    _qa(
        17,
        "Nhóm đã vận dụng 3 khóa học AWS Academy Gói A vào dự án như thế nào trong khi vẫn duy trì chi phí vận hành thực tế 0 VNĐ?",
        "Kiểm tra khả năng liên kết kiến thức học phần đám mây AWS với bài toán tối ưu chi phí thực tế của sinh viên.",
        "Dạ thưa Thầy/Cô, hệ thống trực tiếp của đồ án hiện vận hành **100% cục bộ trên cụm Docker Compose với chi phí thực tế 0 VNĐ**, đồng thời áp dụng trọn vẹn nguyên lý kiến trúc và bảo mật từ **3 khóa học AWS Academy Gói A** kèm bộ đặc tả sẵn sàng lên mây (`Cloud-Ready`) tại thư mục `deploy/aws/`.",
        "Cụ thể cách vận dụng từng khóa học trong Gói A: (1) Từ khóa **`AWS Academy Cloud Foundations`**, chúng em chuẩn hóa kiến trúc vi dịch vụ đóng gói 2 container độc lập (`vitruevoice-api` và `vitruevoice-bot`) và lập bảng dự toán tổng chi phí sở hữu (`TCO`); (2) Từ khóa **`AWS Academy Cloud Security Foundations`**, chúng em thực thi nguyên tắc đặc quyền tối thiểu (`non-root appuser`, gắn kết thư mục trọng số `out/v0.9.4` ở chế độ chỉ đọc `:ro`, tách biến bí mật qua `.env`) và viết chính sách `IAM Least Privilege` (`deploy/aws/iam_policy.json`) cùng quy tắc `S3 Lifecycle` tự hủy dữ liệu tạm sau 24 giờ (`s3_lifecycle_policy.json`); (3) Từ khóa **`AWS Academy Cloud Architecting`**, chúng em thiết kế cơ chế tự kiểm tra sức khỏe `HEALTHCHECK /health` mỗi 30 giây, tự khởi động lại khi sự cố và kịch bản triển khai `EC2 Spot / Auto-Scaling` (`scripts/aws_deploy_ec2.sh`).",
        "Cách tiếp cận kép này giúp đồ án chạy demo thực nghiệm bền bỉ **24/7 với chi phí 0 VNĐ** trên phần cứng cục bộ, nhưng khi doanh nghiệp cần mở rộng lên đám mây AWS Singapore thì đã có sẵn toàn bộ cấu hình chuẩn mực với chi phí lý thuyết ước tính chỉ khoảng **~73 VNĐ / lượt quét** ở quy mô thử nghiệm.",
    )

    # Q18: Why WebRTC browser mic disables noiseSuppression / autoGainControl
    _qa(
        18,
        "Tại sao khi thu âm trực tiếp từ micro trình duyệt (WebRTC), giao diện Web của nhóm bắt buộc tắt noiseSuppression và autoGainControl?",
        "Kiểm tra kinh nghiệm xử lý lỗi thực tế khi đưa mô hình phòng thí nghiệm ra giao diện thu âm người dùng thật.",
        "Dạ thưa Thầy/Cô, chúng em bắt buộc đặt `noiseSuppression: false`, `echoCancellation: false` và `autoGainControl: false` trong cấu hình `WebRTC` vì các bộ lọc khử ồn tự động của trình duyệt **vô tình xóa sạch nền âm học vật lý của phòng thu, tạo ra dấu vết giống hệt bộ tổng hợp giọng giả**.",
        "Trong môi trường tự nhiên, giữa hai từ người thật nói luôn có tiếng nền phòng cực nhỏ liên tục (`Room Tone`). Khi trình duyệt bật `AI Noise Suppression`, nó cắt phăng các khoảng nghỉ này về chuỗi số `0.0000` phẳng tuyệt đối và bóp méo các phụ âm xát tần số cao. Khối `Wav2Vec 2.0 + AASIST` sẽ nhận diện vùng chết số học phẳng lì đó như sản phẩm của một `Neural Vocoder` nhân tạo, gây báo động giả cho người thật! Bên cạnh việc tắt lọc trình duyệt, hàm `_condition_audio_for_inference` còn cắt khoảng lặng thừa (`top_db = 25`), chuẩn hóa đỉnh `0.95` và chỉ cho phép rải nhiễu nền vi mô `Comfort Dither` trên luồng micro trực tiếp (tuyệt đối đặt `apply_dither = False` cho tệp tải lên để không làm mờ vết giả CFM).",
        "Giải pháp phối hợp tiền xử lý `WebRTC` này triệt tiêu hoàn toàn hiện tượng báo động giả khi thử nghiệm nói trực tiếp qua micro trước Hội đồng mà vẫn bảo toàn nguyên vẹn độ nhạy bắt giọng giả tải lên.",
    )

    # Q19: Mode 2 Live OmniVoice CFM Cloning Audit
    _qa(
        19,
        "Chế độ 2 (Live OmniVoice CFM Cloning & Forensic Audit) trên giao diện hoạt động ra sao để kiểm chứng trực tiếp trước Hội đồng?",
        "Kiểm tra khả năng trình diễn khép kín (Red-Team Live Attack & Blue-Team Defense) ngay trên hệ thống thực tế.",
        "Dạ thưa Thầy/Cô, **Chế độ 2** là phòng thí nghiệm đối kháng khép kín cho phép bất kỳ thành viên Hội đồng nào **thu âm 4–6 giây giọng thật của chính mình, để hệ thống tự nhân bản giọng giả bằng `OmniVoice CFM` tại chỗ, rồi lập tức đưa mẫu vừa nhân bản vào bộ thẩm định `v0.9.4` để vạch trần**.",
        "Quy trình chạy hoàn toàn tự động qua 3 bước: (1) Tiền xử lý bản thu mẫu của Giảng viên (chuẩn hóa `16 kHz`, cắt khoảng lặng đầu/cuối tránh lỗi sụp đổ thời lượng `Duration Collapse`, chuẩn hóa biên độ `0.95`); (2) Động cơ `LiveVoiceStudioCloner` giải phương trình vi phân dòng chảy `OmniVoice CFM` để đọc một câu kịch bản chuyển tiền lừa đảo bằng đúng âm sắc của Giảng viên; (3) Luồng âm thanh giả vừa sinh (với cờ `apply_dither = False` để giữ nguyên dấu vết vocoder) được chuyển thẳng sang `SSL-AASIST v0.9.4` phân tích đa cửa sổ và xuất biểu đồ điểm số từng cửa sổ trượt.",
        "Chế độ này chứng minh trực quan trước mắt Hội đồng rằng dù giọng nhân bản `OmniVoice CFM` nghe bằng tai người cực kỳ giống người thật, mô hình `v0.9.4` vẫn bóc tách chính xác vi nhiễu tích phân số học và chặn đứng với điểm thô âm sâu.",
    )

    # Q20: Enrollment IQR Guardrail (|offset| > 4 x IQR) + OMML
    _qa(
        20,
        "Hàng rào an toàn Enrollment IQR Guardrail (|offset| > 4 × IQR) bảo vệ hệ thống trước rủi ro gì?",
        "Kiểm tra tư duy thiết kế an toàn phòng thủ chiều sâu (Defense-in-Depth) chống lạm dụng cơ chế hiệu chuẩn cá nhân.",
        "Dạ thưa Thầy/Cô, hàng rào **`|offset| > 4 × IQR`** trong hàm `calibrate_by_enrollment` đóng vai trò cầu chì an toàn: **tự động từ chối dịch ngưỡng hiệu chuẩn nếu các mẫu đăng ký ban đầu bị nhiễu nặng, lệch chuẩn cực đoan hoặc bị kẻ tấn công cố tình đầu độc (`Enrollment Poisoning`)**.",
        "Khi một người dùng doanh nghiệp đăng ký tối thiểu `3 mẫu giọng thật` để hiệu chỉnh độ lệch cá nhân `offset = median(s_enroll) − median(s_dev)`, nếu kẻ gian lén nộp 3 mẫu giọng giả có điểm âm rất sâu (ví dụ `-30`) làm mẫu đăng ký mà hệ thống ngây thơ trừ đi `offset` đó, mọi mẫu giọng giả tiếp theo sẽ được cộng bù hàng chục điểm để biến thành giọng thật! Bằng cách đo khoảng tứ phân vị bền vững `IQR = Q75 − Q25` trên tập Dev và khóa trần `4 × IQR`, bất kỳ độ lệch bất thường nào vượt ngưỡng đều bị từ chối hiệu chuẩn ngay lập tức, giữ nguyên điểm thô gốc để chuyển sang quy trình kiểm tra thủ công.",
        "Toàn bộ các ca biên của hàng rào `IQR Guardrail` (dưới 3 mẫu, `IQR ≤ 0`, độ lệch vượt `4 × IQR`) đều được kiểm chứng chặt chẽ bằng kịch bản kiểm thử đơn vị tự động trong `tests/`.",
    )

    eq_iqr_xml = (
        omml_delim(omml_sub(omml_r("Δ"), omml_r("enroll", normal=True)), beg="|", end="|")
        + omml_r(" = ", normal=True)
        + omml_delim(
            omml_r("median", normal=True)
            + omml_delim(omml_sub(omml_r("s"), omml_r("enroll", normal=True)))
            + omml_r(" − ", normal=True)
            + omml_r("median", normal=True)
            + omml_delim(omml_sub(omml_r("s"), omml_r("dev", normal=True))),
            beg="|",
            end="|",
        )
        + omml_r(" > 4 · ", normal=True)
        + omml_sub(omml_r("IQR"), omml_r("dev", normal=True))
        + omml_r("  ⇒  Từ chối hiệu chuẩn", normal=True)
    )
    add_omml_equation(
        doc,
        formula_title="Điều kiện kích hoạt cầu chì an toàn Enrollment IQR Guardrail",
        omml_body_xml=eq_iqr_xml,
        variables=[
            ("s_enroll", "Tập điểm thô của tối thiểu 3 mẫu giọng đăng ký tham chiếu từ người nói cần hiệu chuẩn."),
            ("median(s_dev), IQR_dev", "Trung vị và khoảng tứ phân vị (`Q75 − Q25`) của phân phối giọng thật chuẩn trên tập thẩm định `Dev`."),
            ("4 · IQR_dev", "Ngưỡng biên an toàn tối đa cho phép dịch chuyển; vượt quá ngưỡng này hệ thống giữ nguyên `raw_score` gốc để ngăn chặn đầu độc mẫu đăng ký."),
        ],
    )

    # Q21: TDD & CI verification (392/392 unit tests on GitHub Actions Ubuntu)
    _qa(
        21,
        "Quy trình phát triển hướng kiểm thử (TDD) và đường ống GitHub Actions CI xác minh độ tin cậy mã nguồn của dự án như thế nào?",
        "Kiểm tra kỹ năng công nghệ phần mềm hiện đại (Software Engineering & MLOps Quality Assurance).",
        "Dạ thưa Thầy/Cô, mọi mô-đun cốt lõi của ViTrueVoice đều được phát triển theo quy trình **Viết kiểm thử trước – Viết mã thực thi sau (`TDD`)** và được bảo vệ tự động bởi **`392/392 bài kiểm thử đơn vị (unit tests)`** chạy xanh 100% trên máy chủ sạch `GitHub Actions Ubuntu`.",
        "Trong các dự án AI nghiên cứu, lỗi phổ biến nhất là sửa một hàm tiền xử lý hoặc đổi đường dẫn checkpoint làm hỏng ngầm kết quả đánh giá cũ. Bộ `392` bài kiểm thử của chúng em khóa chặt tất cả các bất biến sống còn: nối lặp `Repeat Padding 64.000 mẫu`, trọng số mất mát động, ranh giới `0%` rò rỉ manifest, toán tử `Consensus Asymmetric Veto`, hiệu chuẩn `Platt Scaling`, ẩn danh `SHA-256` trên API/Bot và cô lập giả lập (`mock`) các thư viện ngoài nằm trong `.gitignore` để không bao giờ gãy trên máy chủ đám mây Ubuntu sạch.",
        "Trước mỗi lần cập nhật phiên bản `v0.9.4`, toàn bộ **`392/392 bài kiểm thử đơn vị (unit tests)`** đều đạt trạng thái **100% PASS** cả ở môi trường cục bộ lẫn trên đường ống `GitHub Actions CI`.",
    )

    # Q22: Remaining limitations & future direction (WavLM / multi-scale SSL)
    _qa(
        22,
        "Hạn chế còn tồn đọng lớn nhất của phiên bản v0.9.4 là gì và hướng nghiên cứu tiếp theo để khắc phục triệt để là gì?",
        "Kiểm tra sự trung thực khoa học (Scientific Humility) và tầm nhìn nghiên cứu mở rộng sau đồ án.",
        "Dạ thưa Thầy/Cô, hạn chế còn tồn đọng rõ nhất của `v0.9.4` là vẫn còn một tỷ lệ nhỏ mẫu giả **`OmniVoice CFM` chất lượng phòng thu siêu sạch trùng khớp âm sắc bị lọt lưới (`7.95%` trên tập Test nội bộ và `16.53%` trên bộ 5 tình nguyện viên độc lập)**, cùng giới hạn quy mô mẫu người nói thu thập thực tế.",
        "Nguyên nhân vật lý là `wav2vec2-base-vietnamese-250h` hoạt động ở tần số lấy mẫu `16 kHz` (tần số Nyquist tối đa `8 kHz`) và được tiền huấn luyện chủ yếu cho bài toán nhận dạng chữ viết (`ASR`), nên ở những câu thoại ngắn, rõ nét, không nhiễu nền mà bộ giải phương trình vi phân `OmniVoice CFM` tái tạo cực mượt dưới `8 kHz`, khoảng cách biểu diễn với giọng thật trở nên rất hẹp.",
        "Hướng phát triển tiếp theo của chúng em gồm 3 mũi nhọn: (1) Nâng cấp mặt trước lên kiến trúc **`WavLM` hoặc `Multi-scale SSL`** kết hợp nhánh phổ pha băng rộng `24 kHz` để bắt vi nhiễu tích phân bậc cao trên `8 kHz`; (2) Mở rộng tăng cường dữ liệu biến đổi pha – cao độ hai chiều cho đa công cụ Flow Matching; và (3) Phối hợp kiểm thử thực địa `Red-Team Pilot` diện rộng cùng CLB An toàn thông tin HUTECH.",
    )

    add_term_glossary(
        doc,
        terms=[
            ("CM vs ASV", "Countermeasure vs Automatic Speaker Verification", "`CM` phân biệt giọng người sinh học với giọng tổng hợp AI độc lập danh tính; `ASV` xác minh xem giọng nói có khớp với người dùng đã đăng ký trước hay không."),
            ("APCER & BPCER", "Attack / Bona Fide Presentation Classification Error Rate", "Theo chuẩn `ISO/IEC 30107-3`, `APCER` là tỷ lệ lọt lưới mẫu tấn công giả mạo; `BPCER` là tỷ lệ từ chối nhầm người dùng thật."),
            ("EER & minDCF", "Equal Error Rate & Minimum Detection Cost Function", "`EER` là tỷ lệ lỗi tại điểm `APCER = BPCER`; `minDCF` là hàm chi phí phát hiện cực tiểu có tính đến mức độ thiệt hại bất đối xứng của việc bỏ sót lừa đảo."),
            ("Shortcut Learning", "Spurious Correlation Learning", "Hiện tượng mạng học sâu gian lận bằng cách nhớ khoảng lặng đầu câu, tên người nói hoặc nội dung văn bản thay vì học bản chất giả mạo âm học."),
            ("Platt Scaling", "Logistic / Temperature Probability Calibration", "Kỹ thuật biến đổi điểm thô logit về phân phối xác suất hậu nghiệm trung thực để ngăn chặn hiện tượng báo độ tự tin ảo 99,9% ở vùng mập mờ."),
            ("IQR Guardrail", "Interquartile Range Safety Bound", "Hàng rào thống kê dùng khoảng tứ phân vị `Q75 − Q25` để chặn đứng các phép hiệu chuẩn bất thường vượt quá `4 × IQR`."),
            ("Zero-Persistence", "In-Memory Ephemeral Processing", "Kiến trúc xử lý dữ liệu sinh trắc học thuần trên bộ nhớ RAM và hủy tức thì, không lưu lại tệp giọng nói trên ổ cứng dài hạn."),
            ("TCO", "Total Cost of Ownership", "Tổng chi phí sở hữu và vận hành hạ tầng (đạt `0 VNĐ` khi chạy cục bộ trên Docker Compose và khoảng `~73 VNĐ/lượt quét` theo dự toán đám mây AWS)."),
            ("TDD & CI", "Test-Driven Development & Continuous Integration", "Phương pháp viết bài kiểm thử tự động trước khi viết mã nguồn và tự động chạy kiểm tra toàn bộ `392/392` bài test mỗi khi đẩy mã lên kho lưu trữ."),
        ],
    )

    # =========================================================================
    # CHƯƠNG 12: HỆ THỐNG HÓA TỪ KHÓA KHOA HỌC (7 TRỤC TAXONOMY) & ĐỌC BÀI BÁO
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 12",
        "Hệ Thống Hóa Từ Khóa Khoa Học (7 Trục Taxonomy) & Cẩm Nang Đọc Bài Báo Quốc Tế",
    )

    add_foundation_primer(
        doc,
        process_name="Phương pháp đọc bài báo quốc tế 3 lượt (3-Pass Reading) & Truy vấn học thuật Boolean",
        why_needed=(
            "Lĩnh vực phát hiện giọng giả (Audio Deepfake Detection) thay đổi từng tháng với hàng trăm công trình mới trên "
            "Interspeech, ICASSP và NeurIPS. Nếu sinh viên tìm kiếm bằng câu tiếng Việt thông thường hoặc đọc tuần tự từng chữ "
            "từ trang đầu đến trang cuối một bài báo nặng công thức toán, sinh viên sẽ nhanh chóng bị ngợp và bỏ cuộc."
        ),
        real_analogy=(
            "Đọc bài báo quốc tế giống như khảo sát địa hình bằng bản đồ vệ tinh: Lượt 1 bay lướt trên cao để biết thành phố có mấy quận chính; "
            "Lượt 2 phóng xuống xem các trục đường lớn và biển chỉ dẫn (sơ đồ kiến trúc, bảng kết quả); chỉ khi xác định đúng tòa nhà cần tìm "
            "thì Lượt 3 mới bước vào soi từng viên gạch (chứng minh đạo hàm và tham số huấn luyện)."
        ),
        core_points=[
            "**Cấu trúc chuẩn quốc tế `IMRAD`** (*Introduction – Methods – Results – Analysis & Discussion*): Mọi bài báo đỉnh cao đều đặt câu hỏi nghiên cứu ở *Introduction*, mô tả kiến trúc và hàm mất mát ở *Methods*, chứng minh bằng bảng đối chứng `EER / minDCF` ở *Results*, và mổ xẻ giới hạn ở *Discussion*.",
            "**Truy vấn học thuật bằng toán tử Logic `Boolean` (`AND`, `OR`, dấu ngoặc kép `\"...\"`)**: Trên `Google Scholar`, `IEEE Xplore` hay `ISCA Interspeech Archive`, luôn khóa cụm thuật ngữ chính xác trong dấu ngoặc kép, dùng `OR` để gom các từ đồng nghĩa và dùng `AND` để giao cắt đúng bài toán mục tiêu.",
            "**Quy trình đọc bài báo nặng toán học trong 3 lượt (`3-Pass Method`)**: *Lượt 1 (5–10 phút)* đọc Tiêu đề, Tóm tắt (`Abstract`), Kết luận và nhìn lướt hình vẽ kiến trúc; *Lượt 2 (30 phút)* đọc kỹ các bảng số liệu đối chứng (`Ablation Tables`) và hiểu ý nghĩa đầu vào/đầu ra của từng phương trình mà chưa cần tự chứng minh lại; *Lượt 3 (60–90 phút)* tự viết lại công thức cốt lõi ra giấy, kiểm tra chiều tensor và đối chiếu với mã nguồn thực thi.",
        ],
    )

    add_heading_section(
        doc,
        "12.1 Bảng Phân Loại Hệ Thống Từ Khóa Nghiên Cứu Theo 7 Trục Công Nghệ (7-Axis Taxonomy)",
    )
    add_styled_paragraph(
        doc,
        "Bảng 12.1 hệ thống hóa toàn bộ không gian thuật ngữ quốc tế gắn liền với kiến trúc ViTrueVoice `v0.9.4` thành **7 trục chuyên môn**, "
        "giúp sinh viên dùng làm bản đồ tra cứu nhanh khi viết khóa luận hoặc mở rộng nghiên cứu lên bậc sau đại học:",
    )

    add_styled_table(
        doc,
        headers=[
            "Trục Phân Loại Khoa Học",
            "Các Từ Khóa Quốc Tế Cốt Lõi (English Research Keywords)",
            "Ánh Xạ Trực Tiếp Trong Hệ Thống ViTrueVoice v0.9.4",
        ],
        rows=[
            (
                "Trục 1: Tạo Sinh Dòng Chảy Liên Tục (Continuous Flow Matching)",
                "`Continuous Flow Matching (CFM)`, `Optimal Transport ODE`, `Vector Field Estimation`, `Midpoint / Euler Solver`, `Diffusion Transformer (DiT)`, `Zero-Shot Voice Cloning`, `OmniVoice`, `F5-TTS`",
                "Hai công cụ Seen TTS chủ lực (`F5-TTS` 6.170 mẫu & `OmniVoice CFM` 6.445 mẫu đối xứng 1:1) dùng huấn luyện và kiểm định chống lọt lưới dòng liên tục.",
            ),
            (
                "Trục 2: Mã Hóa Âm Thanh Thần Kinh Rời Rạc (Discrete Neural Audio Codecs)",
                "`Discrete Neural Audio Codec`, `Residual Vector Quantization (RVQ)`, `EnCodec`, `SpeechTokenizer`, `NeuCodec`, `Acoustic Language Model`, `Quantization Micro-Artifacts`, `VieNeu-TTS`",
                "Công cụ Unseen TTS độc lập `VieNeu-TTS v3 Turbo` (955 mẫu Dev & 375 mẫu 5-SPK) phục vụ kiểm định Giả thuyết H2 (`12.05%` EER, `92.53%` chặn).",
            ),
            (
                "Trục 3: Mặt Trước Tự Giám Sát & Đồ Thị Chú Ý (SSL + Graph Backbones)",
                "`Self-Supervised Learning (SSL)`, `Wav2Vec 2.0`, `WavLM`, `Tonal Speech Representation`, `AASIST`, `Heterogeneous Stacking Graph Attention Layer (HS-GAL)`, `Master Node Readout`",
                "Kiến trúc `wav2vec2-base-vietnamese-250h` ghép nối `Compact AASIST` trích xuất đồng thời bất thường thời gian và hài âm thanh điệu tiếng Việt.",
            ),
            (
                "Trục 4: Hiệu Chuẩn Không Gian Trọng Số & Huấn Luyện (Weight-Space Calibration)",
                "`Two-Phase Fine-Tuning`, `Differential Learning Rate`, `Weight-Space Ensembles (WiSE-FT)`, `Linear Head-Blending`, `AM-Softmax`, `Dynamic Inverse-Frequency Weighted CE`, `RawBoost`",
                "Huấn luyện 2 pha (`am_m = 0.20`) kết hợp Giai đoạn 3 `head_blend_a0.75` (`0.25 · Run2_P2 + 0.75 · HeadOnly`) khử lệch biên âm, giữ nguyên 100% SSL.",
            ),
            (
                "Trục 5: Suy Luận Đa Cửa Sổ Đồng Thuận (Multi-Window Consensus Pooling)",
                "`Sliding-Window Batched Inference`, `Repeat Padding Continuity`, `Dense Overlap Slicing`, `Consensus Asymmetric Veto`, `Trimmed Mean Outlier Filtering`, `Order-Statistic Pooling`",
                "Gom lô `(5, 64000)` chạy trong 1 forward pass (`66,3 ms`) kèm bộ lọc `Consensus Asymmetric Veto` hạ EER từ `8.33%` (Max) xuống **5.63%**.",
            ),
            (
                "Trục 6: Hiệu Chuẩn Sinh Trắc & Pháp Y Số (Biometric Calibration & PAD)",
                "`ISO/IEC 30107-3 PAD`, `APCER & BPCER`, `Equal Error Rate (EER)`, `minDCF`, `DET Curve`, `Platt Scaling`, `Temperature Scaling`, `NIST Forensic Bounds`, `IQR Enrollment Guardrail`",
                "Khóa ngưỡng `θ = 0.0`, hiệu chuẩn `Platt Scaling (T = 16.0)`, vùng biên `|s| ≤ 8.0`, kẹp `[0.1%, 99.9%]` và cầu chì đăng ký `|offset| > 4 × IQR`.",
            ),
            (
                "Trục 7: MLOps Bảo Mật Quyền Riêng Tư (Privacy-Preserving MLOps)",
                "`Zero-Persistence In-Memory Stream`, `Magic-Byte Sniffing`, `FFmpeg Pipe Decoding`, `SHA-256 Audit Logging`, `Non-Root Docker Container`, `IAM Least Privilege`, `S3 Lifecycle`",
                "Vận hành Docker Compose cục bộ `0 VNĐ` tuân thủ Luật `91/2025/QH15`, áp dụng 3 khóa AWS Academy Gói A và duy trì `392/392` unit tests CI xanh.",
            ),
        ],
        col_widths=[1.45, 2.55, 2.7],
    )

    add_heading_section(
        doc,
        "12.2 Lộ Trình Đọc Các Bài Báo Nền Tảng Kinh Điển (Curated Reading Roadmap) & Cú Pháp Tìm Kiếm",
    )
    add_styled_paragraph(
        doc,
        "Để nắm vững nền tảng lý thuyết đứng sau từng mô-đun trong kho mã nguồn ViTrueVoice, sinh viên nên đọc theo đúng thứ tự "
        "7 cụm công trình kinh điển dưới đây (từ biểu diễn tiếng nói cơ sở đến mô hình tạo sinh và hiệu chuẩn trọng số hiện đại):",
    )

    add_styled_table(
        doc,
        headers=[
            "Thứ Tự & Công Trình Gốc",
            "Đóng Góp Khoa Học Cốt Lõi Cần Đọc Hiểu",
            "Phần Cần Tập Trung Khi Đọc (3-Pass Focus)",
        ],
        rows=[
            (
                "1. Baevski et al. (NeurIPS 2020)\n*wav2vec 2.0: Self-Supervised Learning of Speech Representations*",
                "Đặt nền móng trích xuất đặc trưng ngữ âm trực tiếp từ sóng âm thô 16 kHz qua 7 tầng CNN và mạng Transformer che mặt nạ đối tương phản.",
                "Đọc kỹ Hình 1 (kiến trúc Feature Encoder bước nhảy 320 mẫu tạo ra 199 khung cho 4 giây) và mục Contrastive Loss.",
            ),
            (
                "2. Jung et al. (ICASSP 2022)\n*AASIST: Integrated Spectro-Temporal Graph Attention Networks*",
                "Đề xuất mạng chú ý đồ thị không đồng nhất `HS-GAL` kết hợp hai miền Thời gian – Tần số và nút điều phối toàn cục `Master Node`.",
                "Đọc kỹ mục Heterogeneous Graph Attention và bảng Ablation chứng minh vai trò của `Master Node` khi bắt lỗi vocoder.",
            ),
            (
                "3. Tak et al. (ICASSP & Odyssey 2022)\n*SSL-AASIST & RawBoost Data Augmentation*",
                "Ghép nối mặt trước `Wav2Vec 2.0` với đồ thị `AASIST` cùng nhiễu tuyến tính / tích chập `RawBoost` để chống suy giảm kênh truyền viễn thông.",
                "Đọc kỹ cấu hình ghép nối SSL front-end, tốc độ học vi chỉnh nhỏ (`1e-6`) và 3 thành phần nhiễu của `RawBoost`.",
            ),
            (
                "4. Lipman et al. (ICLR 2023) & Chen et al. (2024)\n*Flow Matching for Generative Modeling & F5-TTS*",
                "Xây dựng phương trình vi phân thường `ODE` dọc theo quỹ đạo vận chuyển tối ưu (`Optimal Transport`), tạo ra sóng âm nhân bản siêu mượt.",
                "Đọc phương trình trường vận tốc thẳng `x_t = (1 − t)x_0 + t·x_1` để hiểu tại sao `OmniVoice CFM` ít để lại gai nhiễu hơn Diffusion cũ.",
            ),
            (
                "5. Défossez et al. (2023) & Zhang et al. (ICLR 2024)\n*EnCodec & SpeechTokenizer (Discrete RVQ)*",
                "Nén sóng âm thành chuỗi mã rời rạc qua nhiều tầng lượng tử hóa phần dư (`Residual Vector Quantization - RVQ`) cho các mô hình ngôn ngữ âm học.",
                "Đọc cơ chế cộng dồn phần dư qua `M` cuốn từ điển mã (`codebooks`) để hiểu nguồn gốc sai số lượng tử hóa trong `VieNeu-TTS`.",
            ),
            (
                "6. Wortsman et al. (CVPR 2022)\n*WiSE-FT: Weight-Space Ensembles for Fine-Tuning*",
                "Chứng minh phép nội suy tuyến tính giữa trọng số trước và sau tinh chỉnh giữ được cả độ chính xác miền đích lẫn độ bền vững ngoại lai.",
                "Đọc công thức trộn trọng số tuyến tính theo hệ số `α` — chính là cơ sở lý thuyết trực tiếp của bước `head_blend_a0.75` trong `v0.9.4`.",
            ),
            (
                "7. Giao thức ASVspoof 2019 / 2021 / ASVspoof 5\n*(Yamagishi, Nautsch, Wang et al.)*",
                "Thiết lập chuẩn mực quốc tế về chia tập `Speaker-Disjoint`, thử thách nén codec điện thoại thực tế và thước đo `EER`, `minDCF`, `ISO/IEC 30107-3`.",
                "Đọc phần Evaluation Plan để nắm chắc công thức tính `APCER`, `BPCER`, đường cong `DET` và lý do không dùng `Accuracy`.",
            ),
        ],
        col_widths=[1.85, 2.55, 2.3],
    )

    add_heading_subsection(doc, "12.2.1 Bốn Chuỗi Truy Vấn Boolean Mẫu Dùng Ngay Trên Google Scholar & IEEE Xplore")
    add_bullet_item(
        doc,
        '`("audio anti-spoofing" OR "speech deepfake detection") AND ("wav2vec 2.0" OR "WavLM") AND ("AASIST" OR "graph attention")`',
        bold_prefix="Truy vấn 1 — Kiến trúc mạng SSL kết hợp đồ thị chú ý",
    )
    add_bullet_item(
        doc,
        '`("flow matching" OR "zero-shot voice cloning") AND ("spoofing detection" OR "deepfake") AND ("generalization" OR "unseen")`',
        bold_prefix="Truy vấn 2 — Phát hiện giọng giả sinh bởi Flow Matching thế hệ mới",
    )
    add_bullet_item(
        doc,
        '`("voice anti-spoofing" OR "deepfake audio") AND ("telephony" OR "Opus" OR "AMR-NB" OR "AAC") AND "EER"`',
        bold_prefix="Truy vấn 3 — Độ bền vững qua kênh nén thoại viễn thông & OTT",
    )
    add_bullet_item(
        doc,
        '`("weight-space ensembles" OR "WiSE-FT" OR "probability calibration" OR "Platt scaling") AND ("biometrics" OR "anti-spoofing")`',
        bold_prefix="Truy vấn 4 — Hiệu chuẩn không gian trọng số & xác suất sinh trắc học",
    )

    add_term_glossary(
        doc,
        terms=[
            ("IMRAD", "Introduction, Methods, Results, and Discussion", "Bố cục 4 phần chuẩn mực bắt buộc của hầu hết các bài báo thực nghiệm quốc tế trong ngành Khoa học Máy tính và Trí tuệ Nhân tạo."),
            ("ISCA Interspeech", "International Speech Communication Association", "Hội nghị khoa học uy tín bậc nhất thế giới chuyên sâu về công nghệ xử lý tiếng nói, nhận dạng giọng nói và chống giả mạo âm thanh."),
            ("ICASSP", "IEEE International Conference on Acoustics, Speech and Signal Processing", "Hội nghị hàng đầu của Hiệp hội Kỹ sư Điện và Điện tử `IEEE` về xử lý tín hiệu số, âm học và học sâu âm thanh."),
            ("Pre-print / arXiv", "Open-Access Electronic Preprint Archive", "Bản thảo công trình khoa học được nhóm tác giả công bố sớm trên kho mở `arXiv.org` trước hoặc song song với quá trình bình duyệt tạp chí/hội nghị."),
            ("Ablation Study", "Component Removal / Isolation Experiment", "Nghiên cứu bóc tách — thí nghiệm lần lượt tắt hoặc thay thế từng thành phần (như tắt `RawBoost`, đổi chế độ `Pooling`) để đo chính xác đóng góp riêng của nó."),
            ("Taxonomy", "Systematic Scientific Classification", "Hệ thống phân loại khoa học sắp xếp các khái niệm và thuật ngữ phức tạp vào từng trục kiến trúc rõ ràng, không chồng chéo."),
            ("WiSE-FT", "Weight-Space Ensembles for Fine-Tuning", "Kỹ thuật trộn tuyến tính hai bộ trọng số trong không gian tham số để đạt điểm cân bằng tối ưu mà không tốn gấp đôi chi phí suy luận."),
            ("RVQ", "Residual Vector Quantization", "Lượng tử hóa vector phần dư — kỹ thuật xấp xỉ liên tiếp phần sai số còn lại qua nhiều bảng mã rời rạc trong các bộ `Neural Audio Codec` hiện đại."),
        ],
    )
