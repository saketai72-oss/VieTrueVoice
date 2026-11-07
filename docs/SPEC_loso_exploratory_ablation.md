# Đặc Tả Thử Nghiệm Thăm Dò Leave-One-Speaker-Out (LOSO 4 Folds)

> **Mã văn bản**: `SPEC_loso_exploratory_ablation.md`  
> **Trạng thái**: Pre-registered (Khóa trước khi thực thi)  
> **Phiên bản**: 1.1.0 — 2026-11-07  
> **Mục tiêu**: Đánh giá thực nghiệm hiệu ứng chuyển giao liên người nói (Inter-speaker Transfer Effect) khi bổ sung dữ liệu tình nguyện viên vào đầu phân loại, kiểm chứng giả thuyết về giới hạn của việc bổ sung dữ liệu theo cá nhân.

---

## Lịch Sử Thay Đổi & Khóa Băm (Changelog & Hashes)

| Phiên bản | SHA-256 Hash | Ngày | Nội dung thay đổi & Ghi chú minh bạch |
|---|---|---|---|
| **v1.0.0** | `006aec45317863acedbb3f82313f84daddf451f0a1fc69cd407d0e5d8ef11381` | 2026-11-07 | Bản khởi tạo đầu tiên của đặc tả tiên nghiệm. |
| **v1.1.0** | `8cc8e7eaf1171f1bcd7319486d6baabbbc3833a63c806dd462a7dd959603c6bb` | 2026-11-07 | 1. Phân cấp Cấu hình 1 (Standard: $5\times 10^{-5}$) là **Primary**, Cấu hình 2 (Aggressive: $2\times 10^{-4}$) là **Secondary**. Tiêu chí thành công $\ge 3/4$ folds chỉ áp dụng cho Cấu hình 1; Cấu hình 2 không dùng để cứu kết quả âm.<br>2. Bổ sung phép đo Giả thuyết H2 trên Unseen TTS (`VieNeu-TTS` clone của chính người bị giữ lại) tại $\theta_{\text{cal}}$ vào nhóm kết quả phụ để kiểm tra đánh đổi bảo mật.<br>3. Khóa điểm trích xuất cache tại `encoder.last_hidden_state` (768 chiều), encoder ở `eval()`. Bổ sung bằng chứng kiểm định tương đương số học trên 100 tệp (FP32 lệch $0,000000$, FP16 lệch tối đa $0,002673 \le 0,02$).<br>4. Tiêu chí #3 làm rõ là $+15$ điểm phần trăm tuyệt đối ($+15$ percentage points absolute).<br>5. Xác thực Hard Text-Disjoint giữa các fold tình nguyện viên (0 câu trùng lặp).<br>6. Đổi quy ước gọi tên mô hình chuẩn theo mã băm/mô tả: `ckpt-49k-pitchaug` và `ckpt-50.6k-deep`.<br>*(Ghi chú minh bạch: Bản v1.1.0 được chốt trước khi chạy bất kỳ fold huấn luyện nào của LOSO, nhưng diễn ra sau khi đã kiểm tra kết quả chẩn đoán của `ckpt-50.6k-deep`).* |

---

## 1. Khóa Cứng Định Danh & Mã Băm (Cryptographic Locks)

| Thành phần | Đường dẫn | SHA-256 Hash | Tên gọi chuẩn mô tả | Ghi chú kỹ thuật |
|---|---|---|---|---|
| **Checkpoint Baseline (V4)** | `out/best_model_B_zalo.pt` | `5b566d925bca1f79489a46aa6a390b8f4ffe284d1fe235140a529a1ac1536243` | `ckpt-49k-pitchaug` | 94.83M params, AM-Softmax ($s=30, m=0.20$), pitch-aug ON |
| **Train Manifest Gốc (V4)** | `data/manifests_zalo/train_zalo_49k.csv` | `f918735e6e1475e5ab6883fb083d8f269a1ee65659b1b8c1587bb01b2e04b121` | `train_zalo_49k` | Đúng 49.085 dòng (45.425 bona, 3.660 spoof) |
| **Dev Manifest Chuẩn** | `data/manifests_zalo/dev_zalo.csv` | `2fbb18b9f241ee46bf666bc74a93805220da7fb2ea2b100ab121aa2aa3e2f690` | `dev_zalo` | Đúng 11.450 dòng (10.490 bona, 960 spoof) |
| **Checkpoint Đối Chứng (V5 Local)** | `out/zalo_b_zalo_v5_local/best_model.pt` | `85cd82cc2fc9473133254696b51c54c8e8281c77bcdf266838921a0a2a533ec3` | `ckpt-50.6k-deep` | 50.585 dòng (thêm 1.500 clip F0 trầm), AM-Softmax ($m=0.35$), pitch-aug OFF |

### Thống kê chuẩn trên Train Manifest 49.085 dòng
- Tổng số mẫu: $49.085$ dòng ($45.425$ bona fide, $3.660$ spoof).
- Tỷ lệ tệp có độ dài $> 4,0$ giây: $15.532 / 49.085$ ($31,64\%$).
- Phân bố codec: $9.817$ clean, $9.817$ g711, $9.817$ amr, $9.817$ aac_zalo, $9.817$ opus_zalo.

---

## 2. Số Lượng Tham Số & Cơ Chế Huấn Luyện

- **Tổng số tham số mô hình**: $94.830.662$ tham số.
- **Backbone encoder (`model.frontend.encoder`)**: Đóng băng hoàn toàn (`requires_grad = False`, $94.371.712$ tham số).
- **Số tham số huấn luyện thực tế (`requires_grad = True`)**: **$458.950$ tham số**, gồm:
  - Tầng chiếu đặc trưng `model.frontend.proj`: $98.432$ tham số (chiếu từ chiều $768 \rightarrow 128$).
  - Backend phân loại AASIST: $360.518$ tham số (gồm $2$ khối ResBlock2d, đồ thị không gian GAT-s, đồ thị thời gian GAT-t, $2$ khối HS-GAL và Linear Classifier).
- **Điểm trích xuất Feature Caching**: Bắt buộc trích xuất tại ngõ ra của encoder: `h = model.frontend.encoder(wav).last_hidden_state` (kích thước `[B, 199, 768]`), nằm trước tầng chiếu `frontend.proj`.
  - **Trạng thái Encoder khi cache**: Bắt buộc đặt `model.frontend.encoder.eval()` để triệt tiêu hoàn toàn dropout.
  - **Kiểm định tương đương số học**: Đã kiểm tra đối chiếu luồng End-to-End trực tiếp so với luồng Feature Caching trên 100 tệp ngẫu nhiên của Dev Zalo:
    - FP32 Cache: Sai lệch tối đa $= 0,00000000$ (đồng nhất tuyệt đối).
    - FP16 Cache: Sai lệch tối đa $= 0,002673$ (sai lệch trung bình $0,000569$), nhỏ hơn rất nhiều so với ngưỡng kiểm định $\le 0,02$.
- **Ước tính dung lượng lưu trữ (Storage Budget)**:
  - Mỗi mẫu âm thanh: $199 \times 768 \times 2$ bytes (FP16) $\approx 298,5$ KB.
  - Toàn bộ Dev Zalo (11.450 mẫu): $\approx 3,34$ GB (FP16).
  - Dev Spoof $\times 11$ offsets (10.560 mẫu): $\approx 3,15$ GB (FP16).
  - Dữ liệu tình nguyện viên (6 người $\times 5$ codecs): $\approx 0,26$ GB.
  - Replay buffer (2.400 mẫu huấn luyện): $\approx 0,72$ GB.
  - Tổng dung lượng lưu trữ đệm ước tính: $\approx 7,47$ GB (hoàn toàn an toàn trên phân vùng đĩa $119$ GB trống).

---

## 3. Thiết Kế 4 Folds & Phân Bổ Dữ Liệu

Chỉ chạy 4 folds trên các người nói phát sinh lỗi ở baseline `ckpt-49k-pitchaug`:

```
Fold 1: Giữ SPK_0001 (15 câu gốc) | Train: Replay + {SPK_0003, 0004, 0005, 0006, 0007}
Fold 2: Giữ SPK_0003 (20 câu gốc) | Train: Replay + {SPK_0001, 0004, 0005, 0006, 0007}
Fold 3: Giữ SPK_0004 (14 câu gốc) | Train: Replay + {SPK_0001, 0003, 0005, 0006, 0007}
Fold 4: Giữ SPK_0006 (10 câu gốc) | Train: Replay + {SPK_0001, 0003, 0004, 0005, 0007}
```

### Kiểm Tra Hard Text-Disjoint Giữa Các Fold
- Bắt buộc kiểm tra trước khi thực thi: Tập văn bản (`transcript`) của người nói bị giữ lại (held-out) trong mỗi fold hoàn toàn không trùng lặp với bất kỳ câu thoại nào của các người nói trong tập fine-tuning. Đã kiểm định thực tế qua bộ metadata: số cặp văn bản trùng lặp giữa 6 tình nguyện viên bằng **0 tuyệt đối**.

### Thành phần Mini-batch (kích thước batch = 8)
- $4$ mẫu tình nguyện viên: $2$ mẫu bona fide + $2$ mẫu spoof clone F5-TTS (nghiêm cấm tuyệt đối $100\%$ VieNeu-TTS để bảo toàn tính độc lập của Giả thuyết H2).
- $4$ mẫu Replay Buffer: $2$ mẫu bona fide + $2$ mẫu spoof lấy ngẫu nhiên từ manifest chuẩn 49.085 dòng.

### Nhánh Đối Chứng (Replay-only Control)
- Chạy song song cho từng fold và từng seed: cùng số bước huấn luyện, cùng siêu tham số, nhưng mini-batch gồm $4$ bona fide + $4$ spoof đều lấy từ Replay Buffer (không chứa dữ liệu của bất kỳ tình nguyện viên nào).

---

## 4. Cấu Hình Siêu Tham Số Tiên Nghiệm (Pre-registered Configurations)

Cả hai cấu hình đều được chỉ định rõ vai trò và chạy song song; kết quả của cả hai phải được báo cáo đối chiếu đầy đủ, nghiêm cấm lựa chọn kết quả thiên vị (cherry-picking):

| Tham số | Cấu hình 1 (Standard Head Tuning — Primary) | Cấu hình 2 (Aggressive Head Adaptation — Secondary) |
|---|---|---|
| **Bộ tối ưu** | AdamW ($\beta_1=0.9, \beta_2=0.999$, weight_decay=$10^{-4}$) | AdamW ($\beta_1=0.9, \beta_2=0.999$, weight_decay=$10^{-4}$) |
| **Learning Rate** | $5 \times 10^{-5}$ cố định | $2 \times 10^{-4}$ cố định |
| **Số bước huấn luyện ($N$)** | $600$ steps (tương đương 4.800 lượt mẫu nạp qua head) | $600$ steps |
| **Kích thước Batch** | 8 | 8 |
| **Số Seeds** | 3 seeds: `42`, `123`, `2026` | 3 seeds: `42`, `123`, `2026` |
| **Vai trò pháp lý** | **Quyết định chính** cho tiêu chí thành công | **Tham chiếu phụ**, không dùng để cứu kết quả âm |

---

## 5. Thước Đo & Tiêu Chí Thành Công Tiên Nghiệm

### Đơn vị thống kê: Câu thoại gốc (`base_utt`)
Mỗi câu thoại được lấy trung bình điểm qua các phiên bản codec để triệt tiêu phụ thuộc nội bộ:
$$s_{\text{utt}} = \frac{1}{|C|} \sum_{c \in C} s(u_c)$$

### Độ lệch điểm có kiểm soát (Controlled Delta):
$$\Delta s_{\text{utt}} = s_{\text{utt}}^{\text{exp}} - s_{\text{utt}}^{\text{replay}}$$

### Tiêu chí định lượng thành công (Success Criteria cho Cấu hình 1 - Primary):
1. **Mức tăng trung bình**: $\overline{\Delta s} \ge +3,0$ điểm trên tập câu gốc của người bị giữ lại.
2. **Khoảng tin cậy Bootstrap**: Thực hiện $1.000$ lượt tái lấy mẫu Bootstrap theo câu thoại; cận dưới khoảng tin cậy $95\%$ phải dương: $\text{CI}_{95\%, \text{lower}}(\overline{\Delta s}) > 0$.
3. **Hiệu quả lật nhãn tại ngưỡng hiệu chỉnh**:
   - Ngưỡng $\theta_{\text{cal}}$ được tính độc lập trên Dev cho từng checkpoint theo điều kiện $\text{BPCER}_{\text{Dev}} \le 1,0\%$.
   - Tỷ lệ câu gốc vượt ngưỡng: $\text{Rate}(s_{\text{utt}} > \theta_{\text{cal}})$ tăng ít nhất **$+15$ điểm phần trăm tuyệt đối (+15 percentage points absolute)** so với baseline (ví dụ từ $0\%$ lên $\ge 15\%$, hoặc từ mức baseline $P_0$ lên $P_0 + 15\%$).
4. **Ràng buộc an ninh không thoái lui**:
   - Dev EER trên 11.450 mẫu không vượt quá $2,05\%$ (baseline `ckpt-49k-pitchaug` là $1,88\%$).
   - APCER@$\theta_{\text{cal}}$ trên Dev Spoof không tăng quá $+1,5\%$ danh định và không tăng quá $+3,0\%$ worst-case (qua 11 offsets).
5. **Quy tắc tổng hợp 4 Folds**: Thí nghiệm chỉ được tuyên bố "có tín hiệu chuyển giao tổng quát hóa" khi có ít nhất **$3/4$ folds** của **Cấu hình 1 (Standard)** thỏa mãn đồng thời các điều kiện trên. Cấu hình 2 (Aggressive) chỉ báo cáo kèm theo, không được sử dụng để đảo ngược hay cứu vãn kết quả nếu Cấu hình 1 thất bại.

### Nhóm Thước Đo Phụ — Đánh Đổi Bảo Mật Giả Thuyết H2 (Unseen TTS & Unseen Speaker)
Với mỗi fold (người nói bị giữ lại), đánh giá tỷ lệ tấn công lọt lưới trên các clip clone VieNeu-TTS (Unseen TTS) của chính người đó tại ngưỡng $\theta_{\text{cal}}$:
$$\text{APCER}_{\text{H2, held-out}}(\theta_{\text{cal}}) = \frac{1}{|V_{\text{held-out}}|} \sum_{v \in V_{\text{held-out}}} \mathbf{1}(s(v) > \theta_{\text{cal}})$$
- **Nguyên tắc đánh đổi**: Nếu fine-tuning làm giảm BPCER của người nói nhưng lại làm tăng $\text{APCER}_{\text{H2}}$, đây là tổn hại an ninh (security trade-off) bắt buộc phải báo cáo và phân tích rõ trong kết luận.

---

## 6. Giới Hạn Phương Pháp Luận
Kết luận của thử nghiệm LOSO 4 folds này hoàn toàn mang tính chất **thăm dò giả thuyết (exploratory ablation)** nhằm đo lường hiệu ứng chuyển giao liên người nói trong tập dữ liệu sẵn có; tuyệt đối **không thay thế** cho việc nghiệm thu độc lập trên một nhóm tình nguyện viên mới chưa từng xuất hiện.
