# Kế Hoạch Triển Khai Chung (Technical Plan - Expert Finder)

## Thách thức chính

1. **Authentication & Session Management**: Hệ thống xác thực người dùng qua Zalo OAuth và quản lý session trong vòng 24 giờ.
2. **Dữ liệu Chuyên gia (Expert Data)**: Thông tin từ Google Sheets cần được cấu trúc lại để phản ánh chuyên môn, lĩnh vực cố vấn và các liên kết Knowledge Base (NotebookLM).
3. **Địa điểm & Kết nối**: Mặc dù tập trung vào tư vấn online, hệ thống vẫn duy trì khả năng định vị để tìm kiếm "Cố vấn gần bạn" hoặc các trung tâm đào tạo offline.

## Các bước thực hiện

---

### Giai đoạn 0: Authentication System (Zalo OAuth)

Hệ thống xác thực giúp nhận diện người dùng và lưu trữ lịch sử tư vấn.
- **Zalo Login**: Cho phép người dùng đăng nhập nhanh, lấy được Tên và Avatar để AI xưng hô thân thiện.
- **Session Management**: Sử dụng `localStorage` để duy trì trạng thái đăng nhập, đảm bảo trải nghiệm chat không bị ngắt quãng.

### Giai đoạn 1: Chuẩn bị Dữ liệu Chuyên gia (Data Preparation)

Dữ liệu được quản lý qua Google Sheets để dễ dàng cập nhật.
- **Cấu trúc Sheet**:
  - `expert_id`, `expert_name`, `expertise` (Lĩnh vực), `topics` (Chủ đề hỗ trợ).
  - `notebook_link` (Link Knowledge Base/NotebookLM).
  - `zalo_group_link` (Cộng đồng hỗ trợ).
  - `address`, `latitude`, `longitude` (Dùng cho tìm kiếm theo vị trí).

### Giai đoạn 2: Backend Development (FastAPI)

- **Intent Analysis (Matrix Finder AI)**:
  - Phân tích yêu cầu dựa trên bộ 3 biến: **Expert**, **Topic**, **Intent**.
  - Xử lý đa kịch bản (Chào hỏi, Tìm chuyên gia, Tìm đề tài, Tra cứu vị trí, Trợ giúp).
  - Sử dụng cơ chế "Dual-Call LLM" để lọc dữ liệu và sinh câu trả lời ngắn gọn, chính xác.
- **Matching Service**: So khớp từ khóa từ người dùng với `expertise` và `topics` trong database chuyên gia.
- **Location Support**: Tự động kích hoạt GPS khi người dùng chào hỏi hoặc hỏi vị trí.

### Giai đoạn 3: Frontend & UI Components

- **Chat Interface**: Giao diện chat mượt mà, hỗ trợ Markdown để hiển thị link và danh sách chuyên gia.
- **Expert Cards**: Các thẻ hiển thị thông tin chuyên gia với nút "Truy cập Knowledge Base" và "Tham gia cộng đồng".
- **Map View**: Hiển thị vị trí của chuyên gia hoặc văn phòng tư vấn trên bản đồ tương tác.

### Giai đoạn 4: Integration & UX Optimization

- **Lead Generation**: Khi người dùng click vào Zalo của chuyên gia, hệ thống tự động lưu thông tin (Tên, SĐT, Sản phẩm quan tâm) vào sheet `Leads` để chuyên gia có thể chủ động liên hệ hỗ trợ.
- **Mobile Optimization**: Đảm bảo giao diện hoạt động tốt trên thiết bị di động, nơi người dùng thường xuyên sử dụng Zalo.
