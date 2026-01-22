# 📍 AI Expert Finder & Mentor Connector (Hệ thống tìm kiếm Chuyên gia & Cố vấn)

## 1. Tổng Quan

Hệ thống cho phép người dùng (học viên, nghiên cứu sinh) tìm kiếm Chuyên gia hoặc Cố vấn (Mentors/Experts) thông qua giao diện Chat. Hệ thống sẽ tự động xác định nhu cầu học tập/nghiên cứu, tìm Chuyên gia phù hợp nhất (từ danh sách trong Google Sheets), cung cấp quyền truy cập vào Knowledge Base (NotebookLM) của chuyên gia đó và dùng AI để tư vấn lộ trình học tập cá nhân hóa.

Hệ thống hỗ trợ đăng nhập qua Zalo OAuth để cá nhân hóa trải nghiệm và cho phép kết nối trực tiếp với cộng đồng Zalo của Chuyên gia.

## 2. Actors (Tác nhân)

- **User (Người dùng)**: Học viên, nghiên cứu sinh hoặc người cần tìm kiếm tri thức chuyên sâu.
- **System (Backend)**: Xử lý logic tìm kiếm, phân tích ý định (intent), và quản lý kết nối.
- **Zalo OAuth Service**: Cung cấp API để xác thực người dùng qua tài khoản Zalo.
- **Google Maps Service**: Hỗ trợ định vị (nếu cần tư vấn offline) và chuẩn hóa địa chỉ.
- **Google Sheets (Database)**: Lưu trữ hồ sơ chuyên gia, lĩnh vực chuyên môn, và các liên kết tri thức (NotebookLM).
- **AI Engine (DeepSeek V3)**: Phân tích nhu cầu người dùng và sinh câu trả lời tư vấn tự nhiên.

---

## 3. Use Case 1: "Đăng nhập với Zalo OAuth"

**Pre-conditions (Điều kiện tiên quyết)**
- Người dùng có tài khoản Zalo.
- Ứng dụng đã được cấu hình Zalo App và Backend.

**Basic Flow (Luồng chính)**
1. **User**: Truy cập trang đăng nhập.
2. **System**: Kiểm tra session hiện có. Nếu hợp lệ -> Chuyển vào trang chủ.
3. **User**: Click "Đăng nhập với Zalo".
4. **Backend**: Thực hiện quy trình trao đổi code lấy access token và thông tin profile Zalo.
5. **System**: Tạo session và lưu thông tin người dùng (Tên, Avatar) vào `localStorage`.
6. **User**: Bắt đầu tìm kiếm chuyên gia với tư cách đã đăng nhập.

---

## 4. Use Case 2: "Tìm kiếm Chuyên gia & Tư vấn lộ trình"

**Pre-conditions (Điều kiện tiên quyết)**
- Dữ liệu Chuyên gia đã được nạp đầy đủ vào Google Sheets (Tên, Chuyên môn, Link Knowledge Base, Link Zalo).

**Basic Flow (Luồng chính)**
1. **User**: Nhập câu hỏi vào khung chat (Ví dụ: "Tôi muốn tìm người hướng dẫn về AI và Machine Learning").
2. **Backend**: Gọi AI để phân tích **Chủ đề (Topic)** và **Nhu cầu nghiên cứu**.
3. **AI Engine**: Trích xuất các từ khóa chuyên môn (AI, ML).
4. **Backend**:
   - Quét danh sách Chuyên gia từ Google Sheets.
   - Lọc ra các Chuyên gia có chuyên môn khớp với từ khóa.
   - Ưu tiên các chuyên gia có Knowledge Base (NotebookLM) sẵn sàng.
5. **AI Engine**: Nhận ngữ cảnh về các Chuyên gia tìm được để soạn câu trả lời tư vấn:
   - "Chào bạn, mình tìm thấy Chuyên gia A rất giỏi về AI. Bạn có thể chat với Knowledge Base của anh ấy hoặc tham gia nhóm Zalo để trao đổi thêm."
6. **Backend**: Trả về Response gồm: Văn bản tư vấn + Danh sách Expert Cards (Thẻ chuyên gia).
7. **User**: Xem thông tin chuyên gia và chọn hành động tiếp theo.

**Alternative Flows (Luồng thay thế)**
- **A1. Tìm chuyên gia theo vị trí**: Nếu người dùng muốn gặp trực tiếp, hệ thống sẽ lọc chuyên gia gần vị trí của người dùng nhất.
- **A2. Không tìm thấy chuyên gia cụ thể**: AI sẽ đưa ra lời khuyên chung về lộ trình học tập và gợi ý các nguồn tài liệu liên quan.
- **A3. Tham gia cộng đồng**: Người dùng click "Tham gia cộng đồng" -> Ghi nhận Lead (Học viên tiềm năng) vào Google Sheets -> Chuyển hướng sang Zalo Group của chuyên gia.

**Post-conditions (Kết quả)**
- Người dùng kết nối được với nguồn tri thức phù hợp.
- Hệ thống ghi nhận được nhu cầu của học viên để chuyên gia có thể hỗ trợ sâu hơn.
