# Đặc Tả Thử Nghiệm Thăm Dò Leave-One-Speaker-Out (LOSO 4 Folds)

> **Mã văn bản**: `SPEC_loso_exploratory_ablation.md`  
> **Trạng thái**: Completed & Verified (Đã hoàn tất thực thi & Kiểm chứng thực nghiệm)  
> **Phiên bản**: 1.2.1 — 2026-11-07  
> **Mục tiêu**: Đánh giá thực nghiệm hiệu ứng chuyển giao liên người nói (Inter-speaker Transfer Effect) khi bổ sung dữ liệu tình nguyện viên vào đầu phân loại, kiểm chứng giả thuyết về giới hạn của việc bổ sung dữ liệu theo cá nhân.

---

## Lịch Sử Thay Đổi & Khóa Băm (Changelog & Hashes)

| Phiên bản | SHA-256 Hash | Ngày | Nội dung thay đổi & Ghi chú minh bạch |
|---|---|---|---|
| **v1.0.0** | `006aec45317863acedbb3f82313f84daddf451f0a1fc69cd407d0e5d8ef11381` | 2026-11-07 | Bản khởi tạo đầu tiên của đặc tả tiên nghiệm. |
| **v1.1.0** | `8cc8e7eaf1171f1bcd7319486d6baabbbc3833a63c806dd462a7dd959603c6bb` | 2026-11-07 | 1. Phân cấp Cấu hình 1 (Standard: $5\times 10^{-5}$) là **Primary**, Cấu hình 2 (Aggressive: $2\times 10^{-4}$) là **Secondary**. Tiêu chí thành công $\ge 3/4$ folds chỉ áp dụng cho Cấu hình 1; Cấu hình 2 không dùng để cứu kết quả âm.<br>2. Bổ sung phép đo Giả thuyết H2 trên Unseen TTS (`VieNeu-TTS` clone của chính người bị giữ lại) tại $\theta_{\text{cal}}$ vào nhóm kết quả phụ để kiểm tra đánh đổi bảo mật.<br>3. Khóa điểm trích xuất cache tại `encoder.last_hidden_state` (768 chiều), encoder ở `eval()`. Bổ sung bằng chứng kiểm định tương đương số học trên 100 tệp (FP32 lệch $0,000000$, FP16 lệch tối đa $0,002673 \le 0,02$).<br>4. Tiêu chí #3 làm rõ là $+15$ điểm phần trăm tuyệt đối ($+15$ percentage points absolute).<br>5. Xác thực Hard Text-Disjoint giữa các fold tình nguyện viên (0 câu trùng lặp).<br>6. Đổi quy ước gọi tên mô hình chuẩn theo mã băm/mô tả: `ckpt-49k-pitchaug` và `ckpt-50.6k-deep`.<br>*(Ghi chú minh bạch: Bản v1.1.0 được chốt trước khi chạy bất kỳ fold huấn luyện nào của LOSO, nhưng diễn ra sau khi đã kiểm tra kết quả chẩn đoán của `ckpt-50.6k-deep`).* |
| **v1.2.0** | `2f324dca0cf713c1f0090deade41be3a9a2f1eac8c3f4ca30e366c66c7926ca7` | 2026-11-07 | Hoàn tất thực thi toàn bộ 48 lượt chạy (4 folds $\times$ 2 configs $\times$ 3 seeds $\times$ 2 branches). Cập nhật bảng kết quả thực nghiệm chi tiết và xác nhận bác bỏ hoàn toàn Giả thuyết chuyển giao liên người nói (0/4 folds đạt). |
| **v1.2.1** | `591956e4abf812bd77067599e319d7cafaa3a20af74aeb5ff437a282d7f9fa16` | 2026-11-07 | Chuẩn hóa kết luận & bổ sung đối chứng: 1. Bổ sung đối chứng nhánh Replay-only và mức đóng góp ròng của dữ liệu tình nguyện viên; 2. Bổ sung baseline và cỡ mẫu $k/N$ cho H2 VieNeu-TTS; 3. Ghi nhận hiệu ứng trần (ceiling effect) tại Fold 3 và 4; 4. Chuẩn hóa kết luận: chuyển giao dương trên người bị giữ lại ($\Delta s > 0$, pass rate tăng 10–49 pp) nhưng đánh đổi bằng suy giảm an ninh (Dev EER và APCER vượt ngưỡng). |

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

---

## 7. Báo Cáo Kết Quả Thực Nghiệm Toàn Diện (48 Lượt Chạy)

Thực hiện vào: **2026-11-07 20:30:48** trên GPU NVIDIA GeForce RTX 3050 Laptop GPU.  
Baseline Checkpoint: `out/best_model_B_zalo.pt` (`ckpt-49k-pitchaug`, SHA-256: `5b566d925bca1f79489a46aa6a390b8f4ffe284d1fe235140a529a1ac1536243`).  
- Baseline Dev Zalo: $\text{EER} = 1,90\%$, $\theta_{\text{cal}} = -0,7419$, $\text{APCER}_{\text{nom}} = 4,27\%$, $\text{APCER}_{\text{worst}} = 7,60\%$ (mức dịch cố định xấu nhất 0.5s; mô hình đe dọa gộp cực đại theo từng mẫu đạt $11,15\%$).

### Bảng Kết Quả Cấu Hình 1 (Standard Head Tuning — Primary, Quyết Định Chính)

| Fold | Người bị giữ lại | $P_0$ Base | Mean $\Delta s$ | $\text{CI}_{95\%, \text{lower}}$ | Pass Rate (Exp) | Pass Rate (Rep) | Đóng góp ròng ($\Delta$pp) | Dev EER (Exp / Rep) | APCER Nom (Exp / Rep) | APCER Worst (Exp / Rep) | H2 VieNeu [Base $\to$ Exp] ($k/N$) | Đạt Cả 4 Tiêu Chí? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Fold 1** | `SPK_0001` | $0,0\%$ | $+5,00$ | $+3,11$ | $24,4\%$ | $4,4\%$ | $+20,0$ pp | $2,37\%$ / $2,15\%$ | $6,70\%$ / $4,86\%$ | $10,87\%$ / $8,30\%$ | $0,00\% \to 0,00\%$ ($0/50$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 2** | `SPK_0003` | $60,0\%$ | $+1,86$ | $+0,07$ | $76,7\%$ | $65,0\%$ | $+11,7$ pp | $2,58\%$ / $2,15\%$ | $8,19\%$ / $5,03\%$ | $15,38\%$ / $8,12\%$ | $4,00\% \to 12,00\%$ ($3 \to 9 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 3** | `SPK_0004` | $85,7\%$ | $+5,20$ | $+4,06$ | $100,0\%$ | $95,2\%$ | $+4,8$ pp | $2,82\%$ / $2,12\%$ | $8,58\%$ / $5,00\%$ | $14,83\%$ / $8,23\%$ | $14,67\% \to 25,78\%$ ($11 \to 19,3 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 4** | `SPK_0006` | $90,0\%$ | $+2,87$ | $+2,07$ | $100,0\%$ | $100,0\%$ | $+0,0$ pp | $2,81\%$ / $2,17\%$ | $9,58\%$ / $4,97\%$ | $14,44\%$ / $8,23\%$ | $36,00\% \to 45,78\%$ ($27 \to 34,3 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |

- **Kết quả tổng hợp**: **$0/4$ folds** đạt tiêu chuẩn tiên nghiệm.
- **Quy tắc Rule 5**: Thất bại ($0/4 < 3/4$).

### Bảng Kết Quả Cấu Hình 2 (Aggressive Head Adaptation — Secondary, Tham Chiếu Phụ)

| Fold | Người bị giữ lại | $P_0$ Base | Mean $\Delta s$ | $\text{CI}_{95\%, \text{lower}}$ | Pass Rate (Exp) | Pass Rate (Rep) | Đóng góp ròng ($\Delta$pp) | Dev EER (Exp / Rep) | APCER Nom (Exp / Rep) | APCER Worst (Exp / Rep) | H2 VieNeu [Base $\to$ Exp] ($k/N$) | Đạt Cả 4 Tiêu Chí? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Fold 1** | `SPK_0001` | $0,0\%$ | $+13,42$ | $+10,78$ | $48,9\%$ | $13,3\%$ | $+35,6$ pp | $3,01\%$ / $2,26\%$ | $8,58\%$ / $5,38\%$ | $12,81\%$ / $8,89\%$ | $0,00\% \to 0,00\%$ ($0/50$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 2** | `SPK_0003` | $60,0\%$ | $+5,04$ | $+2,66$ | $83,3\%$ | $71,7\%$ | $+11,7$ pp | $3,32\%$ / $2,44\%$ | $9,79\%$ / $6,67\%$ | $15,03\%$ / $9,90\%$ | $4,00\% \to 17,78\%$ ($3 \to 13,3 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 3** | `SPK_0004` | $85,7\%$ | $+4,24$ | $+2,17$ | $100,0\%$ | $95,2\%$ | $+4,8$ pp | $3,54\%$ / $2,59\%$ | $11,84\%$ / $6,39\%$ | $17,08\%$ / $9,13\%$ | $14,67\% \to 28,44\%$ ($11 \to 21,3 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |
| **Fold 4** | `SPK_0006` | $90,0\%$ | $+7,47$ | $+5,68$ | $100,0\%$ | $100,0\%$ | $+0,0$ pp | $3,18\%$ / $2,51\%$ | $11,46\%$ / $6,42\%$ | $14,24\%$ / $10,62\%$ | $36,00\% \to 49,33\%$ ($27 \to 37,0 / 75$) | ❌ **KHÔNG** ($0/3$ seeds) |

- **Kết quả tổng hợp**: **$0/4$ folds** đạt tiêu chuẩn.

### Đối Chiếu Nhánh Đối Chứng Replay-Only & Mức Đóng Góp Ròng Của Dữ Liệu Tình Nguyện Viên

Nhánh đối chứng Replay-only (huấn luyện trên $4.800$ mẫu replay buffer lấy từ tập Train Zalo, không chứa dữ liệu tình nguyện viên) cho phép tách biệt tác động của quá trình fine-tune và tác động riêng của dữ liệu tình nguyện viên:
1. **Quá trình fine-tune đầu phân loại (Replay-only)**: Làm Dev EER tăng nhẹ từ $1,90\%$ lên trung bình $2,15\%$ ($+0,25$ pp) và APCER danh định tăng từ $4,27\%$ lên trung bình $4,96\%$ ($+0,69$ pp).
2. **Mức đóng góp riêng của dữ liệu tình nguyện viên ($\text{Metric}_{\text{exp}} - \text{Metric}_{\text{rep}}$)**:
   - Làm tăng điểm số và tỷ lệ vượt ngưỡng của người bị giữ lại: $\Delta s$ dương ở cả 4 fold ($+1,86$ đến $+5,20$ điểm), đóng góp thêm $0,0$ đến $+20,0$ điểm phần trăm vào tỷ lệ vượt ngưỡng của người bị giữ lại so với chỉ fine-tune trên replay buffer.
   - Nhưng đồng thời gây suy giảm an ninh tổng quát: Dev EER tăng thêm $+0,22$ đến $+0,70$ pp (trung bình $+0,50$ pp, đưa Dev EER lên $2,37\%–2,82\%$); APCER danh định tăng thêm $+1,84$ đến $+4,62$ pp (trung bình $+3,30$ pp); và APCER worst-case tăng thêm $+2,57$ đến $+7,26$ pp (trung bình $+5,66$ pp).

### Ghi Nhận Giới Hạn & Hiệu Ứng Trần (Ceiling Effect)

1. **Hiệu ứng trần trong tiêu chí đã đăng ký trước**: Ở Fold 3 (`SPK_0004`, $P_0 = 85,7\%$) và Fold 4 (`SPK_0006`, $P_0 = 90,0\%$), mức cải thiện tối đa để đạt trần $100\%$ lần lượt chỉ là $+14,3$ pp và $+10,0$ pp. Do đó, tiêu chí cố định $\Delta \text{pp} \ge +15,0$ pp là bất khả thi về mặt số học ngay từ đầu. Dù cả hai fold đều đạt trần $100,0\%$ vượt ngưỡng, kết luận $0/4$ folds đạt vẫn giữ nguyên vì ràng buộc an ninh Dev EER và APCER đều bị vi phạm.
2. **Khác biệt Baseline cục bộ và Kaggle**: Ngưỡng $\theta_{\text{cal}} = -0,7419$ và Dev EER $1,90\%$ phản ánh độ lệch mã hóa proxy của bộ FFmpeg cục bộ (lệch trung bình $0,2$–$0,4$ điểm đã xác minh). Giá trị APCER worst-case $7,60\%$ đo lường điều kiện một mức dịch cố định xấu nhất (offset = 0.50s), trong khi $11,15\%$ thuộc mô hình tấn công đối kháng gộp cực đại theo từng mẫu (sample-level max-pooling).

### Kết Luận Khoa Học

Trong thí nghiệm thăm dò LOSO 4 fold (48 lượt chạy, đăng ký trước), fine-tune đầu phân loại bằng dữ liệu các tình nguyện viên khác làm tăng điểm của người bị giữ lại (cận dưới CI 95% của $\Delta s$ dương ở cả 4 fold, tỷ lệ vượt ngưỡng tăng 10–49 điểm phần trăm) nhưng làm Dev EER tăng từ $1,90\%$ lên $2,37\%–2,82\%$ (cấu hình chính) và APCER danh định tăng 2,4–5,3 điểm phần trăm, nên không fold nào đạt toàn bộ tiêu chí. Chuyển giao là dương trên người bị giữ lại nhưng phải đánh đổi bằng việc suy giảm độ an toàn tổng quát (Dev EER và APCER vượt ngưỡng). Đây là kết quả thăm dò trên 4 người trong tập dữ liệu sẵn có, củng cố quyết định giữ nguyên bộ trọng số `ckpt-49k-pitchaug` và không thay thế cho việc nghiệm thu độc lập trên một nhóm tình nguyện viên mới.
