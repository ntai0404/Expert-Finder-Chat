# Kế Hoạch Triển Khai Frontend (Expert Finder UI)

## 1. Mục tiêu

Xây dựng giao diện người dùng tối ưu cho việc tìm kiếm Chuyên gia và tiếp cận tri thức:
- **Map View**: Hiển thị vị trí người dùng và các chuyên gia/trung tâm hỗ trợ gần nhất.
- **Chatbox**: Giao diện AI tư vấn học tập và nghiên cứu.
- **Expert Interaction**: Hệ thống thẻ thông tin chuyên gia với các hành động kết nối trực tiếp.

## 2. Các thành phần giao diện chính

- **Chat Pane**: Khu vực hiển thị tin nhắn AI và người dùng. Hỗ trợ hiển thị rich content (Markdown, Emoji).
- **Expert Card (Thẻ Chuyên Gia)**: 
  - Hiển thị Tên, Ảnh (Avatar), Chuyên môn và Lĩnh vực hỗ trợ.
  - Nút **"Truy cập Knowledge Base"**: Mở link NotebookLM để người dùng tự nghiên cứu.
  - Nút **"Tham gia cộng đồng"**: Kết nối vào nhóm Zalo để hỏi đáp trực tiếp.
- **Interactive Map**: Hiển thị vị trí trực quan, giúp người dùng tìm thấy các cơ sở tư vấn hoặc chuyên gia hỗ trợ offline.

## 3. Logic xử lý Frontend (script_app.js)

- **Xử lý Vị trí (Geolocation)**: Lấy tọa độ người dùng để AI có thể gợi ý các chuyên gia ở gần hoặc chuẩn hóa lời chào theo địa điểm.
- **Xử lý Chat**: 
  - Gửi nhu cầu của người dùng lên Backend.
  - Nhận phản hồi AI và danh sách Chuyên gia.
  - Hiển thị thẻ chuyên gia động trong khung chat.
- **Persistance**: Lưu lịch sử chat và thông tin người dùng vào `sessionStorage`/`localStorage` để dữ liệu không bị mất khi reload trang.

## 4. Đặc tả Dữ liệu Giao tiếp (Interface Contract)

### Request (Gửi từ Frontend):
```json
{
  "message": "Tôi cần tìm cố vấn về khởi nghiệp công nghệ",
  "latitude": 21.0285,
  "longitude": 105.8542
}
```

### Response (Nhận từ Backend):
```json
{
  "reply": "Chào bạn! Mình đã tìm thấy Chuyên gia X rất phù hợp để tư vấn khởi nghiệp cho bạn tại Hà Nội...",
  "nearest_experts": [
    {
      "name": "Chuyên gia Nguyễn Văn A",
      "expertise": "Khởi nghiệp / SaaS",
      "lat": 21.0300,
      "lng": 105.8500,
      "knowledge_link": "/view/expert_01",
      "zalo_link": "https://zalo.me/g/abc"
    }
  ]
}
```

## 5. Danh sách công việc (Checklist)

- [ ] Cập nhật lại nhãn (label) trong file `index.html` từ "Store" sang "Expert".
- [ ] Thay đổi icon và màu sắc giao diện theo hướng học thuật/chuyên nghiệp.
- [ ] Implement logic hiển thị thẻ Chuyên gia (Expert Card) thay cho thẻ sản phẩm.
- [ ] Kiểm tra tính năng redirect sang NotebookLM từ nút "Xem tri thức".
- [ ] Đảm bảo Zalo login hiển thị tên và avatar học viên chính xác trên header.
