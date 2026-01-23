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
        system_prompt = f"""Bạn là trợ lý ảo 'Matrix Finder AI' - Nền tảng kết nối học viên với Chuyên gia & Cố vấn tri thức hàng đầu.
        Phong cách: Học thuật, chuyên nghiệp, tận tâm và luôn sử dụng emoji 🎓✨.
        
        Thông tin ngữ cảnh (Chuyên gia & Chủ đề):
        {json.dumps(context, ensure_ascii=False, indent=2)}

        Trạng thái hội thoại:
        {json.dumps(intent, ensure_ascii=False, indent=2)}

        QUY TẮC PHẢN HỒI (QUAN TRỌNG):
        1. Nếu 'is_topic_inquiry' là true: 
           - Giải thích ngắn gọn về Topic đó bằng kiến thức của bạn.
           - NẾU context không rỗng: Giới thiệu chuyên gia bên dưới (vd: "Để đào sâu hơn, anh/chị có thể kết nối với Chuyên gia X bên dưới nhé!").
           - NẾU context rỗng: Thông báo chưa có chuyên gia (vd: "Hiện tại Matrix Finder AI chưa có chuyên gia đào tạo mảng này, nhưng sơ bộ thì Topic [X] là...").
        2. Nếu 'is_topic_inquiry' là false và context là []: Báo chưa tìm thấy chuyên gia phù hợp.
        3. Nếu có chuyên gia: Chào hỏi, dẫn dắt tự nhiên và giới thiệu họ.
        4. Trả lời cực kỳ ngắn gọn (tối đa 3 câu). Tuyệt đối không dùng danh sách Markdown.
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

async def extract_search_intent(query: str, categories: Optional[List[str]] = None, expert_menu: List[str] = [], topic_menu: List[str] = []) -> Dict[str, Any]:
    """
    Call 1: Extract search filters (Expert, Topic, Intent) using dynamic menus.
    Returns JSON.
    """
    if not client:
        configure_genai()
        if not client: return {}

    try:
        # Prepare menus for prompt
        expert_menu_str = ", ".join(expert_menu[:100]) if expert_menu else "AI, Marketing, Blockchain"
        topic_menu_str = ", ".join(topic_menu[:100]) if topic_menu else "RAG, Smart Contract, SEO"
        
        prompt = f"""
        Phân tích câu hỏi của người dùng và trích xuất thông tin JSON theo kịch bản Matrix Finder AI.
        
        Query: "{query}"

        MENU HỆ THỐNG (BẮT BUỘC KHỚP NẾU CÓ THỂ):
        - Menu Expert (Kinh nghiệm): {expert_menu_str}
        - Menu Topic (Đề tài): {topic_menu_str}
        - Menu Intent: Expert, Topic, my_location, Expert + Topic, angry, thank, hello, help

        QUY TẮC TRÍCH XUẤT:
        1. Expert: Gắn nhãn kinh nghiệm phù hợp từ Menu Expert. Nếu user hỏi "ai biết về", "có ai giỏi về", "tìm người"... thì MUST set Expert. Nếu không có trong menu, hãy trích xuất từ khóa chính bằng tiếng Anh. Nếu không tìm người, để false.
        2. Topic: Gắn nhãn đề tài phù hợp từ Menu Topic. Nếu user hỏi "có tài liệu", "có sách", "có bài viết"... thì MUST set Topic. Nếu không có trong menu, trích xuất từ khóa chính. Nếu không tìm đề tài, để false.
        3. Intent: 
           - 'hello': Chào hỏi xã giao.
           - 'thank': Cảm ơn.
           - 'angry': Phàn nàn, tức giận.
           - 'help': Hỏi về chức năng hệ thống.
           - 'my_location': Hỏi vị trí hiện tại/gần đây.
           - 'Expert': Người dùng đang tìm Chuyên gia/Cố vấn.
           - 'Topic': Người dùng đang tìm Đề tài/Kiến thức/Tài liệu.
           - 'Expert + Topic': Tìm cả hai (vd: "Có ai giỏi AI và có tài liệu RAG không?").

        Output Format (JSON strict):
        {{
            "Expert": "string or false",
            "Topic": "string or false",
            "Intent": "one from menu intent",
            "keyword": "từ khóa gốc"
        }}
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a specialized Intent Extractor for Matrix Finder AI."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Intent Extraction Error: {e}")
        return {"Expert": False, "Topic": False, "Intent": "help"}

async def summarize_and_filter_results(user_msg: str, results_context: List[Any], intent_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call 2: Semantically filter results and provide a concise summary.
    Returns JSON { "reply": "...", "kept_expert_ids": [...], "kept_topic_names": [...] }
    """
    if not client:
        configure_genai()
        if not client: return {"reply": "Hệ thống đang bận, vui lòng thử lại sau.", "kept_expert_ids": [], "kept_topic_names": []}

    try:
        prompt = f"""
        Dưới đây là yêu cầu của người dùng và kết quả thô từ cơ sở dữ liệu.
        
        NHIỆM VỤ:
        1. Lọc bỏ dữ liệu lỗi ngữ nghĩa (vd: user hỏi 'AI' nhưng kết quả là 'Tâm linh' do trùng chữ cái).
        2. Sinh câu trả lời tổng hợp các kết quả tìm thấy (TỐI ĐA 3 CÂU). 
        3. Nếu Intent là 'Expert': Hãy giới thiệu về các chuyên gia.
        4. Nếu Intent là 'Topic': Hãy giới thiệu về các đề tài.
        5. QUAN TRỌNG: Hãy giữ lại TẤT CẢ các ID chuyên gia và Tên đề tài thực sự liên quan đến yêu cầu từ dữ liệu thô. KHÔNG ĐƯỢC chỉ chọn 1 cái duy nhất.

        Yêu cầu: "{user_msg}"
        Dữ liệu thô: {json.dumps(results_context, ensure_ascii=False)}
        Ý định: {json.dumps(intent_vars, ensure_ascii=False)}

        PHONG CÁCH: Chuyên nghiệp, tận tâm, sử dụng emoji 🎓✨.

        Output Format (JSON strict):
        {{
            "reply": "câu trả lời tổng hợp các kết quả phù hợp",
            "kept_expert_ids": ["ID1", "ID2", ...],
            "kept_topic_names": ["Tên chủ đề 1", "Tên chủ đề 2", ...]
        }}
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are Matrix Finder AI Assistant. Filter and summarize results."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Summarize/Filter Error: {e}")
        return {
            "reply": "Dạ, em tìm thấy một số thông tin phù hợp, mời anh/chị xem chi tiết bên dưới nhé! 🎓✨",
            "kept_expert_ids": [str(r.get('expert_id')) for r in results_context],
            "kept_topic_names": []
        }

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
