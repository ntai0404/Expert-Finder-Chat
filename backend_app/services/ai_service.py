import os
import json
import logging
from openai import OpenAI
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Logger configuration
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Cache for AI standardization
AI_ADDR_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'ai_address_cache.json')

def load_ai_cache():
    if os.path.exists(AI_ADDR_CACHE_FILE):
        try:
            with open(AI_ADDR_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_ai_cache(cache):
    try:
        with open(AI_ADDR_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass

# Initialize Client
client = None

def configure_genai():
    """Confirms DeepSeek Client is ready."""
    global client
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY not found in .env")
        return False
    
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        logger.info("DeepSeek AI Configured Successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to configure DeepSeek: {e}")
        return False

async def get_ai_response(user_msg: str, context: List[Any], intent: Dict[str, Any], type: str = "chat") -> str:
    """
    Generates a response using DeepSeek Chat (V3).
    """
    if not client:
        configure_genai()
        if not client:
            return "Hệ thống AI đang bảo trì (Missing Key)."

    try:
        system_prompt = f"""Bạn là trợ lý ảo 'Expert Finder' - Nền tảng kết nối học viên với Chuyên gia & Cố vấn tri thức hàng đầu.
        Phong cách: Học thuật, chuyên nghiệp, tận tâm và luôn sử dụng emoji 🎓✨.
        
        Thông tin ngữ cảnh (Chuyên gia & Chủ đề):
        {json.dumps(context, ensure_ascii=False, indent=2)}

        QUY TẮC PHÅN HỒI (QUAN TRỌNG):
        1. Nếu ngữ cảnh (context) phía trên là rỗng [], bạn PHẢI trả lời rằng hiện tại chưa tìm thấy chuyên gia nào trong lĩnh vực này. KHÔNG ĐƯỢC bịa đặt tên chuyên gia hoặc chủ đề không có trong ngữ cảnh.
        2. Ví dụ khi không có kết quả: "Dạ, hiện tại em chưa tìm thấy chuyên gia nào chuyên về lĩnh vực này trong danh sách hiện có ạ. Anh/chị có thể thử tìm kiếm với từ khóa khác nhé! 🎓✨"
        3. Nếu có chuyên gia: 
           - Chào hỏi và dẫn dắt tự nhiên.
           - Nếu > 1 người: "Dạ, em tìm thấy chuyên gia [Tên] và một số chuyên gia khác. Mời anh/chị xem chi tiết ở thẻ bên dưới ạ! 🎓✨"
           - Nếu = 1 người: "Dạ, em đã tìm thấy chuyên gia [Tên] phù hợp nhất. Anh/chị xem chi tiết ở thẻ bên dưới nhé!"
        4. Trả lời cực kỳ ngắn gọn (tối đa 2 câu). Tuyệt đối không dùng danh sách Markdown.
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=False
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"DeepSeek Chat Error: {e}")
        return "Xin lỗi, em đang bị quá tải. Anh chị chờ chút nhé!"

async def extract_search_intent(query: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extracts search filters (product name, price, location) using DeepSeek.
    Returns JSON.
    """
    if not client:
        configure_genai()
        if not client: return {}

    try:
        # Include categories in prompt if available to improve accuracy
        cat_str = ", ".join(categories) if categories else "Giáo dục, Công nghệ 4.0, Kinh doanh & Khởi nghiệp, Ngoại ngữ, Nghệ thuật"
        
        prompt = f"""
        Phân tích câu hỏi của người dùng và trích xuất thông tin JSON phục vụ tìm kiếm Chuyên gia & Cố vấn tri thức.
        
        Query: "{query}"
        Lĩnh vực chuyên môn (ưu tiên khớp chính xác): {cat_str}
        Chủ đề tri thức tiêu biểu (vd): Chatbot, RAG, Solidity, DeFi, SEO, Figma, Penetration Testing.
        
        Quy tắc Boolean (RẤT QUAN TRỌNG):
        - "is_social_or_emotional": true nếu khách CHÀO HỎI (hi, chào), CẢM ƠN, hoặc BÀY TỎ CẢM XÚC (vui, buồn, khen ngợi, phàn nàn).
        - "is_general_inquiry": true nếu khách hỏi về Expert Finder là gì, bot có thể làm gì, hoặc các câu hỏi không liên quan đến tìm kiếm chuyên môn cụ thể.
        - "is_location_request": true chỉ khi có từ khóa địa điểm hoặc yêu cầu tìm gần đây ("ở đâu", "gần đây", "quanh đây").

        Quy tắc quan trọng nhất: 
        - Nếu người dùng hỏi bằng tiếng Việt ("học máy", "chuỗi khối", "tiếp thị"), PHẢI dịch sang TIẾNG ANH ("Machine Learning", "Blockchain", "Marketing").
        - Nếu lĩnh vực người dùng hỏi KHÔNG có trong danh sách gợi ý (ví dụ: "nông nghiệp", "y tế"), bạn VẪN PHẢI trích xuất từ khóa đó vào "expertise" (dịch sang tiếng Anh). KHÔNG ĐƯỢC để trống nếu người dùng đang có ý định tìm kiếm.
        - Tuyệt đối giữ nguyên các từ khóa kỹ thuật (Smart Contract, Chatbot, DeFi) và chuyển về dạng từ đơn nếu cần (vd: "chat bot" -> "Chatbot").

        Output Format (JSON strict):
        {{
            "expertise": "Lĩnh vực chuyên môn (vd: Agriculture, AI, Blockchain).",
            "topic": "Chủ đề cụ thể (vd: RAG, Smart Contracts, Chatbot).",
            "keyword": "từ khóa gốc người dùng nhập",
            "location": "",
            "is_location_request": boolean,
            "is_general_inquiry": boolean,
            "is_social_or_emotional": boolean
        }}
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a JSON extractor."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Intent Extraction Error: {e}")
        return {}

async def expert_logic_template(query: str, experts: List[Any]) -> Dict[str, Any]:
    """
    Template for expert matching logic.
    """
    return {
        "found": True,
        "experts": experts,
        "ai_message_template": "Dạ, em tìm thấy chuyên gia {{expert_name}} chuyên về {{expertise}} có thể hỗ trợ anh/chị ạ."
    }

async def standardize_address_ai(ward: str, district: str, city: str) -> str:
    """
    Standardizes address components using DeepSeek AI.
    Uses local cache to minimize API calls.
    """
    cache = load_ai_cache()
    raw_key = f"{ward}|{district}|{city}"
    
    if raw_key in cache:
        return cache[raw_key]
    
    global client
    if not client:
        configure_genai()
    
    if not client:
        return f"{ward}, {district}, {city}"
        
    prompt = f"""Bạn là chuyên gia về địa lý Việt Nam. 
    Hãy chuẩn hóa địa chỉ sau thành định dạng chuẩn nhất để bản đồ có thể xác định được tọa độ.
    Dữ liệu thô: {ward}, {district}, {city}

    Quy tắc:
    1. Giữ nguyên cấp hành chính: Nếu là "Thị trấn" thì ghi "Thị trấn", không được tự ý đổi thành "Xã".
    2. Giải mã viết tắt: "Q." -> "Quận", "P." -> "Phường", "TP." -> "Thành phố", "TP.HCM" -> "Thành phố Hồ Chí Minh".
    3. Định dạng trả về: "Tên Phường/Xã/Thị trấn, Tên Quận/Huyện/Thị xã/Thành phố thuộc tỉnh, Tên Tỉnh/Thành phố trực thuộc trung ương".
    4. Chỉ trả về 1 dòng địa chỉ duy nhất, không giải thích gì thêm.
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        clean_addr = response.choices[0].message.content.strip()
        cache[raw_key] = clean_addr
        save_ai_cache(cache)
        return clean_addr
    except Exception as e:
        logger.error(f"AI Address Standarization Error: {e}")
        return f"{ward}, {district}, {city}"
