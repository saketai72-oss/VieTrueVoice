# ARCH_aws-cost-and-runbook — Dự Toán Chi Phí Đám Mây AWS & Sổ Tay Xử Lý Sự Cố Runbook (W08)

---

## 1. Kiến Trúc Hạ Tầng AWS & Dự Toán Chi Phí (3 Quy Mô Người Dùng)

Căn cứ chứng chỉ **AWS Academy Cloud Architecting (100% Complete)** và số đo thực nghiệm độ trễ $P_{50} = 66.3\text{ ms}$, hạ tầng VieTrueVoice được thiết kế tối ưu trên AWS Region Singapore (`ap-southeast-1`):

| Hạng mục dịch vụ AWS | Quy mô 1: 100 User/ngày (~500 reqs/ngày) | Quy mô 2: 1.000 User/ngày (~10.000 reqs/ngày) | Quy mô 3: 10.000 User/ngày (~200.000 reqs/ngày) |
|---|---|---|---|
| **1. Compute (AI Core)** | `t3.medium` (CPU ONNX) — **$30.37 / tháng** | `g4dn.xlarge` (Spot Instance $0.158/h) — **$113.76 / tháng** | Auto Scaling 2–4x `g4dn.xlarge` (Spot + On-Demand) — **$379.20 / tháng** |
| **2. API & Bot Server** | Chạy chung trên compute — **$0.00** | `t3.small` riêng biệt — **$15.18 / tháng** | 2x `t3.medium` đằng sau ALB — **$60.74 / tháng** |
| **3. S3 Storage & Lifecycle** | S3 Standard 5GB — **$0.12 / tháng** | S3 Standard 50GB + Lifecycle 24h — **$1.20 / tháng** | S3 Standard 500GB + Lifecycle 24h — **$12.00 / tháng** |
| **4. Network & Load Balancer** | Băng thông miễn phí 100GB — **$0.00** | Application Load Balancer — **$18.50 / tháng** | ALB + Data Transfer 1TB — **$98.50 / tháng** |
| **5. Giám sát & An mật** | CloudWatch Free Tier — **$0.00** | CloudWatch Logs + Alarms — **$5.00 / tháng** | AWS WAF + CloudWatch Pro — **$25.00 / tháng** |
| **TỔNG CHI PHÍ (USD)** | **$30.49 / tháng** | **$153.64 / tháng** | **$575.44 / tháng** |
| **TỔNG CHI PHÍ (VNĐ)** | **≈ 774.000 VNĐ / tháng** | **≈ 3.902.000 VNĐ / tháng** | **≈ 14.616.000 VNĐ / tháng** |

> [!TIP]
> **Kinh tế học đơn vị (Unit Economics)**: Ở quy mô 10.000 người dùng (200.000 lượt quét mỗi tháng), chi phí hạ tầng trên mỗi lượt kiểm tra giọng nói chỉ tốn khoảng **73 VNĐ**. Việc ứng dụng **AWS Spot Instances** giúp giảm tới **68.4% chi phí** so với On-Demand.

---

## 2. Sổ Tay Xử Lý Sự Cố Khi Vận Hành Thực Tế (Troubleshooting Runbook)

| Mã sự cố | Triệu chứng | Nguyên nhân gốc rễ | Lệnh / Thao tác khắc phục tức thì | Biện pháp phòng ngừa lâu dài |
|---|---|---|---|---|
| **INC-01** | Tràn VRAM GPU (`CUDA Out of Memory`) | Nhiều tác vụ Live VoiceStudio CFM chạy song song trên GPU 4GB VRAM. | `docker restart VieTrueVoice-api` hoặc `torch.cuda.empty_cache()` | Cấu hình hàng đợi Celery/Redis giới hạn tối đa 2 luồng CFM đồng thời. |
| **INC-02** | Âm thanh Micro bị im lặng / rè | Micro WebRTC 48kHz bị trôi lệch DC Offset và tiếng ù đất 50Hz. | Bật tự động: `librosa.effects.trim(top_db=25)` và chuẩn hóa đỉnh 95%. | Tái lấy mẫu Mono PCM_16 ngay trên luồng thu WebRTC của trình duyệt. |
| **INC-03** | Khởi động lạnh trễ $> 3.0$s | CUDA Context và trọng số chưa được nạp sẵn khi container mới bật. | Gửi request khởi động mồi: `curl http://localhost:8000/health` kèm dummy tensor. | Tích hợp script warm-up tự động trong Dockerfile ENTRYPOINT. |
| **INC-04** | Lỗi định dạng tệp âm thanh lạ | File tải lên bị hỏng header hoặc sai phần mở rộng MIME type. | Bộ nạp `audio_loader.py` nhận diện theo Magic Bytes và stream qua FFmpeg. | Chặn tệp không hợp lệ tại tầng Gateway trước khi nạp vào AI Core. |
| **INC-05** | Quá tải luồng gọi API (`HTTP 429`) | Một IP gửi liên tiếp $> 30$ yêu cầu thẩm định trong vòng 1 phút. | Trả về mã lỗi HTTP 429 kèm tiêu đề `Retry-After: 60`. | Áp dụng thuật toán Token Bucket kiểm soát lưu lượng trên FastAPI middleware. |

---

## 3. Công Thức & Tự Tính Tỷ Lệ Hoàn Thành Đồ Án Tại Tuần 8

Áp dụng công thức quy định tại Mục F Đề cương chi tiết:
$$\text{\% Hoàn thành (W08)} = 50\% \times \left(\frac{\text{Số Checkpoint Đạt}}{8}\right) + 50\% \times \left(\frac{\text{Số Must Đã Nghiệm Thu}}{\text{Tổng Số Must}}\right)$$

* Số Checkpoint Đạt: $8 / 8$ Checkpoints (W01 đến W08) $= 50.0\%$
* Số Tính năng Must Đã Nghiệm Thu: $3 / 3$ Musts (Must #1, #2, #3) $= 50.0\%$
* **Tổng tỷ lệ hoàn thành**: **$100.0\%$** (Vượt xa điều kiện $\ge 50\%$ để được phép bảo vệ trước Hội đồng).
