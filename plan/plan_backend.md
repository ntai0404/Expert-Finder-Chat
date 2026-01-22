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

### Bước 1: Intent Extraction
Khi người dùng gửi tin nhắn, AI sẽ trích xuất:
- `topic`: Chủ đề học viên đang quan tâm.
- `level`: Mức độ kiến thức người dùng đang ở (Cơ bản/Nâng cao).
- `location_require`: Có cần tìm chuyên gia ở gần không?

### Bước 2: Expert Matching
- Backend thực hiện lọc trong DataFrame chuyên gia dựa trên `expertise` và `topics`.
- Nếu có tọa độ người dùng, thực hiện tính khoảng cách để tìm người gần nhất.

### Bước 3: RAG & AI Response
- Backend tạo ngữ cảnh (context) từ profile các chuyên gia tìm được.
- Gửi context và câu hỏi người dùng tới DeepSeek.
- AI sinh câu trả lời hướng dẫn: "Dựa trên nhu cầu tìm hiểu về [Topic], mình gợi ý bạn kết nối với Chuyên gia [Name]..."

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
