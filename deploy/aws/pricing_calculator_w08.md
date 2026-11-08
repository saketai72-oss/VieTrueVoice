# Ước Tính Chi Phí Vận Hành Hệ Thống ViTrueVoice Trên Hạ Tầng Đám Mây AWS (Bảng 3.4 Đề Cương v4)

> **Mô hình kiến trúc**: Áp dụng tri thức từ 3 chứng chỉ AWS Academy Gói A (Cloud Foundations, Security Foundations, Cloud Architecting).  
> **Khu vực tính toán**: `ap-southeast-1` (Singapore - độ trễ thấp nhất về Việt Nam, RTT ~30-40ms).  
> **Nguyên tắc bảo mật**: Toàn bộ luồng âm thanh xử lý in-memory; tệp ghi nhận trên S3 kích hoạt S3 Lifecycle hủy sau 24h (zero long-term storage cost).

---

## 1. Bảng Tổng Hợp Chi Phí Vận Hành Theo 3 Kịch Bản Quy Mô

| Dịch vụ AWS | Thành phần cấu hình | Kịch bản 1: Thử nghiệm (100 users/ngày ~500 reqs) | Kịch bản 2: Vận hành cơ sở (1.000 users/ngày ~5.000 reqs) | Kịch bản 3: Doanh nghiệp (10.000 users/ngày ~50.000 reqs) |
|---|---|:---:|:---:|:---:|
| **Amazon EC2 (Compute)** | Instance Type & SL | 1x `t3.large` (2 vCPU, 8GB RAM) On-Demand | 1x `g4dn.xlarge` (4 vCPU, 16GB RAM, 1 NVIDIA T4 GPU) Spot | Auto Scaling: 1-3x `g4dn.xlarge` Spot sau ALB |
| | Chi phí máy chủ / tháng | **$60.74** ($0.0832/h) | **$114.24** (Spot ~$0.158/h) | **$295.68** (Bình quân 1.8 instances) |
| **Amazon ECR** | Lưu trữ Docker Image (5GB) | **$0.50** ($0.10/GB) | **$0.50** ($0.10/GB) | **$0.50** ($0.10/GB) |
| **Amazon S3** | Standard Storage (Lifecycle 1 day) | **$0.05** (< 2 GB lưu chuyển/ngày) | **$0.35** (~15 GB lưu chuyển/ngày) | **$2.50** (~120 GB lưu chuyển/ngày) |
| **AWS CloudWatch** | Ingestion & Metric Alarms | **$2.50** (< 3 GB log ẩn danh SHA-256) | **$6.80** (~10 GB log ẩn danh) | **$24.50** (~40 GB log + Alarms) |
| **Application Load Balancer** | Cân bằng tải & SSL Termination | Không dùng (EC2 gắn Elastic IP) | Không dùng | **$22.26** (1 ALB + LCU) |
| **Data Transfer Out** | Lưu lượng băng thông mạng trả về | **$0.45** (~5 GB/tháng) | **$4.05** (~45 GB/tháng) | **$36.00** (~400 GB/tháng) |
| **TỔNG CHI PHÍ / THÁNG** | *(Dự toán chi phí AWS)* | **~$64.24 / tháng** | **~$125.94 / tháng** | **~$381.44 / tháng** |
| **Chi phí trên mỗi lượt xác thực** | *(Cost per Request)* | **~$0.0043** (~107 VNĐ) | **~$0.0008** (~20 VNĐ) | **~$0.00025** (~6 VNĐ) |

---

## 2. Phân Tích Kỹ Thuật & Tối Ưu Hóa Chi Phí (AWS Well-Architected)

1. **Chiến lược Điện toán (Compute Strategy)**:
   - Với quy mô **100 users/ngày**, kiến trúc CPU với `t3.large` (sử dụng CPU Credits burstable) hoàn toàn đáp ứng trần độ trễ $\le 3.0$s (thực nghiệm đo được ~0.35s/req), giúp tiết kiệm 70% chi phí so với việc thuê máy chủ GPU liên tục.
   - Với quy mô **1.000 – 10.000 users/ngày**, việc chuyển sang GPU `g4dn.xlarge` dạng **Spot Instance** (tiết kiệm đến 68% so với On-Demand) giúp thời gian suy luận đạt đỉnh cao **66.3ms/req**, xử lý thông lượng lên tới 15 reqs/giây trên một node.

2. **Tối ưu Hóa Lưu Trữ & Tuân Thủ Đạo Đức Sinh Trắc Học (S3 Lifecycle)**:
   - Nhờ quy tắc `s3_lifecycle_policy.json` tự động xóa tệp âm thanh trong vòng 24 giờ, dung lượng tích lũy trên S3 luôn duy trì gần mức 0 GB, loại bỏ hoàn toàn chi phí lưu trữ dài hạn và rủi ro rò rỉ dữ liệu sinh trắc học theo Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15.

3. **Giám Sát Ẩn Danh (CloudWatch Logs)**:
   - Toàn bộ log gửi lên CloudWatch chỉ chứa mã băm SHA-256 của file âm thanh và số đo độ trễ (không chứa nội dung giọng nói hay số điện thoại), tối ưu hóa dung lượng ghi log chỉ vài chục byte cho mỗi request.
