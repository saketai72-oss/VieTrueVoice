# -*- coding: utf-8 -*-
"""
Chương 1, 2, 3: Cơ sở lý thuyết, Dữ liệu sinh mẫu giả và Xử lý tín hiệu âm thanh DSP
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

def add_chapters_1_to_3(doc):
    """Add chapters 1, 2, and 3 with comprehensive prerequisites and technical details."""

    # =========================================================================
    # CHƯƠNG 1
    # =========================================================================
    add_heading_chapter(doc, "Chương 1", "Tổng Quan Đề Tài, Bài Toán Thực Tế & Cơ Chế Đánh Giá Khoa Học")
    
    add_prerequisite_box(doc, "Chương 1", 
        "Phân loại nhị phân (Binary Classification), Ma trận nhầm lẫn (Confusion Matrix), "
        "Lỗi Loại I & Lỗi Loại II, Nghịch lý độ chính xác trên dữ liệu mất cân bằng (Imbalanced Data Paradox), "
        "Đường cong ROC và AUC, Điểm cân bằng lỗi EER, Lý thuyết quyết định Bayes & Hàm chi phí rủi ro minDCF.")

    add_heading_section(doc, "1.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 1")
    add_styled_paragraph(doc, 
        "Để nắm bắt trọn vẹn bản chất toán học của các chỉ số đánh giá chuyên sâu trong chương này, "
        "người mới bắt đầu cần hiểu rõ 5 khái niệm cốt lõi sau đây:")

    add_heading_subsection(doc, "1.0.1 Bài Toán Phân Loại Nhị Phân & Ma Trận Nhầm Lẫn (Confusion Matrix)")
    add_styled_paragraph(doc, 
        "Trong học máy, bài toán phân loại nhị phân (Binary Classification) là bài toán dự đoán một quan sát thuộc về một trong hai lớp. "
        "Trong đề tài ViTrueVoice, hai lớp đó là:\n"
        "- **Lớp Giả Mạo (Spoof / Positive)**: Cuộc tấn công giọng nói nhân tạo bằng AI.\n"
        "- **Lớp Người Thật (Bona fide / Negative)**: Giọng nói con người sinh học tự nhiên.\n"
        "Khi đưa mô hình vào thẩm định, ta so sánh giữa Nhãn Thực Tế (Ground Truth) và Dự Đoán Của Mô Hình, sinh ra 4 trường hợp (Ma trận nhầm lẫn):")
    add_bullet_item(doc, "Mẫu thực tế là Spoof và mô hình dự đoán chính xác là Spoof (Bắt đúng tội phạm lừa đảo).", "True Positive (TP)")
    add_bullet_item(doc, "Mẫu thực tế là Bona fide và mô hình dự đoán chính xác là Bona fide (Xác nhận đúng người thật).", "True Negative (TN)")
    add_bullet_item(doc, "Mẫu thực tế là Bona fide nhưng mô hình đoán nhầm thành Spoof (Báo động giả / oan sai).", "False Positive (FP - Lỗi Loại I)")
    add_bullet_item(doc, "Mẫu thực tế là Spoof nhưng mô hình đoán nhầm thành Bona fide (Bỏ lọt tội phạm lừa đảo).", "False Negative (FN - Lỗi Loại II)")

    add_heading_subsection(doc, "1.0.2 Sự Khác Nhau Giữa Lỗi Loại I (Type I Error) và Lỗi Loại II (Type II Error)")
    add_styled_paragraph(doc, 
        "Trong khoa học bảo mật và sinh trắc học, hai loại lỗi này gây ra hậu quả hoàn toàn bất đối xứng:\n"
        "- **Lỗi Loại I (BPCER / False Positive)**: Người dùng thật gửi tin nhắn thoại nhờ người thân mượn tiền nhưng hệ thống báo động đỏ là giả mạo. Hậu quả là người dùng cảm thấy phiền toái, nhưng tiền bạc không bị mất.\n"
        "- **Lỗi Loại II (APCER / False Negative)**: Kẻ lừa đảo dùng AI nhân bản giọng nói để chiếm đoạt tài sản, nhưng hệ thống lại bảo vệ cho rằng đây là người thật. Hậu quả là nạn nhân mất tiền, thiệt hại tài chính vô cùng nghiêm trọng!\n"
        "Do đó, trong an ninh thông tin, người ta luôn ưu tiên ép tỷ lệ APCER (bỏ sót) xuống mức thấp nhất có thể.")

    add_heading_subsection(doc, "1.0.3 Nghịch Lý Độ Chính Xác (Accuracy Paradox) Trên Dữ Liệu Mất Cân Bằng")
    add_styled_paragraph(doc, 
        "Giả sử trên mạng viễn thông thực tế, có 99.000 cuộc gọi thật và chỉ có 1.000 cuộc gọi deepfake (tỷ lệ 99:1). "
        "Nếu một lập trình viên ngây thơ xây dựng một mô hình 'vô dụng' luôn đoán mọi cuộc gọi đều là người thật, "
        "thì độ chính xác tổng thể (Accuracy) của hệ thống sẽ đạt ngay **99,0%**! "
        "Con số 99% này tạo ra một ảo tưởng nguy hiểm: mô hình tưởng chừng hoàn hảo nhưng thực tế đã **bỏ sót 100% các cuộc gọi lừa đảo** (APCER = 100%). "
        "Chính vì lý do này, giới khoa học thế giới nghiêm cấm dùng Accuracy để đánh giá hệ thống phòng chống gian lận sinh trắc học.")

    add_heading_subsection(doc, "1.0.4 Bản Chất Hình Học Của Đường Cong ROC và Điểm Cân Bằng Sai Số EER")
    add_styled_paragraph(doc, 
        "Mô hình không đưa ra quyết định Có/Không ngay lập tức mà đưa ra một điểm số liên tục $s$. "
        "Bằng cách thay đổi ngưỡng quyết định $\\theta$ từ $-\\infty$ đến $+\\infty$, ta thu được một đồ thị biểu diễn sự đánh đổi giữa "
        "tỷ lệ bắt đúng tội phạm và tỷ lệ báo động giả — gọi là đường cong ROC (Receiver Operating Characteristic). "
        "Diện tích dưới đường cong (AUC) đo lường khả năng phân tách: $AUC = 1.0$ là hoàn hảo, $AUC = 0.5$ tương đương tung đồng xu ngẫu nhiên.\n"
        "**Equal Error Rate (EER)** là điểm giao cắt kỳ diệu trên đường cong lỗi: nơi mà tỷ lệ bỏ sót tội phạm (APCER) bằng đúng tỷ lệ báo oan người thật (BPCER). "
        "EER cung cấp một con số duy nhất độc lập với ngưỡng cắt, phản ánh năng lực cốt lõi của kiến trúc mạng.")

    add_heading_subsection(doc, "1.0.5 Lý Thuyết Quyết Định Bayes & Hàm Chi Phí Quyết Định Tối Thiểu minDCF")
    add_styled_paragraph(doc, 
        "Lý thuyết quyết định Bayes (Bayesian Decision Theory) chỉ ra rằng: một quyết định tối ưu phải dựa trên việc cực tiểu hóa chi phí rủi ro kỳ vọng. "
        "Hàm chi phí minDCF của Viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ (NIST) chính là hiện thân của nguyên lý này, "
        "khi gán trọng số thiệt hại của việc bỏ lọt lừa đảo gấp 10 lần ($C_{\\text{fa}} = 10$) so với việc báo nhầm người thật ($C_{\\text{miss}} = 1$).")

    # -------------------------------------------------------------------------
    # 1.1, 1.2, 1.3 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "1.1 Bối Cảnh Thực Tế & Động Lực Nghiên Cứu")
    add_styled_paragraph(doc, 
        "Tại Việt Nam trong giai đoạn 2024–2026, hình thức lừa đảo qua mạng viễn thông và mạng xã hội (đặc biệt là tin nhắn thoại Zalo, Telegram và cuộc gọi thoại giả danh) đã bước sang thế hệ mới: **sử dụng công nghệ Voice Cloning (nhân bản giọng nói AI)**. Đối tượng tội phạm công nghệ cao chỉ cần thu thập một đoạn âm thanh ngắn (3–10 giây) từ video TikTok, Facebook Reels hoặc cuộc gọi khảo sát của nạn nhân, sau đó sử dụng các công cụ sinh giọng nói thế hệ mới (như F5-TTS, VieNeu-TTS, VoiceStudio CFM) để tổng hợp các đoạn tin nhắn thoại mượn tiền, thông báo tai nạn, yêu cầu chuyển khoản khẩn cấp hoặc xác nhận mã OTP.")
    add_styled_paragraph(doc, 
        "Khác với môi trường phòng thí nghiệm lý tưởng (âm thanh chuẩn 44.1kHz/48kHz WAV không nén), các cuộc tấn công lừa đảo thực tế luôn diễn ra qua **kênh truyền nén suy hao**: tin nhắn thoại Zalo sử dụng Opus 24kbps hoặc AAC-LC 76kbps, cuộc gọi di động GSM sử dụng AMR-NB 12.2kbps, cuộc gọi điện thoại bàn PSTN sử dụng G.711 A-law 64kbps ở tần số lấy mẫu bị bóp nghẽn chỉ còn 8.000 Hz. Các thuật toán nén này thực hiện biến đổi cosin rời rạc (MDCT) và lượng tử hóa thô bạo, làm phẳng các méo hài vi mô (micro-harmonic artifacts) mà các bộ phát hiện deepfake truyền thống thường dựa vào.")
    
    add_heading_section(doc, "1.2 Câu Hỏi Nghiên Cứu & Giả Thuyết Khoa Học (CH1, CH2, H1, H2)")
    add_styled_paragraph(doc, "Đề tài được xây dựng nhằm trả lời chính xác hai câu hỏi nghiên cứu cốt lõi:")
    add_bullet_item(doc, "Độ bền của mô hình trước hiện tượng suy hao và nén kênh thoại viễn thông là bao nhiêu? Liệu việc tăng cường nén kênh thoại trong quá trình huấn luyện có giúp mô hình duy trì độ nhạy khi kẻ gian truyền âm thanh qua Zalo, GSM và PSTN?", "Câu hỏi CH1 (Channel Robustness)")
    add_bullet_item(doc, "Khả năng tổng quát hóa của mô hình trước các công cụ tổng hợp giọng nói chưa từng thấy (Unseen TTS) là như thế nào? Mô hình có bị 'học vẹt' dấu vết riêng của một công cụ cụ thể hay thực sự học được bản chất nhân tạo của giọng nói tổng hợp?", "Câu hỏi CH2 (Unseen TTS Generalization)")
    
    add_styled_paragraph(doc, "Từ đó, đề tài thiết lập hai giả thuyết khoa học định lượng (Pre-registered Hypotheses) để kiểm chứng trước hội đồng:")
    add_bullet_item(doc, "Mô hình được huấn luyện tăng cường kênh thoại (ViTrueVoice - Nhánh B) giảm ít nhất **>= 30% tỷ lệ sai số EER tương đối** trên tập kiểm định nén (Opus, AMR-NB, G.711, 8kHz) so với mô hình baseline không tăng cường (Nhánh A).", "Giả thuyết H1 (CH1)")
    add_bullet_item(doc, "Mô hình duy trì **EER <= 15.0%** trên các công cụ tổng hợp giọng nói hoàn toàn chưa từng xuất hiện trong tập huấn luyện (Unseen Zero-Shot TTS - VoiceStudio CFM).", "Giả thuyết H2 (CH2 / NFR2)")
    
    add_heading_section(doc, "1.3 Bản Chất Toán Học Của Các Chỉ Số Thẩm Định Âm Học")
    add_styled_paragraph(doc, "Để hiểu sâu và trả lời lưu loát trước hội đồng, sinh viên cần phân biệt rõ ràng 5 chỉ số sau:")
    
    add_heading_subsection(doc, "1. Điểm thô Logit (Raw Score - s)")
    add_styled_paragraph(doc, 
        "Đầu ra của mô hình SSL-AASIST gồm 2 logits $[z_{\text{spoof}}, z_{\text{bonafide}}]$. Điểm số thô được định nghĩa là hiệu số: **s = z_bonafide - z_spoof**. "
        "Theo quy ước khoa học toàn cầu (ASVspoof Consortium): Điểm s mang giá trị dương ($s > 0$) thể hiện xu hướng giọng người thật (Bona fide); Điểm s mang giá trị âm ($s < 0$) thể hiện xu hướng giọng giả mạo (Spoof). Ngưỡng phân định mặc định ban đầu là theta = 0.0.")
    
    add_heading_subsection(doc, "2. Hai loại sai số cơ bản: APCER và BPCER")
    add_styled_paragraph(doc, 
        "Trong lĩnh vực trắc sinh học âm thanh (ISO/IEC 30107-3), hai lỗi này được định nghĩa cực kỳ chuẩn xác:\n"
        "- **APCER (Attack Presentation Classification Error Rate)** — hay còn gọi là **FAR (False Acceptance Rate)**: Tỷ lệ mẫu GIẢ MẠO nhưng hệ thống lại nhận diện NHẦM thành người thật (Bỏ sót deepfake). Công thức: $\\text{APCER} = \\frac{\\text{Số mẫu Spoof bị gán nhãn Bona}}{\\text{Tổng số mẫu Spoof}}$.\n"
        "- **BPCER (Bona Fide Presentation Classification Error Rate)** — hay còn gọi là **FRR (False Rejection Rate)**: Tỷ lệ mẫu NGƯỜI THẬT nhưng hệ thống lại báo NHẦM thành giả mạo (Báo động giả). Công thức: $\\text{BPCER} = \\frac{\\text{Số mẫu Bona bị gán nhãn Spoof}}{\\text{Tổng số mẫu Bona}}$.")

    add_heading_subsection(doc, "3. Điểm cân bằng sai số EER (Equal Error Rate)")
    add_styled_paragraph(doc, 
        "EER là giá trị sai số tại ngưỡng quyết định theta_EER mà tại đó tỷ lệ bỏ sót deepfake bằng đúng tỷ lệ báo nhầm người thật: **APCER(theta_EER) = BPCER(theta_EER) = EER**. "
        "EER càng nhỏ thì mô hình càng hoàn hảo (EER = 0% nghĩa là phân tách tuyệt đối Thật và Giả).")

    add_heading_subsection(doc, "4. Chi phí quyết định tối thiểu minDCF (Minimum Detection Cost Function)")
    add_styled_paragraph(doc, 
        "minDCF là chỉ số chuẩn mực của Vi viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ (NIST SRE/ASVspoof). minDCF không coi 2 loại sai số có hậu quả ngang nhau, mà gán trọng số thiệt hại thực tế:\n"
        "$$\\text{DCF}(\\theta) = C_{\\text{miss}} \\cdot P_{\\text{target}} \\cdot \\text{BPCER}(\\theta) + C_{\\text{fa}} \\cdot (1 - P_{\\text{target}}) \\cdot \\text{APCER}(\\theta)$$\n"
        "Trong đó $C_{\\text{miss}} = 1$ (chi phí báo nhầm), $C_{\\text{fa}} = 10$ (chi phí bỏ sót lừa đảo), $P_{\\text{target}} = 0.05$ (xác suất gặp người thật). minDCF chuẩn hóa là giá trị nhỏ nhất của DCF chia cho chi phí của hệ thống mặc định.")

    add_heading_subsection(doc, "5. Đường cong DET (Detection Error Trade-off) và ROC-AUC")
    add_styled_paragraph(doc, 
        "Đường cong DET vẽ mối quan hệ giữa APCER và BPCER trên thang đo độ lệch chuẩn Gauss. Đường DET càng ép sát về góc dưới bên trái thì mô hình càng mạnh. ROC-AUC là diện tích dưới đường cong ROC (AUC = 1.0 nghĩa là độ chính xác tuyệt đối).")

    add_callout_box(doc,
        "Khi hội đồng hỏi: 'Tại sao lại dùng EER mà không dùng Accuracy thông thường?', bạn trả lời: **'Dạ thưa Thầy/Cô, trong bài toán an ninh sinh trắc học và phát hiện gian lận, tập dữ liệu thực tế luôn bị mất cân bằng nghiêm trọng (ví dụ 95% cuộc gọi là thật, chỉ 5% là lừa đảo). Nếu dùng Accuracy, một hệ thống chỉ cần luôn đoán là người thật sẽ đạt ngay độ chính xác 95% nhưng lại bỏ sót 100% các cuộc tấn công deepfake. Do đó, chuẩn quốc tế NIST và ASVspoof bắt buộc sử dụng EER và minDCF để đánh giá độc lập ngưỡng cắt, không bị phụ thuộc vào tỷ lệ mẫu.'**",
        title="BÍ QUYẾT PHẢN BIỆN #1: VÌ SAO DÙNG EER THAY CHO ACCURACY?")

    # =========================================================================
    # CHƯƠNG 2
    # =========================================================================
    add_heading_chapter(doc, "Chương 2", "Bản Đồ Dữ Liệu & Quy Trình Kỹ Thuật Sinh Mẫu Giả Kép (Data Pipeline)")

    add_prerequisite_box(doc, "Chương 2", 
        "Hiện tượng rò rỉ dữ liệu (Data Leakage), Kiến trúc Text-to-Speech (TTS Pipeline: Text -> Acoustic Model -> Vocoder), "
        "3 thế hệ TTS (Concatenative -> Neural Vocoder -> Diffusion & Flow Matching), Tỷ lệ lỗi nhận dạng ASR (WER/CER & Khoảng cách Levenshtein), "
        "Không gian nhúng người nói (Speaker Embedding) & Độ tương đồng Cosine (Cosine Similarity).")

    add_heading_section(doc, "2.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 2")
    add_styled_paragraph(doc, 
        "Để hiểu tại sao quy trình chuẩn bị dữ liệu trong ViTrueVoice lại thiết lập các rào cản cực kỳ khắt khe, "
        "người đọc cần nắm vững 5 khái niệm học thuật sau:")

    add_heading_subsection(doc, "2.0.1 Hiện Tượng Rò Rỉ Dữ Liệu (Data Leakage) Trong Machine Learning")
    add_styled_paragraph(doc, 
        "Rò rỉ dữ liệu xảy ra khi thông tin từ tập kiểm thử (Test set) vô tình lọt vào quá trình huấn luyện (Train set). "
        "Trong xử lý tiếng nói, rò rỉ thường xảy ra ở 2 dạng vô hình:\n"
        "1. **Rò rỉ người nói (Speaker Overlap)**: Cùng một người nói xuất hiện ở cả tập Train và Test. Mô hình chỉ việc nhớ âm sắc đặc trưng của người này là đoán đúng, dẫn đến việc khi gặp người lạ hoàn toàn ngoài đời thực thì sụp đổ 100%.\n"
        "2. **Rò rỉ văn bản (Text Overlap)**: Cùng một câu khẩu ngữ xuất hiện ở cả Train và Test. Mô hình học đặc trưng âm vị của từ ngữ thay vì học dấu vết của AI tổng hợp.")

    add_heading_subsection(doc, "2.0.2 Nguyên Lý Của Hệ Thống Tạo Giọng Nói AI (TTS Pipeline)")
    add_styled_paragraph(doc, 
        "Một hệ thống tổng hợp tiếng nói từ văn bản (TTS) hiện đại luôn trải qua 3 chặng cơ bản:\n"
        "1. **Text Normalization / G2P (Grapheme-to-Phoneme)**: Chuyển đổi văn bản chữ viết thành chuỗi âm vị phát âm (ví dụ: '10k' -> 'mười nghìn').\n"
        "2. **Acoustic Model (Mô hình âm học)**: Biến đổi chuỗi âm vị thành biểu diễn phổ trung gian (Mel-spectrogram). Chặng này quyết định cao độ (Pitch), nhịp điệu (Rhythm) và cảm xúc.\n"
        "3. **Vocoder (Bộ giải mã âm thanh)**: Biến đổi Mel-spectrogram thành dạng sóng âm thanh vật lý (Waveform) nghe được qua loa. Vocoder chính là nơi để lại các méo hài vi mô đặc trưng của AI!")

    add_heading_subsection(doc, "2.0.3 Lịch Sử Phát Triển 3 Thế Hệ TTS")
    add_styled_paragraph(doc, 
        "Để đánh giá độ bền của hệ thống, ta cần hiểu sự tiến hóa công nghệ của kẻ tấn công:\n"
        "- **Thế hệ 1 (Ghép nối mẫu - Concatenative TTS)**: Cắt nhỏ các đoạn âm thanh thật của một người rồi ghép lại. Giọng nói giật cục, không tự nhiên, dễ nhận biết bằng tai người.\n"
        "- **Thế hệ 2 (Neural Vocoder hồi quy / Non-autoregressive)**: FastSpeech2, Tacotron2 kết hợp HiFi-GAN. Giọng mượt mà nhưng để lại méo hài chu kỳ dạng lược (comb filter artifacts).\n"
        "- **Thế hệ 3 (Diffusion & Continuous Flow Matching - CFM)**: F5-TTS, VoiceStudio CFM. Tận dụng phương trình vi phân và trường vector để tạo giọng nói với chất lượng biểu cảm vượt trội, sao chép giọng người khác chỉ từ 3 giây tham chiếu (Zero-shot cloning).")

    add_heading_subsection(doc, "2.0.4 Đo Lường Độ Chính Xác Nhận Dạng ASR: Khoảng Cách Levenshtein & WER/CER")
    add_styled_paragraph(doc, 
        "Khoảng cách Levenshtein giữa hai chuỗi ký tự là số phép chèn (Insertion), xóa (Deletion) và thay thế (Substitution) tối thiểu "
        "để biến chuỗi này thành chuỗi kia. "
        "Tỷ lệ lỗi từ (Word Error Rate - WER) và Tỷ lệ lỗi ký tự (Character Error Rate - CER) là thước đo chuẩn để kiểm tra xem "
        "âm thanh do AI tổng hợp có phát âm rõ ràng, chuẩn tiếng Việt hay không (được sử dụng tại Gate 1 của dự án).")

    add_heading_subsection(doc, "2.0.5 Vân Giọng Sinh Trắc (Speaker Embedding) & Độ Tương Đồng Cosine")
    add_styled_paragraph(doc, 
        "Mô hình ECAPA-TDNN chiếu một đoạn âm thanh bất kỳ thành một vector toán học 192 chiều cố định — đại diện cho vân giọng độc nhất của người đó. "
        "Độ tương đồng Cosine giữa hai vector $\\mathbf{u}$ và $\\mathbf{v}$ được tính theo công thức:\n"
        "$$\\text{Cosine Sim}(\\mathbf{u}, \\mathbf{v}) = \\frac{\\mathbf{u} \\cdot \\mathbf{v}}{\\|\\mathbf{u}\\| \\|\\mathbf{v}\\|}$$\n"
        "Nếu $\\text{Cosine Sim} \\ge 0.70$, khoa học khẳng định hai đoạn âm thanh này cùng phát ra từ một người (được sử dụng tại Gate 2 của dự án).")

    # -------------------------------------------------------------------------
    # 2.1 - 2.6 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "2.1 Ba Nguồn Dữ Liệu Nền Tảng Của Đề Tài")
    add_styled_paragraph(doc, "Dự án sử dụng 3 nguồn dữ liệu âm thanh tiếng Việt được chuẩn hóa nghiêm ngặt:")
    add_bullet_item(doc, "Gồm 65 người nói (Nam/Nữ, cả giọng miền Bắc và miền Nam), thu âm chuẩn phòng thu 16kHz WAV mono. Được sử dụng để phân chia tập Train (50 người) và tập Test In-domain (15 người).", "1. Tập VIVOS (Khoa CNTT - ĐH Quốc tế ĐHQG-HCM)")
    add_bullet_item(doc, "Tập dữ liệu mở tiếng Việt thu âm đa dạng từ cộng đồng qua micro điện thoại/laptop (22.97 giờ, 419 người nói), có sẵn nhiễu nền môi trường và đa dạng phương ngữ. Dùng cho tập Dev và Test OOD.", "2. Mozilla Common Voice 8.0 (Tiếng Việt)")
    add_bullet_item(doc, "Gồm 5 sinh viên/thành viên (SPK_0003, SPK_0004, SPK_0005, SPK_0006, SPK_0007), đã ký Phiếu đồng ý thu thập dữ liệu sinh trắc học (Consent Form) theo Luật 91/2025/QH15. Mỗi người thu âm 15-20 câu thoại độc bản, tạo thành 84 clips gốc x 5 biến thể codec = 420 clips bona fide. ĐÂY LÀ BỘ NGHIỆM THU ĐỘC LẬP CHÍNH THỨC CỦA ĐỒ ÁN, NGHIÊM CẤM 100% XUẤT HIỆN TRONG TRAIN/DEV.", "3. Nhóm Tình nguyện viên Nghiệm thu Độc lập (Held-Out Acceptance Volunteers)")

    add_heading_section(doc, "2.2 Ràng Buộc Phân Vùng Chống Rò Rỉ: Speaker-Disjoint & Hard Text-Disjoint")
    add_styled_paragraph(doc, 
        "Một trong những lỗi nghiêm trọng nhất của các nghiên cứu AI nhận diện giọng nói là **rò rỉ dữ liệu (Data Leakage)**, khiến mô hình đạt điểm số cao ảo nhưng sụp đổ trong thực tế. ViTrueVoice thiết lập hai rào chắn toán học tuyệt đối:")
    add_bullet_item(doc, "Một người nói (Speaker ID) xuất hiện ở tập Train thì tuyệt đối KHÔNG ĐƯỢC PHÉP xuất hiện ở tập Dev hay Test. Điều này đảm bảo mô hình không ghi nhớ âm sắc hay ngữ điệu của một người cụ thể.", "Ràng buộc 1: Speaker-Disjoint (Cô lập người nói)")
    add_bullet_item(doc, "Một câu văn bản (Transcript) đã dùng để kiểm thử (Test) thì tuyệt đối KHÔNG ĐƯỢC XUẤT HIỆN trong tập Dev và tập Train. Cơ chế phân bổ bắt buộc đi theo chiều: Test giữ nguyên câu thoại gốc -> Dev lọc bỏ các câu trùng với Test -> Train lọc bỏ toàn bộ các câu trùng với Dev và Test. Thêm vào đó, đoạn âm thanh dùng làm giọng mẫu (Prompt/Reference) hoàn toàn tách biệt khỏi đoạn âm thanh dùng để sinh giả mạo (Target Evaluation).", "Ràng buộc 2: Hard Text-Disjoint (Cô lập văn bản triệt để)")

    add_heading_section(doc, "2.3 Hai Động Cơ Sinh Mẫu Giả Seen TTS (F5-TTS & VieNeu-TTS v3 Turbo)")
    add_styled_paragraph(doc, "Để mô hình học được đa dạng dấu vết tổng hợp giọng nói tiếng Việt, tập huấn luyện tích hợp hai công cụ TTS tiên tiến nhất hiện nay:")
    add_bullet_item(doc, "Động cơ thế hệ mới dựa trên Diffusion Transformer và Flow Matching. F5-TTS có khả năng Zero-shot voice cloning chỉ từ 3-5 giây âm thanh tham chiếu, mô phỏng ngữ điệu và độ biểu cảm tự nhiên rất cao. Dấu vết đặc trưng: Làm mịn quá mức các phụ âm xát (fricatives) và dấu vết nội suy luồng đặc trưng (Flow Matching trajectory smoothing).", "1. F5-TTS-Vietnamese (Diffusion / Flow Matching)")
    add_bullet_item(doc, "Động cơ nén âm học 48kHz sử dụng mạng tích chập kết hợp bộ biến đổi cao độ (Acoustic Pitch Vocoder). Dấu vết đặc trưng: Xuất hiện các méo hài bậc cao dạng lược (comb-filter harmonic artifacts) và hiện tượng rò rỉ pha năng lượng ở dải tần 4.0kHz - 8.0kHz.", "2. VieNeu-TTS v3 Turbo (48kHz Neural Vocoder)")

    add_heading_section(doc, "2.4 Động Cơ Unseen TTS Phục Vụ Kiểm Chứng Giả Thuyết H2 (VoiceStudio CFM)")
    add_styled_paragraph(doc, 
        "Theo STUBBORN_FACT của dự án, để kiểm chứng Giả thuyết H2 (OOD Generalization), công cụ Unseen TTS bắt buộc phải là một công nghệ hoàn toàn chưa từng thấy và phải là **chuẩn Zero-Shot Voice Cloning thực thụ** (sao chép giọng từ đoạn audio mẫu của người khác).")
    add_styled_paragraph(doc, 
        "Dự án sử dụng **VoiceStudio (OmniVoice CFM - Continuous Flow Matching)** làm công cụ Unseen TTS chính thức. Kokoro-TTS (StyleTTS 2) bị loại khỏi bộ nghiệm thu H2 chính thức vì bản chất kiến trúc của nó chỉ là multi-speaker preset, không hỗ trợ Zero-shot clone từ giọng mẫu tùy ý của tình nguyện viên.")

    add_heading_section(doc, "2.5 Bộ Lọc Kiểm Định Chất Lượng 4 Cổng (Label-Free Prosody MultiGate)")
    add_styled_paragraph(doc, 
        "Không phải bất kỳ mẫu âm thanh nào sinh ra từ TTS cũng được đưa vào tập dữ liệu. Để đảm bảo dữ liệu spoof đạt độ chân thực tuyệt đối như giọng người thật, dự án thiết kế bộ lọc tự động 4 cổng (MultiGate):")
    add_bullet_item(doc, "Sử dụng mô hình ASR tiếng Việt (Wav2Vec2) để giải mã lại văn bản từ âm thanh sinh ra. Bắt buộc CER <= 0.08 (8%) và WER <= 0.15 (15%). Loại bỏ ngay các file phát âm ngọng, nuốt từ hoặc bị lặp từ.", "Cổng 1 (ASR Intelligibility Gate)")
    add_bullet_item(doc, "Sử dụng mô hình nhận diện người nói ECAPA-TDNN trích xuất vector đặc trưng 192 chiều. Tính độ tương đồng Cosine giữa giọng mẫu của nạn nhân và giọng do AI nhân bản. Bắt buộc Cosine Similarity >= 0.70 để đảm bảo kẻ lừa đảo đã nhân bản giống giọng nạn nhân.", "Cổng 2 (Speaker Similarity Gate)")
    add_bullet_item(doc, "Phân tích đường cong tần số cơ bản F0 (Pitch contour) bằng thuật toán YIN. Đảm bảo độ lệch chuẩn của F0 nằm trong ngưỡng sinh học tự nhiên (sigma_F0 >= 15 Hz), loại bỏ các giọng nói phẳng lì đơn điệu như robot.", "Cổng 3 (Prosody Naturalness Gate)")
    add_bullet_item(doc, "Kiểm tra độ dài clip (tối thiểu 1.5 giây, tối đa 12.0 giây) và tỷ số tín hiệu trên tạp âm SNR >= 15 dB.", "Cổng 4 (Duration & SNR Gate)")

    add_heading_section(doc, "2.6 Cấu Trúc Manifest Chuẩn 18 Cột & Kho Nghiệm Thu Voice_Final")
    add_styled_paragraph(doc, 
        "Toàn bộ dữ liệu được quản lý đồng bộ qua các tệp CSV Manifest gồm đúng **18 cột dữ liệu tiêu chuẩn**. "
        "Mỗi dòng đại diện cho một bản ghi âm thanh duy nhất, đảm bảo tính truy vết 100% trong khoa học dữ liệu:")

    manifest_cols = [
        ("utt_id", "Mã định danh duy nhất của đoạn âm thanh (Primary Key, ví dụ: SPK0003_01_f5_aac)."),
        ("speaker_id", "Mã định danh người nói (ví dụ: SPK_0003, VIVOSSPK01...). Dùng để đảm bảo Speaker-Disjoint."),
        ("audio_path", "Đường dẫn tương đối chuẩn POSIX tới tệp âm thanh WAV trên ổ đĩa."),
        ("label", "Nhãn phân loại: 'bonafide' (người thật) hoặc 'spoof' (giả mạo AI)."),
        ("subset", "Tập phân vùng: 'train', 'dev' hoặc 'test'."),
        ("engine", "Động cơ tạo ra âm thanh: 'bonafide', 'f5_tts', 'vieneu_tts' hoặc 'voicestudio_cfm'."),
        ("codec", "Bộ nén viễn thông áp dụng: 'clean', 'aac_zalo_76k', 'opus_zalo_24k', 'amr_nb' hoặc 'g711'."),
        ("pre_codec", "Trạng thái nén của audio mẫu gốc trước khi đưa vào pipeline."),
        ("base_utt", "Mã liên kết chéo cặp âm thanh (dùng để đo lường độ suy giảm Paired Deltas)."),
        ("sample_rate", "Tần số lấy mẫu của tệp (chuẩn hóa cố định 16.000 Hz)."),
        ("duration_s", "Độ dài thời gian của đoạn âm thanh (tính bằng giây)."),
        ("num_samples", "Tổng số mẫu âm thanh vật lý (duration_s * sample_rate)."),
        ("text", "Nội dung văn bản câu thoại (dùng để kiểm soát Hard Text-Disjoint)."),
        ("wer", "Tỷ lệ lỗi từ đo được tại Cổng 1 của bộ lọc MultiGate."),
        ("cer", "Tỷ lệ lỗi ký tự đo được tại Cổng 1 của bộ lọc MultiGate."),
        ("spk_sim", "Độ tương đồng vân giọng với người nói gốc đo được tại Cổng 2 (ECAPA-TDNN)."),
        ("f0_std", "Độ biến thiên cao độ âm điệu đo được tại Cổng 3 (YIN Algorithm)."),
        ("sha256", "Mã băm an mật SHA-256 của tệp âm thanh (Đạo đức sinh trắc học & toàn vẹn dữ liệu).")
    ]

    t_m = doc.add_table(rows=len(manifest_cols) + 1, cols=2)
    t_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_m)

    m_hdr = t_m.rows[0]
    set_cell_background(m_hdr.cells[0], "1F497D"); set_cell_background(m_hdr.cells[1], "1F497D")
    set_cell_margins(m_hdr.cells[0], 80, 80, 100, 100); set_cell_margins(m_hdr.cells[1], 80, 80, 100, 100)
    m_hdr.cells[0].width, m_hdr.cells[1].width = Inches(2.0), Inches(4.9)
    p = m_hdr.cells[0].paragraphs[0]; r = p.add_run("Tên Cột (Column)"); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); r.font.name = "Times New Roman"; r.font.size = Pt(9.5)
    p = m_hdr.cells[1].paragraphs[0]; r = p.add_run("Ý Nghĩa & Vai Trò Kỹ Thuật"); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); r.font.name = "Times New Roman"; r.font.size = Pt(9.5)

    for i, (c_name, c_desc) in enumerate(manifest_cols):
        row = t_m.rows[i+1]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = Inches(2.0), Inches(4.9)
        if i % 2 == 0:
            set_cell_background(c0, "F9FAFC"); set_cell_background(c1, "F9FAFC")
        set_cell_margins(c0, 50, 50, 80, 80); set_cell_margins(c1, 50, 50, 80, 80)
        p0 = c0.paragraphs[0]; p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(c_name); r0.bold = True; r0.font.name = "Courier New"; r0.font.size = Pt(8.5); r0.font.color.rgb = RGBColor(192, 0, 0)
        p1 = c1.paragraphs[0]; p1.paragraph_format.space_after = Pt(0); p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(c_desc); r1.font.name = "Times New Roman"; r1.font.size = Pt(9); r1.font.color.rgb = RGBColor(20, 20, 20)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # =========================================================================
    # CHƯƠNG 3
    # =========================================================================
    add_heading_chapter(doc, "Chương 3", "Xử Lý Tín Hiệu Âm Thanh & Công Nghệ Chống Shortcut Âm Học (DSP)")

    add_prerequisite_box(doc, "Chương 3", 
        "Tần số lấy mẫu fs & Định lý Nyquist-Shannon, Hiện tượng Aliasing, Biến đổi Fourier FFT & STFT, "
        "Biểu đồ phổ (Spectrogram) & Formants, Năng lượng RMS & Thang đo dBFS, Chuẩn âm lượng phát thanh EBU R128 (-23 LUFS), "
        "Chuẩn hóa Z-score, Lỗi lượng tử hóa & Rung nhiễu Dithering (RFC 3389 / AES-17), Nén âm thanh mất mát MDCT.")

    add_heading_section(doc, "3.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 3")
    add_styled_paragraph(doc, 
        "Xử lý tín hiệu âm thanh (Digital Signal Processing - DSP) là bước khởi đầu quyết định 80% thành bại của mô hình học máy. "
        "Để hiểu sâu sắc các quyết định thiết kế trong chương này, người học cần nắm vững 6 nguyên lý nền tảng sau:")

    add_heading_subsection(doc, "3.0.1 Tín Hiệu Số Học, Định Lý Nyquist-Shannon & Hiện Tượng Chồng Phổ (Aliasing)")
    add_styled_paragraph(doc, 
        "Âm thanh trong tự nhiên là sóng liên tục (Analog). Khi đi vào máy tính, nó được lấy mẫu (Sampling) rời rạc theo thời gian "
        "với tần số lấy mẫu $f_s$ (Hz).\n"
        "- **Định lý Nyquist-Shannon**: Để khôi phục hoàn hảo một tín hiệu có tần số cao nhất là $f_{\\max}$, "
        "tần số lấy mẫu bắt buộc phải lớn hơn ít nhất 2 lần: $f_s \\ge 2 f_{\\max}$.\n"
        "- **Hiện tượng Chồng Phổ (Aliasing)**: Nếu ta lấy mẫu với tần số không đủ cao, các tần số cao trong âm thanh sẽ bị 'gập ngược' "
        "xuống vùng tần số thấp, tạo ra các tần số ma (Ghost frequencies) làm biến dạng hoàn toàn âm thanh. "
        "Do đó, khi chuyển đổi tần số (Resampling về 16kHz), ta bắt buộc phải dùng bộ lọc thông thấp (Low-pass filter) đa pha (Polyphase filter) "
        "để triệt tiêu mọi tần số trên 8.000 Hz trước khi hạ mẫu.")

    add_heading_subsection(doc, "3.0.2 Miền Thời Gian vs Miền Tần Số: Biến Đổi Fourier (FFT), STFT & Spectrogram")
    add_styled_paragraph(doc, 
        "Dạng sóng thô (Waveform) là tín hiệu ở **miền thời gian** (Biên độ theo Thời gian). Nó cho ta biết lúc nào âm thanh to, lúc nào nhỏ, "
        "nhưng không thể biết được trong đó đang có những nốt nhạc hay tần số nào.\n"
        "- **Biến đổi Fourier (FFT)**: Chiếu toàn bộ tín hiệu sang **miền tần số** (Năng lượng theo Tần số), cho biết các thành phần tần số nhưng mất hoàn toàn thông tin thời gian.\n"
        "- **Biến đổi Fourier thời gian ngắn (STFT)**: Chia nhỏ âm thanh thành các khung ngắn (ví dụ 25ms), dịch chuyển từng bước (hop size 10ms) "
        "và áp dụng FFT lên từng khung. Kết quả là **Biểu đồ phổ (Spectrogram)**: ma trận 2D thể hiện năng lượng vừa theo Thời gian, vừa theo Tần số. "
        "Đây chính là 'bức tranh' mà các mô hình học sâu quan sát để tìm dấu vết giả mạo!")

    add_heading_subsection(doc, "3.0.3 Formants Của Giọng Nói & Năng Lượng Hiệu Dụng RMS")
    add_styled_paragraph(doc, 
        "Khi con người phát âm, luồng khí từ phổi đi qua dây thanh đới tạo ra tần số cơ bản $F_0$ (Pitch). Luồng âm thanh này tiếp tục "
        "cộng hưởng trong khoang miệng và khoang mũi, tạo ra các đỉnh năng lượng phổ gọi là **Formants ($F_1, F_2, F_3$)**. "
        "Formants chính là yếu tố giúp tai người phân biệt được nguyên âm 'A', 'O' hay 'I'.\n"
        "- **Năng Lượng Hiệu Dụng RMS (Root Mean Square)**: Căn bậc hai của trung bình bình phương biên độ tín hiệu. "
        "RMS phản ánh chính xác độ lớn năng lượng thực tế của đoạn âm thanh thay vì chỉ nhìn vào biên độ đỉnh (Peak).")

    add_heading_subsection(doc, "3.0.4 Thang Đo Decibel Toàn Dải (dBFS) & Chuẩn Phát Thanh EBU R128 (-23 LUFS)")
    add_styled_paragraph(doc, 
        "Trong âm thanh số học, giá trị mẫu tối đa không bao giờ vượt quá biên độ 1.0 (chuẩn PCM 16-bit). "
        "Thang đo **dBFS (Decibels relative to Full Scale)** lấy giá trị lớn nhất này làm mốc $0\\text{ dBFS}$. Mọi âm thanh thực tế đều có giá trị âm (ví dụ: $-12\\text{ dBFS}$, $-30\\text{ dBFS}$).\n"
        "- **Chuẩn EBU R128 (-23 LUFS)**: Tai người không nghe các tần số như nhau (tai nhạy cảm nhất ở 2kHz–4kHz và kém nhạy ở âm trầm). "
        "Đơn vị LUFS (Loudness Units relative to Full Scale) tích hợp bộ lọc mô phỏng thính giác K-weighting. "
        "Chuẩn hóa âm thanh về đúng **-23 LUFS** giúp mọi clip âm thanh có độ to cảm nhận đồng nhất tuyệt đối, ngăn chặn mô hình học vẹt độ to.")

    add_heading_subsection(doc, "3.0.5 Lỗi Lượng Tử Hóa & Nghệ Thuật Rung Nhiễu Làm Mềm (Comfort Dithering)")
    add_styled_paragraph(doc, 
        "Khi cắt khoảng lặng hoặc khi âm thanh bị tắt hoàn toàn, giá trị mẫu số học rơi về số 0 tròn trĩnh ($x_i = 0.000000$). "
        "Trong thực tế tự nhiên, không bao giờ có môi trường nào tĩnh lặng tuyệt đối không có hạt nhiễu nhiệt (Thermal noise). "
        "Một chuỗi số 0 kéo dài sẽ tạo thành một **shortcut âm học nguy hiểm**: mô hình AASIST sẽ nhận ra ngay các giá trị 0 tuyệt đối này "
        "và phân loại sai lệch.\n"
        "- Kỹ thuật **Comfort Dithering** (RFC 3389 / AES-17) chủ động rải một lớp nhiễu Gauss cực nhỏ (khoảng $-80\\text{ dBFS}$ đến $-70\\text{ dBFS}$) "
        "vào các vùng phẳng, vừa giúp âm thanh tự nhiên đối với màng nhĩ, vừa ngăn chặn mô hình học các điểm dị biệt toán học.")

    add_heading_subsection(doc, "3.0.6 Bản Chất Cơ Chế Nén Mất Mát Của Kênh Thoại (Lossy Codecs)")
    add_styled_paragraph(doc, 
        "Để truyền giọng nói qua mạng viễn thông băng thông hẹp, các thuật toán nén như Opus, AAC, AMR-NB sử dụng **Mô hình Tâm lý Âm học (Psychoacoustic Model)**. "
        "Chúng tính toán xem những dải tần số nào tai người không nghe thấy (do bị các âm thanh to bên cạnh che lấp - hiện tượng Frequency Masking) "
        "để vứt bỏ hoàn toàn các thông tin đó, đồng thời làm tròn thô bạo (Quantization). "
        "Việc này giúp giảm dung lượng file xuống 10–20 lần nhưng cũng đồng thời xóa sổ các méo hài bậc cao của AI!")

    # -------------------------------------------------------------------------
    # 3.1 - 3.6 Chuyên sâu
    # -------------------------------------------------------------------------
    add_heading_section(doc, "3.1 Chuẩn Hóa 16.000 Hz Mono (Polyphase Resampling)")
    add_styled_paragraph(doc, 
        "Mọi tệp âm thanh đầu vào (bất kể là 44.1kHz, 48kHz, stereo 2 kênh hay 8kHz) đều bắt buộc trải qua pipeline tiền xử lý:")
    add_bullet_item(doc, "Nếu âm thanh là Stereo (2 kênh), tính trung bình cộng hai kênh để chuyển thành Mono 1 kênh: $x_{\\text{mono}} = \\frac{x_L + x_R}{2}$.", "Chuyển đổi Mono")
    add_bullet_item(doc, "Sử dụng bộ lọc đa pha chất lượng cao `soxr_vhq` hoặc `torchaudio.transforms.Resample(orig_sr, 16000)` với bộ lọc Kaiser window. Tuyệt đối không dùng nội suy tuyến tính (Linear interpolation) vì gây hiện tượng méo gấp phổ (Aliasing artifacts).", "Chuyển tần số lấy mẫu 16.000 Hz")

    add_heading_section(doc, "3.2 Cắt Khoảng Lặng Dựa Trên Phân Vị Thứ 20 (RMS P20 Trimming)")
    add_styled_paragraph(doc, 
        "Khoảng lặng đầu và cuối file (Leading/Trailing silence) không mang thông tin sinh trắc học nhưng làm loãng năng lượng tensor đầu vào. "
        "ViTrueVoice áp dụng giải thuật cắt khoảng lặng thích ứng dựa trên phân vị năng lượng thứ 20 (P20):")
    add_bullet_item(doc, "Tính năng lượng hiệu dụng RMS của từng khung âm thanh (Frame size = 512 mẫu, Hop size = 128 mẫu): $\\text{RMS}_t = \\sqrt{\\frac{1}{K} \\sum_{k=0}^{K-1} x[t \\cdot H + k]^2}$.", "Bước 1")
    add_bullet_item(doc, "Tính ngưỡng năng lượng động: $\\text{Threshold} = \\max(\\text{Percentile}_{20}(\\text{RMS}), -50.0\\text{ dBFS})$. "
        "Giải thuật này thông minh hơn ngưỡng cứng cố định (-40 dB): nếu một file có tiếng ồn nền lớn, ngưỡng P20 sẽ tự động nâng lên theo nền nhiễu đó mà không cắt lẹm vào giọng nói thật.", "Bước 2")
    add_bullet_item(doc, "Loại bỏ các khung ở hai đầu có năng lượng nhỏ hơn Threshold, giữ lại vùng giọng nói hữu ích (Voiced segments).", "Bước 3")

    add_heading_section(doc, "3.3 Cố Định Độ Dài 64.000 Mẫu (4.0s): Repeat Padding vs. Zero-Padding")
    add_styled_paragraph(doc, 
        "Kiến trúc Wav2Vec 2.0 và AASIST yêu cầu độ dài tensor đầu vào cố định chính xác là **64.000 mẫu** (tương đương 4,0 giây ở tần số 16kHz). "
        "Khi một đoạn âm thanh ngắn hơn 64.000 mẫu (ví dụ câu thoại chỉ dài 2.5 giây = 40.000 mẫu):")
    add_bullet_item(doc, "Thêm một chuỗi các số 0 vào sau đuôi tín hiệu. "
        "HẬU QUẢ: Tạo ra một bước nhảy gián đoạn biên độ đột ngột tại điểm nối ($x[39999] \\to 0$). Bước nhảy này sinh ra các thành phần tần số cao nhân tạo (Gibbs phenomenon) và tạo ra một vùng năng lượng bằng 0 kéo dài. Bộ lọc đồ thị AASIST sẽ nhận diện đây là dấu vết bất thường giả tạo và phân loại sai.", "Giải pháp ngây thơ: Zero-Padding")
    add_bullet_item(doc, "Sử dụng hàm lặp tuần hoàn `np.tile(x, ceil(64000/N))[:64000]` để nối tiếp chính đoạn âm thanh đó cho đến khi đủ 64.000 mẫu. "
        "ƯU ĐIỂM TUYỆT ĐỐI: Bảo toàn 100% tính liên tục của dạng sóng, giữ nguyên cấu trúc phổ tần số và phân phối năng lượng tự nhiên của người nói, không sinh ra bước nhảy biên độ nhân tạo.", "STUBBORN_FACT ViTrueVoice: Repeat Padding")

    add_callout_box(doc,
        "Khi hội đồng hỏi: 'Tại sao các em dùng Repeat Padding mà không dùng Zero-padding như thông thường?', bạn trả lời: **'Dạ thưa Thầy/Cô, trong xử lý tín hiệu âm thanh và mạng nơ-ron đồ thị (AASIST), đệm số 0 (Zero-padding) sẽ tạo ra một cú nhảy biên độ gián đoạn đột ngột tại điểm giao cắt, đồng thời tạo ra một dải phẳng năng lượng bằng 0 kéo dài. Điều này làm méo mó các đặc trưng phổ STFT và tạo ra shortcut nhân tạo khiến mô hình bị nhầm lẫn. Kỹ thuật Repeat Padding (np.tile) giúp duy trì tính liên tục phổ và bảo toàn phân bố âm học tự nhiên của giọng nói.'**",
        title="BÍ QUYẾT PHẢN BIỆN #2: BẢN CHẤT CỦA REPEAT PADDING")

    add_heading_section(doc, "3.4 Chuẩn Hóa Độ To EBU R128 (-23 LUFS) & Z-Score")
    add_styled_paragraph(doc, 
        "Một trong những nguyên nhân khiến mô hình AI bị học vẹt (shortcut) là sự chênh lệch âm lượng giữa các tập dữ liệu: "
        "mẫu giọng thật thu âm gần micro thì to, trong khi mẫu TTS sinh ra thì nhỏ (hoặc ngược lại). "
        "Để triệt tiêu hoàn toàn shortcut âm lượng, ViTrueVoice áp dụng quy trình chuẩn hóa 2 lớp:")
    add_bullet_item(doc, "Sử dụng chuẩn phát thanh truyền hình châu Âu EBU R128. Thuật toán tích hợp bộ lọc thính giác K-weighting và cửa sổ tích hợp để đo độ to cảm nhận thực tế của con người (Integrated Loudness). Sau đó, nhân toàn bộ dạng sóng với hệ số khuếch đại để đưa độ to về đúng chuẩn **-23 LUFS**.", "Lớp 1: Chuẩn hóa EBU R128")
    add_bullet_item(doc, "Sau khi đưa về -23 LUFS, tín hiệu tiếp tục được chuẩn hóa thống kê đưa kỳ vọng về 0 và phương sai về 1: $x_{\\text{norm}} = \\frac{x - \\mu}{\\sigma + 10^{-7}}$. Điều này giúp tensor đầu vào có phân phối chuẩn, giúp hàm mất mát hội tụ ổn định.", "Lớp 2: Z-Score Normalization")

    add_heading_section(doc, "3.5 Bù Đắp Tiếng Ồn Tiện Nghi Thích Ứng (Adaptive Comfort Dithering — v0.4.7)")
    add_styled_paragraph(doc, 
        "Trong phiên bản hoàn thiện v0.4.7, khi kiểm thử trực tiếp giọng thu âm từ các micro laptop/điện thoại có tính năng khử nhiễu tự động (AI Noise Suppression), "
        "các vùng khoảng lặng giữa các từ thường bị micro ép về giá trị phẳng tuyệt đối ($0.0000$). "
        "Hệ thống ViTrueVoice tích hợp kỹ thuật bù đắp tiếng ồn tiện nghi thích ứng:")
    add_bullet_item(doc, "Nếu phát hiện vùng phẳng kéo dài > 100 mẫu có giá trị bằng 0, thuật toán tự động rải một lớp nhiễu tam giác hoặc Gaussian siêu mịn (Adaptive Dithering) có biên độ $-75\\text{ dBFS}$ tuân thủ tiêu chuẩn ITU-T RFC 3389 và AES-17.", "Cơ chế Dithering")
    add_bullet_item(doc, "Kỹ thuật này giúp giải quyết dứt điểm hiện tượng nhận diện nhầm người thật thành deepfake (BPCER = 0%) khi người dùng thu âm trong phòng kín có micro chống ồn.", "Ý nghĩa")

    add_heading_section(doc, "3.6 Bộ Suy Giảm Nén Kênh Thoại & Tăng Cường Âm Học RawBoost")
    add_styled_paragraph(doc, 
        "Để huấn luyện mô hình có sức đề kháng cao trước các cuộc gọi lừa đảo thực tế (Kiểm chứng Giả thuyết H1), "
        "ViTrueVoice tích hợp hai kỹ thuật biến dạng dữ liệu (Data Augmentation) mạnh mẽ trực tiếp trong quá trình huấn luyện:")
    add_bullet_item(doc, "Mô phỏng chân thực các thuật toán nén viễn thông bằng cách gọi FFmpeg in-memory: "
        "(1) Zalo Profile A: AAC-LC 76kbps, 48kHz; "
        "(2) Zalo Profile B: Opus 24kbps OGG; "
        "(3) Di động GSM: AMR-NB 12.2kbps, bóp tần số về 8.000 Hz; "
        "(4) Điện thoại bàn PSTN: G.711 A-law 64kbps, 8.000 Hz.", "1. Telephony Codec Simulator")
    add_bullet_item(doc, "Mô phỏng các méo dạng tuyến tính và phi tuyến của micro thu âm và loa phát: "
        "(1) Nhánh 1: Nhiễu méo cộng tuyến tính (Linear additive noise); "
        "(2) Nhánh 2: Méo pha và tích chập phi tuyến (Convolutive noise / Room impulse response); "
        "(3) Nhánh 3: Tạp âm dải tần không dừng (Non-stationary colored noise). "
        "RawBoost giúp giảm thêm **13.8% – 22.1% tỷ lệ lỗi EER** trên toàn bộ các tập kiểm thử.", "2. RawBoost Augmentation")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)
