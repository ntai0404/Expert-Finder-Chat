# 🎓 Matrix Finder AI - AI-Powered Professional Network

Matrix Finder AI là nền tảng kết nối học viên với các Chuyên gia & Cố vấn tri thức hàng đầu thông qua trí tuệ nhân tạo (DeepSeek V3). Hệ thống cho phép tìm kiếm chuyên gia dựa trên vị trí thực tế, lĩnh vực chuyên môn và kho tri thức số (NotebookLM).

---

## ✨ Tính Năng Chính

*   **🤖 Trí Tuệ Nhân Tạo (DeepSeek V3)**: Tự động phân tích ý định tìm kiếm, gợi ý chuyên gia phù hợp và phản hồi tự nhiên.
*   **📍 Định Vị Thông Minh**: Tìm kiếm và tính khoảng cách tới các chuyên gia gần bạn nhất.
*   **🎓 Expert Cards (Compact UI)**: Giao diện thẻ chuyên gia chuyên nghiệp, hiển thị Avatar, lĩnh vực chuyên môn, Notebook Link và Zalo Group.
*   **📚 Kho Tri Thức (NotebookLM)**: Kết nối trực tiếp tới các tài liệu, bài giảng và ghi chép số của chuyên gia.
*   **🔑 Đăng Nhập Zalo**: Tích hợp Zalo OAuth để quản lý phiên làm việc và định danh người dùng thuận tiện.
*   **📊 Quản Lý Dữ Liệu Linh Hoạt**: Hệ thống back-office chạy trên Google Sheets, cho phép cập nhật thông tin chuyên gia và chủ đề tri thức theo thời gian thực.

---

## 🏗️ Kiến Trúc Hệ Thống

```text
expert_finder/
├── backend_app/         # Backend (FastAPI + DeepSeek API)
│   ├── main.py          # Entry point & API Endpoints
│   ├── services/        # AI, Geocoding, Google Sheets & Expert Logic
│   └── models.py        # Cấu trúc dữ liệu (Pydantic)
├── assets/              # Hình ảnh, biểu tượng & tài nguyên tĩnh
├── index.html           # Giao diện Chat & Map chính
├── login.html           # Trang đăng nhập Zalo
├── script_app.js        # Logic Frontend (Chat, Map & Persistence)
├── style.css            # Giao diện chi tiết
├── .env.example         # Cấu hình môi trường mẫu
└── README.md            # Tài liệu dự án
```

---

## 🚀 Hướng Dẫn Cài Đặt

### 1. Chuẩn Bị
*   Python 3.10+
*   Google Maps API Key (cho Geocoding & Map)
*   DeepSeek API Key (cho AI Response)
*   Zalo App Credentials (cho OAuth)

### 2. Cài Đặt
```bash
# Clone dự án
git clone https://github.com/ntai0404/Expert-Finder-Chat.git
cd Expert-Finder-Chat

# Cài đặt thư viện
pip install -r backend_app/requirements.txt
```

### 3. Cấu Hình
Tạo file `.env` từ `.env.example` và điền đầy đủ các API Keys cần thiết.

### 4. Khởi Chạy
```bash
cd backend_app
python main.py
```
Server sẽ chạy mặc định tại cổng **9000**. Truy cập: `http://localhost:9000`

---

## 👨‍💻 Tác Giả
**Nguyễn Xuân Tài** - [ntai0404](https://github.com/ntai0404)

## 📄 Giấy Phép
Dự án được phát hành dưới giấy phép MIT.
