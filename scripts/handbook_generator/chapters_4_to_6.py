# -*- coding: utf-8 -*-
"""
Chương 4, 5, 6: Kiến trúc mô hình SSL-AASIST, Suy luận đa cửa sổ Pooling và Hiệu chuẩn Platt Scaling
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from .styles import (
    add_heading_chapter,
    add_heading_section,
    add_heading_subsection,
    add_styled_paragraph,
    add_bullet_item,
    add_callout_box,
    add_prerequisite_box,
    set_cell_background,
    set_cell_margins,
    set_table_borders,
)

def add_chapters_4_to_6(doc):
    """Add chapters 4, 5, and 6 with comprehensive prerequisites and technical details."""

    # =========================================================================
    # CHƯƠNG 4
    # =========================================================================
    add_heading_chapter(doc, "Chương 4", "Kiến Trúc Mạng Nơ-Ron Tự Giám Sát SSL-AASIST & Chiến Lược Huấn Luyện")

    add_prerequisite_box(doc, "Chương 4", 
        "Học tự giám sát (Self-Supervised Learning - SSL: Masked Latent Reconstruction), "
        "Kiến trúc Transformer & Cơ chế Self-Attention (Q, K, V), Mạng nơ-ron đồ thị (GNN: Nodes, Edges, Message Passing), "
        "Hiện tượng Quên thảm khốc (Catastrophic Forgetting) & Tốc độ học phân tầng (Differential Learning Rates), "
        "Học khoảng cách siêu cầu & Biên độ góc AM-Softmax.")

    add_heading_section(doc, "4.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 4")
    add_styled_paragraph(doc, 
        "Kiến trúc của ViTrueVoice là sự kết hợp đỉnh cao giữa mô hình nền tảng ngôn ngữ tự giám sát (SSL) "
        "và mạng nơ-ron đồ thị không gian - thời gian (GNN). Người học cần nắm chắc 5 nguyên lý cốt lõi sau:")

    add_heading_subsection(doc, "4.0.1 Học Tự Giám Sát (SSL): Bí Quyết Huấn Luyện Mô Hình Không Cần Nhãn")
    add_styled_paragraph(doc, 
        "Trong học có giám sát truyền thống, ta cần hàng triệu giờ âm thanh được con người gán nhãn thủ công (rất đắt đỏ và tốn kém). "
        "Học tự giám sát (Self-Supervised Learning - SSL) giải quyết bài toán này bằng cách tự tạo ra nhiệm vụ học từ dữ liệu thô:\n"
        "- Mô hình che giấu ngẫu nhiên một số đoạn âm thanh (Masking), sau đó bắt mạng nơ-ron phải đoán xem đoạn bị che giấu chứa thông tin gì (Masked Latent Reconstruction).\n"
        "- Qua quá trình đoán hàng triệu lần, mô hình tự động thấu hiểu sâu sắc cấu trúc âm vị, quy luật thanh điệu và ngữ điệu tự nhiên của tiếng Việt mà không cần bất kỳ nhãn người nào!")

    add_heading_subsection(doc, "4.0.2 Kiến Trúc Transformer & Cơ Chế Chú Ý Không Gian Tự Thân (Self-Attention)")
    add_styled_paragraph(doc, 
        "Cơ chế Self-Attention cho phép mỗi vị trí trong chuỗi âm thanh nhìn vào tất cả các vị trí khác để tìm mối liên hệ ngữ cảnh. "
        "Toán học của Self-Attention dựa trên 3 ma trận:\n"
        "- **Query ($Q$)**: Đại diện cho câu hỏi: 'Tôi đang tìm kiếm đặc trưng gì?'.\n"
        "- **Key ($K$)**: Đại diện cho nhãn đánh chỉ mục: 'Tôi chứa đựng thông tin gì?'.\n"
        "- **Value ($V$)**: Đại diện cho giá trị nội dung thực tế.\n"
        "$$\\text{Attention}(Q, K, V) = \\text{Softmax}\\left(\\frac{Q K^T}{\\sqrt{d_k}}\\right) V$$\n"
        "Nhờ tích vô hướng $Q K^T$, mô hình nắm bắt được sự phụ thuộc xa (Long-range dependencies) giữa âm đầu và âm cuối câu thoại.")

    add_heading_subsection(doc, "4.0.3 Mạng Nơ-Ron Đồ Thị (Graph Neural Networks - GNN) & Truyền Tin (Message Passing)")
    add_styled_paragraph(doc, 
        "Mạng tích chập (CNN) chỉ xử lý dữ liệu dạng lưới 2D cố định (ảnh). Tuy nhiên, mối liên hệ giữa các tần số âm thanh không hề cố định theo dạng lưới. "
        "Lý thuyết đồ thị mô hình hóa dữ liệu thành tập các **Đỉnh (Nodes)** và **Cạnh (Edges)** nối các đỉnh:\n"
        "- **Cơ chế Truyền tin (Message Passing)**: Mỗi đỉnh sẽ thu thập thông tin từ các đỉnh láng giềng được kết nối với nó thông qua ma trận kề $A$, "
        "sau đó tổng hợp và cập nhật trạng thái mới của chính nó qua các hàm phi tuyến.\n"
        "- Đồ thị cho phép các tần số xa nhau (ví dụ tần số cơ bản 150Hz và hài bậc cao 3000Hz) 'nói chuyện trực tiếp' với nhau qua một cạnh đồ thị!")

    add_heading_subsection(doc, "4.0.4 Hiện Tượng Quên Thảm Khốc (Catastrophic Forgetting) & Tốc Độ Học Phân Tầng")
    add_styled_paragraph(doc, 
        "Khi một mô hình đã học được các đặc trưng tiếng Việt rất giỏi (Wav2Vec2), nếu ta tinh chỉnh (Fine-tune) nó trên một tập dữ liệu mới "
        "với tốc độ học quá lớn, toàn bộ các trọng số ngữ âm nền tảng sẽ bị ghi đè thô bạo. Mô hình sẽ quên sạch kiến thức cũ — hiện tượng này gọi là **Catastrophic Forgetting**.\n"
        "- **Giải pháp Tốc độ học Phân tầng (Differential Learning Rates)**: Đặt tốc độ học cho khối Wav2Vec2 cực nhỏ ($10^{-6}$) "
        "để giữ nguyên tri thức ngữ âm, trong khi đặt tốc độ học cho khối AASIST lớn hơn ($10^{-4}$) để nó tự do học dấu vết phân loại giả mạo.")

    add_heading_subsection(doc, "4.0.5 Học Biểu Diễn Khoảng Cách Trên Siêu Cầu & Biên Độ Góc AM-Softmax")
    add_styled_paragraph(doc, 
        "Hàm mất mát Softmax truyền thống chỉ quan tâm việc phân tách hai lớp, nhưng không ép các mẫu cùng lớp phải gom lại thật sát nhau. "
        "Hàm **AM-Softmax (Additive Margin Softmax)** chuẩn hóa các vector đặc trưng lên mặt cầu đơn vị và đưa vào một biên độ phạt góc $m$:\n"
        "$$\\mathcal{L} = -\\log \\frac{e^{s \\cdot (\\cos \\theta_y - m)}}{e^{s \\cdot (\\cos \\theta_y - m)} + \\sum_{j \\neq y} e^{s \\cdot \\cos \\theta_j}}$$\n"
        "Biên độ $m$ buộc mô hình phải ép các mẫu thật lại cực kỳ chặt chẽ trong một góc cầu hẹp, và đẩy các mẫu giả mạo ra xa một khoảng biên an toàn!")

    # -------------------------------------------------------------------------
    # 4.1 - 4.4 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "4.1 Khối Front-end Tự Giám Sát (SSL Backbone)")
    add_styled_paragraph(doc, 
        "ViTrueVoice sử dụng mô hình tự giám sát tiếng Việt `nguyenvulebinh/wav2vec2-base-vietnamese-250h` làm khối trích xuất đặc trưng nền tảng (Front-end). "
        "Kiến trúc gồm 7 lớp tích chập thời gian 1D (Temporal CNN) biến đổi 64.000 mẫu âm thanh thô thành chuỗi vector ẩn, "
        "theo sau bởi 12 lớp Transformer Encoder (768 chiều ẩn, 12 attention heads).")
    add_styled_paragraph(doc, 
        "Ưu thế vượt trội của SSL tiếng Việt so với các mô hình quốc tế (như Wav2Vec2-XLSR): "
        "Nó đã học sâu sắc đặc trưng ngữ âm có dấu thanh (6 thanh điệu tiếng Việt: ngang, huyền, sắc, hỏi, ngã, nặng). "
        "Các công cụ TTS khi sinh tiếng Việt thường gặp lỗi mất tự nhiên ở cao độ của dấu ngã và dấu hỏi. "
        "Khối front-end này bắt trọn các sai lệch thanh điệu đó ở ngay tầng biểu diễn ngữ âm.")

    add_heading_section(doc, "4.2 Khối Back-end Đồ Thị Chú Ý Không Đồng Nhất Compact AASIST (HS-GAL)")
    add_styled_paragraph(doc, 
        "Đặc trưng trích xuất từ tầng 12 của Wav2Vec 2.0 có kích thước $(B, 199, 768)$. Khối back-end Compact AASIST biến đổi ma trận này "
        "thành cấu trúc đồ thị không đồng nhất thông qua cơ chế HS-GAL (Heterogeneous Spatio-Temporal Graph Attention Layer):")
    add_bullet_item(doc, "Mỗi khung thời gian (199 khung) được xem là một nút trên đồ thị. Các nút thời gian lân cận được kết nối với nhau để học sự liên tục của ngữ điệu.", "Nút Miền Thời Gian (Temporal Nodes)")
    add_bullet_item(doc, "Các dải phổ tần số được chiếu thành các nút tần số. Các nút này kết nối chéo để học mối tương quan hài âm giữa các formant.", "Nút Miền Tần Số (Spectral Nodes)")
    add_bullet_item(doc, "Một nút nhân tạo đặc biệt được kết nối với TẤT CẢ các nút thời gian và TẤT CẢ các nút tần số. "
        "Nút này đóng vai trò là 'trung tâm điều phối', thu thập thông tin toàn cục từ cả hai miền và phát hiện sự phi logic giữa phổ tần số và diễn tiến thời gian do AI sinh ra.", "Nút Chủ Quyền (Master Node)")

    add_heading_section(doc, "4.3 Quy Trình Huấn Luyện 2 Pha (Two-Phase Fine-Tuning Protocol)")
    add_styled_paragraph(doc, 
        "Để tránh hiện tượng quên thảm khốc (Catastrophic Forgetting) khi tinh chỉnh mô hình lớn, dự án áp dụng quy trình huấn luyện 2 pha nghiêm ngặt:")
    add_bullet_item(doc, "Khóa chặt hoàn toàn (Freeze) 12 lớp của Wav2Vec 2.0. Chỉ cập nhật trọng số của khối đồ thị AASIST và tầng phân loại. "
        "Tốc độ học $\\text{lr} = 10^{-4}$, tối ưu bằng AdamW trong 5 epochs. Giai đoạn này giúp khối AASIST làm quen với các biểu diễn âm học tiếng Việt.", "Pha 1 (Frozen Backbone - 5 Epochs)")
    add_bullet_item(doc, "Mở khóa toàn bộ mô hình (Unfreeze), cho phép gradient lan truyền ngược vào cả Wav2Vec 2.0. "
        "Áp dụng cơ chế tốc độ học phân tầng (Differential Learning Rates): "
        "Khối Wav2Vec 2.0 sử dụng $\\text{lr}_{\\text{ssl}} = 10^{-6}$ (rất nhỏ để bảo toàn tri thức ngữ âm); "
        "Khối AASIST sử dụng $\\text{lr}_{\\text{gnn}} = 10^{-4}$. Huấn luyện tiếp 10 epochs kết hợp Cosine Annealing Scheduler.", "Pha 2 (Differential Fine-Tuning - 10 Epochs)")

    add_heading_section(doc, "4.4 Hàm Mất Mát Dynamic Weighted CE & AM-Softmax Margin")
    add_styled_paragraph(doc, 
        "Trong tập huấn luyện, tỷ lệ giữa mẫu người thật và mẫu giả mạo thường bị chênh lệch. "
        "Để cân bằng gradient, dự án sử dụng hàm mất mát Weighted Cross-Entropy tính động theo công thức:")
    add_styled_paragraph(doc, 
        "$$w_c = \\frac{N}{2 \\cdot N_c}$$\n"
        "Trong đó $N$ là tổng số mẫu của tập train, $N_c$ là số mẫu của lớp $c$ ($c \\in \\{\\text{bonafide}, \\text{spoof}\\}$). "
        "Hàm `loss_weights_from_counts` tự động tính trọng số này ngay khi nạp manifest.")

    add_callout_box(doc,
        "Theo STUBBORN_FACT của dự án: **Tuyệt đối KHÔNG ĐƯỢC PHÉP dùng đồng thời WeightedRandomSampler cùng với Weighted Loss!** "
        "Nếu bạn dùng `WeightedRandomSampler` để lấy mẫu cân bằng (tỷ lệ 50:50), rồi lại tiếp tục nhân thêm trọng số phạt $w_c$ trong hàm Loss, "
        "hệ thống sẽ bị lỗi **bù trừ kép (Double Penalty)**. Mô hình sẽ bị thiên lệch cực đoan về một phía, dẫn đến việc sụp đổ hoàn toàn độ nhạy.",
        title="BÍ QUYẾT PHẢN BIỆN #3: VÌ SAO KHÔNG DÙNG ĐỒNG THỜI SAMPLER VÀ WEIGHTED LOSS?")

    # =========================================================================
    # CHƯƠNG 5
    # =========================================================================
    add_heading_chapter(doc, "Chương 5", "Công Nghệ Suy Luận Đa Cửa Sổ Trượt & Max-Pooling (Multi-Window Inference)")

    add_prerequisite_box(doc, "Chương 5", 
        "Tính bất đối xứng của lỗi âm học (Acoustic Asymmetry), Kỹ thuật Cửa sổ trượt (Sliding Window & Hop Size), "
        "Phép gộp Average Pooling vs Max-Pooling, Tính chất cực trị của toán tử Max, Xử lý song song mini-batch trên GPU.")

    add_heading_section(doc, "5.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 5")
    add_styled_paragraph(doc, 
        "Tại sao việc cắt lấy 4.0 giây đầu tiên truyền thống lại làm sai lệch kết quả nhận diện người thật? "
        "Để trả lời câu hỏi hóc búa này của hội đồng, người học cần nắm chắc 4 nguyên lý toán học và âm học sau:")

    add_heading_subsection(doc, "5.0.1 Tính Bất Đối Xứng Của Lỗi Âm Học (Acoustic Asymmetry)")
    add_styled_paragraph(doc, 
        "Giữa giọng người thật và giọng AI tồn tại một sự bất đối xứng rất tinh tế về mặt sinh học:\n"
        "- **Người thật**: Trong 1–2 giây đầu khi bắt đầu nói, con người thường có thói quen hắng giọng, lấy hơi, ậm ừ ('à', 'ừm'), "
        "hoặc bị giật micro. Những đoạn này có năng lượng âm học bất thường, dễ làm mô hình nhầm lẫn là méo dạng của AI.\n"
        "- **Giọng AI tạo giả**: Kẻ gian tạo ra clip giọng nói tổng hợp hoàn hảo, nhưng ở những đoạn chuyển âm phức tạp hoặc cuối câu, "
        "thuật toán vocoder để lại các vết nứt vi mô. "
        "Do đó, một đoạn âm thanh dài 6–10 giây không thể bị đánh giá chỉ qua một lát cắt 4.0 giây duy nhất!")

    add_heading_subsection(doc, "5.0.2 Nguyên Lý Cửa Sổ Trượt (Sliding Window & Hop Size)")
    add_styled_paragraph(doc, 
        "Để quét toàn diện một tín hiệu dài mà không bị bỏ sót thông tin tại các điểm biên, "
        "người ta sử dụng kỹ thuật **Cửa sổ trượt (Sliding Window)**:\n"
        "- Đặt độ rộng cửa sổ $W = 64.000$ mẫu (4.0 giây).\n"
        "- Bước nhảy (Hop size) $H = 16.000$ mẫu (1.0 giây).\n"
        "- Khi trượt cửa sổ từ đầu đến cuối file, hai cửa sổ liên tiếp sẽ gối đầu lên nhau 75% ($3.0\\text{s}$). "
        "Sự gối đầu này đảm bảo mọi âm tiết tiếng Việt đều được nằm trọn vẹn ở vị trí trung tâm của ít nhất một cửa sổ!")

    add_heading_subsection(doc, "5.0.3 Bản Chất Toán Học Của Phép Gộp: Vì Sao Max-Pooling Thắng Average Pooling?")
    add_styled_paragraph(doc, 
        "Giả sử một file audio sau khi trượt sinh ra $K$ cửa sổ, mô hình cho ra $K$ điểm số: $s_1, s_2, \\dots, s_K$. "
        "Ta có hai cách gộp:\n"
        "- **Average Pooling**: $s_{\\text{final}} = \\frac{1}{K} \\sum_{i=1}^K s_i$. Điểm yếu: Nếu 1 cửa sổ phát âm rất tốt ($+30$) "
        "và 3 cửa sổ bị nhiễu do lấy hơi ($-10, -5, -5$), giá trị trung bình sẽ bị kéo về mức âm ($+2.5$), khiến người thật bị nghi ngờ oan!\n"
        "- **Max-Pooling**: $s_{\\text{final}} = \\max(s_1, s_2, \\dots, s_K)$. "
        "Theo định lý cực trị trên tập số thực: Chỉ cần trong file có MỘT đoạn người nói phát âm rõ ràng, mang đầy đủ đặc trưng sinh học "
        "con người (điểm $s > 0$ cao), toán tử Max sẽ bắt trọn giá trị cao nhất đó để chứng minh người thật, "
        "hoàn toàn miễn nhiễm với các đoạn ậm ừ lấy hơi ở đầu file!")

    add_heading_subsection(doc, "5.0.4 Tối Ưu Hóa Song Song Bằng Mini-Batching Trên Tensor GPU")
    add_styled_paragraph(doc, 
        "Nếu ta đưa từng cửa sổ qua mạng nơ-ron tuần tự ($K$ lần gọi mô hình), thời gian suy luận sẽ tăng lên gấp $K$ lần, "
        "vi phạm chỉ số thời gian thực NFR1. "
        "Giải pháp kỹ thuật: Gom toàn bộ $K$ cửa sổ của một file thành một **mini-batch tensor duy nhất** có kích thước $(K, 64000)$. "
        "Mô hình chỉ thực hiện một lượt truyền thẳng (Forward pass) duy nhất trên GPU, sau đó áp dụng phép toán `torch.max(dim=0)` "
        "trong đúng 0.05 mili-giây!")

    # -------------------------------------------------------------------------
    # 5.1 - 5.2 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "5.1 Thách Thức BPCER Khi Cắt 4.0 Giây Đầu Truyền Thống")
    add_styled_paragraph(doc, 
        "Trong các phiên bản ban đầu (v0.4.1 và v0.4.2), hệ thống áp dụng phương pháp truyền thống: cắt lấy đúng 4.0 giây đầu tiên "
        "của file âm thanh để suy luận. Hậu quả thực nghiệm vô cùng tai hại:")
    add_bullet_item(doc, "Nhiều tình nguyện viên nói thật (như SPK_0004, SPK_0005) trong 1–2 giây đầu chỉ là tiếng lấy hơi, thở dài hoặc ậm ừ chuẩn bị nói. Đoạn này có năng lượng thấp và méo hài vi mô, khiến mô hình chấm điểm âm ($s < 0$) và phán quyết là Deepfake!", "Hiện tượng Báo Động Oan (BPCER cao)")
    add_bullet_item(doc, "Tỷ lệ vượt qua Gate 2 trên 5 tình nguyện viên nghiệm thu chỉ đạt 89.3%, bị rớt 9 clip bona fide.", "Hậu quả nghiệm thu")

    add_heading_section(doc, "5.2 Giải Thuật Multi-Window Sliding Window & Max-Pooling (`pooling.py`)")
    add_styled_paragraph(doc, 
        "Để giải quyết triệt để vấn đề mà KHÔNG CẦN HUẤN LUYỆN LẠI GPU (0 retrain GPU), phiên bản v0.4.3 đã thiết kế "
        "giải thuật trích xuất đa cửa sổ trượt kết hợp Max-Pooling trong module `src/preprocessing/pooling.py`:")
    add_bullet_item(doc, "Cửa sổ trượt cố định $W = 64.000$ mẫu (4.0s). Bước nhảy trượt $H = 16.000$ mẫu (1.0s). "
        "Số lượng cửa sổ tối đa giới hạn ở $N_{\\max} = 5$ cửa sổ (đảm bảo độ trễ suy luận luôn cực thấp).", "Thông số Cửa Sổ Trượt")
    add_bullet_item(doc, "Toàn bộ $N$ cửa sổ ($1 \\le N \\le 5$) được gộp lại thành một batch tensor $(N, 64000)$ và đưa qua mô hình trong **một lượt suy luận duy nhất (Single Forward Pass)** trên GPU.", "Batching Song Song")
    add_bullet_item(doc, "Thu được $N$ điểm số thô: $[s_1, s_2, \\dots, s_N]$. Điểm số đại diện cuối cùng của file là giá trị cực đại: "
        "$$s_{\\text{final}} = \\max(s_1, s_2, \\dots, s_N)$$\n"
        "BẢN CHẤT ÂM HỌC: Chỉ cần người nói có ít nhất 1 cửa sổ thể hiện rõ đặc trưng sinh trắc học tự nhiên của con người (không có dấu vết méo của vocoder), "
        "giá trị cực đại đó sẽ bảo vệ người dùng, loại bỏ hoàn toàn các lỗi báo động giả do lấy hơi ở đầu clip.", "Toán tử Max-Pooling")

    add_callout_box(doc,
        "KẾT QUẢ ĐỘT PHÁ CỦA MULTI-WINDOW MAX-POOLING: "
        "Nâng tỷ lệ vượt Gate 2 trên 4 tình nguyện viên đối chứng lên **100.0% (64/64 clip)** và trên cả 5 tình nguyện viên lên **96.4% (81/84 clip)**. "
        "Đồng thời, tỷ lệ bỏ sót spoof (APCER) trên tập Dev vẫn được giữ vững ở mức cực kỳ an toàn: **6.77% <= 8.0%**. "
        "Độ trễ suy luận chỉ tăng từ 64.1ms lên **66.3ms** (vẫn nhanh gấp 45 lần yêu cầu NFR1 <= 3.0s).",
        title="BẰNG CHỨNG THỰC NGHIỆM ĐẬP TAN CÂU HỎI VỀ BPCER CỦA HỘI ĐỒNG")

    # =========================================================================
    # CHƯƠNG 6
    # =========================================================================
    add_heading_chapter(doc, "Chương 6", "Hiệu Chuẩn Độ Tin Cậy Toán Học Platt Scaling & Chuẩn Forensics NIST")

    add_prerequisite_box(doc, "Chương 6", 
        "Logits vs Xác suất, Hàm Sigmoid & Log-odds mapping, Hiện tượng Quá tự tin (Overconfidence in Deep Learning), "
        "Lỗi hiệu chuẩn xác suất (Expected Calibration Error - ECE, Brier Score), Hồi quy Logistic Platt Scaling, "
        "Nguyên lý bất định trong Giám định Pháp y NIST, Đại lượng phân vị IQR & Guardrails an toàn.")

    add_heading_section(doc, "6.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 6")
    add_styled_paragraph(doc, 
        "Đưa một mô hình AI vào thực tế không chỉ dừng lại ở việc phân loại nhị phân mà phải cung cấp một thước đo độ tin cậy "
        "chính xác cho cơ quan điều tra và người dùng. Người học cần nắm chắc 5 nguyên lý sau:")

    add_heading_subsection(doc, "6.0.1 Logits Trong Mạng Nơ-Ron vs Xác Suất Thực Nghiệm")
    add_styled_paragraph(doc, 
        "Tầng cuối cùng của mạng nơ-ron trước hàm kích hoạt đưa ra các giá trị số thực thô gọi là **Logits** "
        "(nằm trong khoảng từ $-\\infty$ đến $+\\infty$).\n"
        "- Điểm thô $s = z_{\\text{bonafide}} - z_{\\text{spoof}}$ chỉ có ý nghĩa về mặt thứ tự (Ordinal): "
        "$s = +10$ chắc chắn thật hơn $s = +2$. Tuy nhiên, ta KHÔNG THỂ nói rằng $s = +10$ thì có 99% khả năng là người thật!\n"
        "- Hàm Sigmoid tiêu chuẩn $\\sigma(s) = \\frac{1}{1 + e^{-s}}$ chỉ đơn thuần là một phép ánh xạ hình học đưa khoảng $(-\\infty, +\\infty)$ "
        "về đoạn $[0, 1]$, nó hoàn toàn không phản ánh tần suất xác suất thực nghiệm ngoài đời thực.")

    add_heading_subsection(doc, "6.0.2 Hiện Tượng Quá Tự Tin (Overconfidence) & Đo Lường Lỗi Hiệu Chuẩn ECE")
    add_styled_paragraph(doc, 
        "Các mạng nơ-ron hiện đại (như Wav2Vec2 và Transformers) mắc phải một căn bệnh kinh niên: **Cực kỳ quá tự tin (Overconfident)**. "
        "Chúng thường xuyên đưa ra các dự đoán với xác suất $99.99\\%$ ngay cả khi chúng đang đoán sai!\n"
        "- **Expected Calibration Error (ECE)**: Chia khoảng xác suất dự đoán $[0, 1]$ thành $M$ khoảng nhỏ (Bins). "
        "Trong từng khoảng, tính độ chênh lệch tuyệt đối giữa Độ Tin Cậy Trung Bình của mô hình (Average Confidence) "
        "và Độ Chính Xác Thực Tế (Accuracy). Một mô hình được hiệu chuẩn hoàn hảo phải có $ECE = 0$.")

    add_heading_subsection(doc, "6.0.3 Phương Pháp Hồi Quy Logistic Platt Scaling")
    add_styled_paragraph(doc, 
        "Platt Scaling (được đề xuất bởi John Platt năm 1999) là phương pháp dùng một mô hình hồi quy Logistic đơn biến "
        "để ánh xạ điểm số thô $s$ thành xác suất thực nghiệm $P$:\n"
        "$$P(Y = 1 | s) = \\frac{1}{1 + e^{-(A \\cdot s + B)}}$$\n"
        "Hai tham số $A$ và $B$ được tối ưu hóa trên một tập dữ liệu thẩm định độc lập (Validation set) bằng phương pháp cực đại hóa hàm hợp lý (Maximum Likelihood). "
        "Platt Scaling làm phẳng các vùng quá tự tin, đưa xác suất về đúng với phân phối thực tế.")

    add_heading_subsection(doc, "6.0.4 Nguyên Lý Bất Định Trong Khoa Học Giám Định Kỹ Thuật Hình Sự (NIST Forensics)")
    add_styled_paragraph(doc, 
        "Trong khoa học pháp y và hình sự quốc tế (NIST Forensic Science Standards), **không bao giờ có một phép đo thực nghiệm nào đạt độ chắc chắn tuyệt đối 100% hay 0.0%**. "
        "Luôn tồn tại sai số ngẫu nhiên của thiết bị thu âm, nhiễu môi trường và sự biến thiên sinh học của con người. "
        "Một hệ thống giám định deepfake nếu hiển thị cho tòa án hoặc người dân rằng: 'Độ tin cậy 100% là giả mạo' "
        "thì hệ thống đó vi phạm nguyên tắc khoa học pháp lý, vì nó triệt tiêu quyền hoài nghi hợp lý (Reasonable Doubt).")

    add_heading_subsection(doc, "6.0.5 Khoảng Phân Vị IQR & Cơ Chế Guardrail Tự Vệ An Toàn")
    add_styled_paragraph(doc, 
        "Khoảng tứ phân vị (Interquartile Range - $IQR = Q_3 - Q_1$) là thước đo độ phân tán thống kê vững chắc (Robust statistics), "
        "không bị ảnh hưởng bởi các giá trị ngoại lai cực đoan (Outliers). "
        "Bằng cách thiết lập rào chắn an toàn (Guardrail) dựa trên bội số của IQR (ví dụ $4 \\times IQR$), "
        "hệ thống có thể phát hiện ngay khi có ai đó cố tình can thiệp hoặc khi gặp một mẫu giọng quá bất thường để từ chối can thiệp tự động.")

    # -------------------------------------------------------------------------
    # 6.1 - 6.4 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "6.1 Sai Lầm Của Điểm Thô & Hàm Sigmoid Giả Tạo")
    add_styled_paragraph(doc, 
        "Nhiều hệ thống AI thương mại mắc một sai lầm nghiêm trọng trong giao diện người dùng: "
        "Lấy điểm số thô $s$ đưa trực tiếp vào hàm Sigmoid tiêu chuẩn $\\sigma(s) = \\frac{1}{1 + e^{-s}}$ rồi công bố đó là 'Độ tin cậy xác suất'. "
        "Đây là một sự giả tạo toán học: vì điểm $s$ của mô hình có dải giá trị rất rộng (từ $-50$ đến $+50$), "
        "hàm Sigmoid thông thường sẽ lập tức bão hòa ở hai cực, biến mọi dự đoán thành **99.9% Thật** hoặc **99.9% Giả**, "
        "hoàn toàn phá hủy ý nghĩa thống kê.")

    add_heading_section(doc, "6.2 Mô Hình Hồi Quy Logistic Platt Scaling")
    add_styled_paragraph(doc, 
        "ViTrueVoice áp dụng giải thuật chuẩn hóa xác suất Platt Scaling chính quy. "
        "Sử dụng tập dữ liệu Dev độc lập gồm 11.450 mẫu Zalo làm tập cân chỉnh (Calibration set), "
        "hệ thống tối ưu hóa tham số độ dốc nhiệt độ (Temperature scale parameter) $k$ qua phương pháp Maximum Likelihood:")
    add_styled_paragraph(doc, 
        "$$P(\\text{spoof} | s) = \\frac{1}{1 + e^{-k \\cdot (-s)}} = \\frac{1}{1 + e^{k \\cdot s}}$$\n"
        "Với hệ số tối ưu thực nghiệm được khóa chết tại: **k = 0.3569**.\n"
        "Nhờ có Platt Scaling, một điểm số $s = -5.0$ sẽ được ánh xạ thành xác suất giả mạo xấp xỉ **85.6%** (thay vì nhảy vọt lên 99.3% như Sigmoid thô), "
        "phản ánh chính xác mức độ hoài nghi của mô hình.")

    add_heading_section(doc, "6.3 Guardrail An Toàn Chuẩn NIST Forensics: Kẹp [0.1%, 99.9%]")
    add_styled_paragraph(doc, 
        "Tuân thủ nghiêm ngặt Hướng dẫn Giám định Âm thanh Pháp y của Viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ (NIST Forensic Science Standards), "
        "hệ thống ViTrueVoice thiết lập rào chắn an toàn (Guardrail) cứng tại tầng suy luận:")
    add_styled_paragraph(doc, 
        "$$P_{\\text{calibrated}} = \\text{clip}(P_{\\text{platt}}, 0.001, 0.999)$$\n"
        "Ý NGHĨA KHOA HỌC: Hệ thống TUYỆT ĐỐI KHÔNG BAO GIỜ hiển thị 100.0% hay 0.0%. "
        "Trong giám định pháp y kỹ thuật số, luôn tồn tại một sai số biên sinh học không thể triệt tiêu. "
        "Việc kẹp xác suất trong khoảng $[0.1\\%, 99.9\\%]$ bảo toàn tính khách quan tư pháp và ngăn chặn việc ngộ nhận chứng cứ trước tòa án.")

    add_heading_section(doc, "6.4 Guardrail Hiệu Chỉnh Enrollment (IQR Guard)")
    add_styled_paragraph(doc, 
        "Trong kịch bản người dùng đăng ký giọng mẫu (Enrollment) để hiệu chỉnh ngưỡng cá nhân hóa, "
        "nếu giọng người dùng quá dị biệt (như trường hợp tình nguyện viên ngoại lai SPK_0001 lệch tới $-9.91 \\times IQR$), "
        "hệ thống tự động kích hoạt **IQR Guardrail**:")
    add_bullet_item(doc, "Nếu độ lệch $|\\text{offset}| > 4 \\times IQR$ (với $IQR = 14.50$, ngưỡng từ chối là $|\\text{offset}| > 58.0$), "
        "hệ thống tự động TỪ CHỐI can thiệp dời ngưỡng tự động.", "Cơ chế Tự Vệ")
    add_bullet_item(doc, "Hệ thống bảo toàn nguyên vẹn điểm số thô và chuyển giao clip sang luồng xem xét thủ công (Human-in-the-loop Forensic Audit), "
        "ngăn chặn triệt để nguy cơ kẻ gian lợi dụng việc đăng ký giọng mẫu để hạ thấp rào cản an ninh của hệ thống.", "Ý nghĩa Bảo mật")

    add_callout_box(doc,
        "Khi hội đồng hỏi: 'Tại sao giao diện của các em hiển thị cao nhất chỉ là 99.9% mà không phải 100%?', bạn trả lời: **'Dạ thưa Thầy/Cô, hệ thống của chúng em tuân thủ nghiêm ngặt tiêu chuẩn giám định kỹ thuật hình sự pháp y của NIST. Trong khoa học nhận dạng âm thanh, luôn tồn tại sai số biên ngẫu nhiên do micro và biến thiên sinh học của con người. Không có một hệ thống pháp y chuẩn mực nào được phép khẳng định chắc chắn 100%. Việc kẹp an toàn trong khoảng [0.1%, 99.9%] là minh chứng cho tính trung thực khoa học và chuẩn mực pháp lý quốc tế của đề tài.'**",
        title="BÍ QUYẾT PHẢN BIỆN #4: TẠI SAO KHÔNG BAO GIỜ HIỂN THỊ 100%?")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)
