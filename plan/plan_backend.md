# Kế Hoạch Triển Khai Backend (Expert Finder Backend)

## 1. Công nghệ sử dụng

- **Framework**: FastAPI (Async support cho AI và Database calls).
- **AI Engine**: DeepSeek V3 (Phân tích intent và sinh văn bản tư vấn).
- **Data Source**: Google Sheets (Lưu trữ profile chuyên gia và leads).
- **Core Libraries**: `pandas` (Xử lý bảng), `geopy` (Tính khoảng cách), `openai` (Giao tiếp với DeepSeek).

## 2. Cấu trúc dữ liệu Chuyên gia (Google Sheets)

Hệ thống sử dụng các cột chính sau:
- `expert_id`: Mã định danh duy nhất.
- `expert_name`: Tên chuyên gia/cố vấn.
- `expertise`: Lĩnh vực chuyên môn chính.
- `topics`: Danh sách các chủ đề hỗ trợ cụ thể.
- `notebook_link`: Link dẫn tới Knowledge Base (NotebookLM).
- `zalo_group_link`: Link nhóm cộng đồng hỗ trợ.
- `latitude`, `longitude`: Tọa độ vị trí hỗ trợ.

## 3. Quy trình xử lý tại Backend

### Bước 1: Intent Extraction & Variable Mapping
Khi người dùng gửi tin nhắn, AI thực hiện Call 1 để trích xuất:
- **Expert**: Kỹ năng/Kinh nghiệm chuyên gia (nếu tìm người).
- **Topic**: Đề tài nghiên cứu cụ thể (nếu tìm tài liệu).
- **Intent**: Loại kịch bản (hello, thank, angry, help, my_location, Expert, Topic, Expert+Topic).

### Bước 2: Phân nhánh Xử lý (Flow Logic)
1. **Cảm xúc/Chào hỏi**: Trả về tin nhắn AI tương ứng, Expert/Topic = false.
2. **Tìm Chuyên gia (Expert)**: Lọc sheet `Experts` theo cột `kinh_nghiem`.
3. **Tìm Đề tài (Topic)**: Lọc sheet `Topics` theo `Chủ đề tri thức`.
4. **Vị trí (my_location)**: Kích hoạt API Google Maps lấy tọa độ user.

### Bước 3: Data Filtering & Second LLM Call
Đối với tìm kiếm (Expert/Topic):
- Hệ thống gửi kết quả thô từ database cho LLM thực hiện **Call 2**.
- LLM lọc bỏ dữ liệu nhiễu (lỗi ngữ nghĩa) và tổng hợp câu trả lời ngắn gọn.
- **Đặc biệt (Topic Search)**: Expert Card chỉ hiển thị các đề tài có trong kết quả lọc.

### Bước 4: Geolocation & Distance
- Với các yêu cầu tìm kiếm hoặc chào hỏi: Call Geolocation API để ghim vị trí user.
- Tính toán khoảng cách từ user đến chuyên gia để hiển thị trên Thẻ Chuyên Gia.

## 4. Đặc tả API Models

### ChatRequest
```python
class ChatRequest(BaseModel):
    message: str
    latitude: float
    longitude: float
```

### ExpertInfo
```python
class ExpertInfo(BaseModel):
    name: str
    expertise: str
    lat: float
    lng: float
    knowledge_link: str
    zalo_link: str
```

### ChatResponse
```python
class ChatResponse(BaseModel):
    reply: str
    nearest_experts: List[ExpertInfo]
```

## 5. Danh sách công việc (Checklist)

- [ ] Cấu hình API Key DeepSeek và Google Sheets Service Account.
- [ ] Xây dựng service `sheet_service.py` để load profile chuyên gia.
- [ ] Xây dựng service `ai_service.py` với prompt chuyên sâu về giáo dục/cố vấn.
- [ ] Viết endpoint `/chat` xử lý toàn bộ luồng matching chuyên gia.
- [ ] Đảm bảo cơ chế lưu Lead vào Google Sheets hoạt động khi học viên click kết nối.
