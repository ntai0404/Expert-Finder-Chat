import os
import json
import logging
import random
import google.generativeai as genai
from openai import OpenAI
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Logger configuration
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
GEMINI_KEYS_RAW = os.getenv("GEMINI_KEYS", "")
GEMINI_KEYS = [k.strip() for k in GEMINI_KEYS_RAW.split(",") if k.strip()]
NVIDIA_KEYS_RAW = os.getenv("NVIDIA_KEYS", os.getenv("NVIDIA_API_KEY", "")) # Support both for convenience
NVIDIA_KEYS = [k.strip() for k in NVIDIA_KEYS_RAW.split(",") if k.strip()]
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

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

class AIModelManager:
    def __init__(self):
        self.gemini_keys = GEMINI_KEYS
        self.current_gemini_idx = 0
        self.nvidia_keys = NVIDIA_KEYS
        self.current_nvidia_idx = 0
        
    def _get_next_gemini_key(self):
        if not self.gemini_keys: return None
        return self.gemini_keys[self.current_gemini_idx]

    def _rotate_gemini(self):
        if self.gemini_keys:
            self.current_gemini_idx = (self.current_gemini_idx + 1) % len(self.gemini_keys)
            logger.info(f"🔄 Swapping to next Gemini Key (Index: {self.current_gemini_idx})")

    def _get_next_nvidia_key(self):
        if not self.nvidia_keys: return None
        return self.nvidia_keys[self.current_nvidia_idx]

    def _rotate_nvidia(self):
        if self.nvidia_keys:
            self.current_nvidia_idx = (self.current_nvidia_idx + 1) % len(self.nvidia_keys)
            logger.info(f"🔄 Swapping to next NVIDIA Key (Index: {self.current_nvidia_idx})")

    async def call_gemini(self, prompt: str, system_instruction: str = "", model_name: str = "models/gemini-2.5-flash") -> Optional[str]:
        if not self.gemini_keys:
            logger.warning("⚠️ No Gemini Keys available in GEMINI_KEYS")
            return None
            
        # Refined models based on Audit: 2.5 and 3.0+ only as requested
        model_name_map = {
            "models/gemini-2.5-flash": ["models/gemini-2.5-flash", "models/gemini-3-flash-preview", "models/gemini-flash-latest"],
            "models/gemini-2.0-flash": ["models/gemini-2.5-flash", "models/gemini-3-flash-preview"],
            "models/gemini-3-flash-preview": ["models/gemini-3-flash-preview", "models/gemini-2.5-flash"]
        }
        
        # Ensure prefix models/
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        models_to_try = [model_name] + model_name_map.get(model_name, ["models/gemini-2.5-flash", "models/gemini-3-flash-preview"])
        models_to_try = list(dict.fromkeys(models_to_try))

        for _ in range(len(self.gemini_keys)):
            key = self._get_next_gemini_key()
            genai.configure(api_key=key)
            
            for m_name in models_to_try:
                try:
                    kwargs = {"model_name": m_name}
                    if system_instruction:
                        kwargs["system_instruction"] = system_instruction
                    
                    model = genai.GenerativeModel(**kwargs)
                    response = model.generate_content(prompt)
                    
                    if response and hasattr(response, 'text'):
                        return response.text
                except Exception as e:
                    if "429" in str(e) or "404" in str(e) or "quota" in str(e).lower():
                        continue
                    logger.error(f"❌ Gemini API Error (Key: {key[:6]}..., Model: {m_name}): {e}")
                    break
            
            self._rotate_gemini()
        return None

    async def call_nvidia_deepseek(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Optional[str]:
        if not self.nvidia_keys:
            logger.warning("⚠️ No NVIDIA Keys available in NVIDIA_KEYS")
            return None
        
        base_url = os.getenv("NVIDIA_BASE_URL", NVIDIA_BASE_URL)
        model = "deepseek-ai/deepseek-v3.1"

        for _ in range(len(self.nvidia_keys)):
            key = self._get_next_nvidia_key()
            try:
                client = OpenAI(api_key=key, base_url=base_url)
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"} if json_mode else None,
                    temperature=0.7 if not json_mode else 0.1,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"❌ NVIDIA Provider Error (Key: {key[:6]}...): {e}")
                self._rotate_nvidia()
        return None

# Global instance
ai_manager = AIModelManager()

def configure_genai():
    """Confirms AI Engine is ready."""
    if not GEMINI_KEYS and not NVIDIA_API_KEY:
        logger.error("No AI API Keys found in .env")
        return False
    logger.info("AI Service Manager Initialized Successfully (Gemini & NVIDIA Swap Ready).")
    return True

async def get_ai_response(user_msg: str, context: List[Any], intent: Dict[str, Any], type: str = "chat") -> str:
    """
    Generates a response using Gemini 2.0 Flash with NVIDIA fallback.
    """
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

    # Try Gemini 2.0 Flash (Primary)
    response = await ai_manager.call_gemini(user_msg, system_instruction=system_prompt, model_name="gemini-2.0-flash")
    if response: return response

    # Fallback: NVIDIA DeepSeek
    logger.warning("Falling back to NVIDIA DeepSeek for chat response.")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    response = await ai_manager.call_nvidia_deepseek(messages)
    if response: return response

    return "Hệ thống AI đang bảo trì. Anh chị chờ chút nhé! 🛠️"

async def extract_search_intent(query: str, categories: Optional[List[str]] = None, expert_menu: List[str] = [], topic_menu: List[str] = []) -> Dict[str, Any]:
    """
    Extract search filters using NVIDIA DeepSeek V3.1 (Primary) or Gemini (Fallback).
    """
    expert_menu_str = ", ".join(expert_menu[:100]) if expert_menu else "AI, Marketing, Blockchain"
    topic_menu_str = ", ".join(topic_menu[:100]) if topic_menu else "RAG, Smart Contract, SEO"
    
    prompt = f"""
    Bạn là chuyên gia phân tích ý định (Intent Extractor) cho hệ thống Matrix Finder AI.
    Nhiệm vụ: Trích xuất thông tin từ câu hỏi của người dùng sang định dạng JSON.

    Dữ liệu đầu vào: "{query}"

    MENU HỆ THỐNG (Ưu tiên khớp chính xác):
    - Chuyên môn (Expert): {expert_menu_str}
    - Đề tài (Topic): {topic_menu_str}
    - Ý định (Intent): Expert, Topic, Expert + Topic, my_location, hello, thank, angry, help

    QUY TẮC PHÂN LOẠI (QUAN TRỌNG):
    1. Intent 'Expert': Người dùng tìm người hỗ trợ/dạy/cố vấn. 
       Dấu hiệu: "có ai...", "tìm người...", "dạy môn...", "biết về...", "giỏi về...".
    2. Intent 'Topic': Người dùng tìm tài liệu/kiến thức/đề tài.
       Dấu hiệu: "có tài liệu...", "có sách...", "nghiên cứu về...", "thông tin về...".
    3. Expert: Nếu tìm người, hãy trả về tên lĩnh vực từ Menu Chuyên môn. Nếu không có trong menu, trích xuất từ khóa chuyên môn quan trọng nhất (ưu tiên tiếng Anh hoặc tiếng Việt chuẩn).
    4. Topic: Nếu tìm đề tài, tương tự trích xuất từ Menu Đề tài hoặc từ khóa quan trọng.
    5. 'help': Chỉ dùng khi người dùng hỏi về cách dùng hệ thống hoặc hỏi chung chung không rõ mục đích tìm kiếm.

    VÍ DỤ:
    - "có ai dạy môn học máy không?" -> {{"Expert": "Machine Learning", "Topic": false, "Intent": "Expert", "keyword": "học máy"}}
    - "tìm tài liệu RAG" -> {{"Expert": false, "Topic": "RAG", "Intent": "Topic", "keyword": "RAG"}}

    Định dạng đầu ra (Chỉ trả về JSON):
    {{
        "Expert": "string hoặc false",
        "Topic": "string hoặc false",
        "Intent": "chọn từ menu ý định",
        "keyword": "từ khóa gốc quan trọng"
    }}
    """

    # Try NVIDIA DeepSeek V3.1 (Primary for Intent)
    messages = [
        {"role": "system", "content": "You are a specialized Intent Extractor for Matrix Finder AI. Return ONLY JSON."},
        {"role": "user", "content": prompt}
    ]
    response_str = await ai_manager.call_nvidia_deepseek(messages, json_mode=True)
    
    if not response_str:
        # Fallback to Gemini
        logger.warning("Falling back to Gemini for intent extraction.")
        response_str = await ai_manager.call_gemini(prompt + "\n\nIMPORTANT: REMEMBER TO RETURN ONLY JSON.")

    if response_str:
        try:
            import re
            # Aggressive JSON extraction using regex
            json_match = re.search(r'\{.*\}', response_str, re.DOTALL)
            if json_match:
                cleaned_str = json_match.group(0)
                logger.info(f"AI Intent Extracted JSON: {cleaned_str[:100]}...")
                return json.loads(cleaned_str)
            else:
                logger.warning(f"No JSON found in response: {response_str[:100]}...")
        except Exception as e:
            logger.error(f"JSON Parsing Error: {e} | Raw: {response_str}")

    return {"Expert": False, "Topic": False, "Intent": "help"}

async def summarize_and_filter_results(user_msg: str, results_context: List[Any], intent_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantically filter results using Gemini (Primary) or NVIDIA (Fallback).
    """
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

    # Try Gemini 2.0 Flash
    response_str = await ai_manager.call_gemini(prompt + "\n\nIMPORTANT: REMEMBER TO RETURN ONLY JSON.")
    
    if not response_str:
        # Fallback to NVIDIA
        logger.warning("Falling back to NVIDIA DeepSeek for summarize/filter.")
        messages = [
            {"role": "system", "content": "You are Matrix Finder AI Assistant. Filter and summarize results. Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ]
        response_str = await ai_manager.call_nvidia_deepseek(messages, json_mode=True)

    if response_str:
        try:
            if "```json" in response_str:
                response_str = response_str.split("```json")[1].split("```")[0].strip()
            elif "```" in response_str:
                response_str = response_str.split("```")[1].split("```")[0].strip()
            return json.loads(response_str)
        except Exception as e:
            logger.error(f"Summarize/Filter JSON Parsing Error: {e} | Raw: {response_str}")

    return {
        "reply": "Dạ, em tìm thấy một số thông tin phù hợp, mời anh/chị xem chi tiết bên dưới nhé! 🎓✨",
        "kept_expert_ids": [str(r.get('expert_id')) for r in results_context],
        "kept_topic_names": []
    }

async def standardize_address_ai(ward: str, district: str, city: str) -> str:
    """
    Standardizes address components using NVIDIA DeepSeek V3.1 (Primary) or Gemini.
    """
    cache = load_ai_cache()
    raw_key = f"{ward}|{district}|{city}"
    
    if raw_key in cache:
        return cache[raw_key]
        
    prompt = f"""Bạn là chuyên gia về địa lý Việt Nam. 
    Hãy chuẩn hóa địa chỉ sau thành định dạng chuẩn nhất để bản đồ có thể xác định được tọa độ.
    Dữ liệu thô: {ward}, {district}, {city}

    Quy tắc:
    1. Giữ nguyên cấp hành chính: Nếu là "Thị trấn" thì ghi "Thị trấn", không được tự ý đổi thành "Xã".
    2. Giải mã viết tắt: "Q." -> "Quận", "P." -> "Phường", "TP." -> "Thành phố", "TP.HCM" -> "Thành phố Hồ Chí Minh".
    3. Định dạng trả về: "Tên Phường/Xã/Thị trấn, Tên Quận/Huyện/Thị xã/Thành phố thuộc tỉnh, Tên Tỉnh/Thành phố trực thuộc trung ương".
    4. Chỉ trả về 1 dòng địa chỉ duy nhất, không giải thích gì thêm.
    """
    
    # Try NVIDIA DeepSeek V3.1 (Primary)
    messages = [{"role": "user", "content": prompt}]
    clean_addr = await ai_manager.call_nvidia_deepseek(messages)
    
    if not clean_addr:
        # Fallback to Gemini
        clean_addr = await ai_manager.call_gemini(prompt)

    if clean_addr:
        clean_addr = clean_addr.strip()
        cache[raw_key] = clean_addr
        save_ai_cache(cache)
        return clean_addr
    
    return f"{ward}, {district}, {city}"
