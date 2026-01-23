from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import pandas as pd
import httpx
from datetime import datetime, timedelta
from urllib.parse import quote
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time

# --- CONFIGURATION LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- LOAD ENVIRONMENT VARIABLES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..")
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path, override=True)

# --- IMPORTS AFTER ENV LOAD ---
from models import ChatRequest, ChatResponse, ExpertInfo, TopicInfo, LeadRequest
from services.sheet_service import load_expert_system_data, save_lead_to_sheet
from services.geo_service import find_nearest_experts
from services.ai_service import get_ai_response, extract_search_intent, configure_genai
from services.intent_service import handle_expert_search

# --- CONSTANTS ---
SESSION_TIMEOUT_HOURS = 24
ZALO_ACCESS_TOKEN_URL = "https://oauth.zaloapp.com/v4/access_token"
ZALO_GRAPH_API_URL = "https://graph.zalo.me/v2.0/me"
REDIRECT_FRONTEND_PATH = "/index.html"

ZALO_APP_ID = os.environ.get("ZALO_APP_ID", "")
ZALO_APP_SECRET = os.environ.get("ZALO_APP_SECRET", "")

# --- GLOBAL STATE ---
sessions: Dict[str, dict] = {}
experts_dataframe: pd.DataFrame = pd.DataFrame()
topics_dataframe: pd.DataFrame = pd.DataFrame()
unique_categories: List[str] = []
expert_menu: List[str] = []
topic_menu: List[str] = []

# --- FIREBASE INITIALIZATION ---
fb_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
db = None
if fb_path and os.path.exists(fb_path):
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(fb_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("✅ Firebase initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")

# --- LIFESPAN HANDLER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_time = time.time()
    global experts_dataframe, unique_categories, topics_dataframe, expert_menu, topic_menu
    
    logger.info("=" * 60)
    logger.info("🚀 INITIALIZING MATRIX FINDER AI SYSTEM 🚀")
    logger.info("=" * 60)

    # 0. System Info
    logger.info(f"Step 0: System Environment Check...")
    logger.info(f"  - Working Dir   : {os.getcwd()}")
    logger.info(f"  - Server Port   : {os.environ.get('PORT', '9000')}")

    # 1. Environment Check
    logger.info("Step 1: Checking Environment Variables...")
    required_envs = ["DEEPSEEK_API_KEY", "KNOWLEDGE_SPREADSHEET_ID", "GOOGLE_MAPS_API_KEY"]
    for env in required_envs:
        val = os.environ.get(env, "")
        status = "✅ SET" if val else "❌ MISSING"
        masked = val[:6] + "..." if len(val) > 8 else "***"
        logger.info(f"  - {env.ljust(25)}: {status} ({masked})")

    # 2. Firebase Check
    logger.info("Step 2: Verifying Firebase Connection...")
    if db is not None:
        logger.info("  - Firestore Connection: ✅ ACTIVE")
    else:
        logger.warning("  - Firestore Connection: ⚠️ INACTIVE (Key missing?)")

    # 3. Load Expert Data
    logger.info("Step 3: Loading Knowledge Base (Google Sheets)...")
    load_start = time.time()
    experts_dataframe, topics_dataframe, _, expert_menu, topic_menu = await load_expert_system_data()
    load_duration = time.time() - load_start
    
    if not experts_dataframe.empty:
        logger.info(f"  - Experts Loaded: ✅ {len(experts_dataframe)}")
        logger.info(f"  - Topics Loaded : ✅ {len(topics_dataframe)}")
        logger.info(f"  - Load Time     : {load_duration:.2f}s")
    else:
        logger.error("  - Data Load: ❌ FAILED. Critical expert data missing.")

    # 4. AI Engine Configuration
    logger.info("Step 4: Configuring DeepSeek AI Engine...")
    try:
        configure_genai()
        logger.info("  - AI Status: ✅ ONLINE")
    except Exception as e:
        logger.error(f"  - AI Status: ❌ {e}")

    total_duration = time.time() - start_time
    print("-" * 60)
    logger.info(f"SYSTEM READY in {total_duration:.2f}s")
    print("-" * 60 + "\n")

    yield
    logger.info("Shutting down Matrix Finder AI application...")

app = FastAPI(
    title="Matrix Finder AI API",
    description="Connect with Experts and Knowledge Topics",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ZALO AUTH HELPERS ---
async def exchange_zalo_access_token(client: httpx.AsyncClient, code: str, code_verifier: Optional[str] = None) -> str:
    headers = {"secret_key": ZALO_APP_SECRET}
    payload = {
        "code": code,
        "app_id": ZALO_APP_ID,
        "grant_type": "authorization_code",
    }
    if code_verifier:
        payload["code_verifier"] = code_verifier

    response = await client.post(ZALO_ACCESS_TOKEN_URL, headers=headers, data=payload)
    res_data = response.json()
    if "access_token" not in res_data:
        logger.error(f"Zalo Auth Error: {res_data}")
        raise HTTPException(status_code=400, detail=f"Failed to get Zalo access token: {res_data.get('error_description', 'Unknown error')}")
    return res_data["access_token"]

async def get_zalo_user_profile(client: httpx.AsyncClient, access_token: str) -> dict:
    headers = {"access_token": access_token}
    params = {"fields": "id,name,picture"}
    response = await client.get(ZALO_GRAPH_API_URL, headers=headers, params=params)
    user_data = response.json()
    if "id" not in user_data:
        logger.error(f"Zalo Profile Error: {user_data}")
        raise HTTPException(status_code=400, detail="Failed to get Zalo user profile")
    return user_data

# --- ROUTES ---
@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    if experts_dataframe.empty:
        raise HTTPException(status_code=500, detail="Expert data not loaded.")

    try:
        # 1. EXTRACT INTENT (Call 1) - Pass dynamic menus
        search_intent = await extract_search_intent(
            request.message, 
            unique_categories,
            expert_menu=expert_menu,
            topic_menu=topic_menu
        )
        logger.info(f"Expert Search Intent: {search_intent}")
        
        # 2. HANDLE CASE (Offloaded to Intent Service as requested)
        response = await handle_expert_search(
            request.message, 
            request.latitude, 
            request.longitude, 
            experts_dataframe, 
            unique_categories, 
            search_intent
        )
        return response

    except Exception as e:
        logger.error(f"Error in chat processing: {e}")
        return ChatResponse(reply="Hệ thống đang bận, vui lòng thử lại sau.", nearest_experts=[])

@app.get("/debug/experts")
async def debug_experts():
    """Debug endpoint to inspect loaded expert data"""
    if experts_dataframe.empty:
        return {"error": "No data loaded", "count": 0}
    
    sample = experts_dataframe.head(3).to_dict('records')
    return {
        "count": len(experts_dataframe),
        "columns": list(experts_dataframe.columns),
        "sample_data": sample,
        "categories": unique_categories
    }

@app.get("/api/auth/zalo/verify")
async def zalo_callback(code: str = None, state: str = None, error: str = None, code_verifier: str = None):
    if error:
        return HTMLResponse(f"<html><body><h1>Đăng nhập thất bại</h1><p>{error}</p></body></html>", status_code=400)
    if not code:
        return HTMLResponse(f"<html><body><h1>Thiếu mã xác thực</h1></body></html>", status_code=400)
    
    try:
        async with httpx.AsyncClient() as client:
            access_token = await exchange_zalo_access_token(client, code, code_verifier)
            user_data = await get_zalo_user_profile(client, access_token)
            
            session_id = f"zalo_{user_data['id']}_{time.time()}"
            sessions[session_id] = {
                "user_id": user_data["id"],
                "name": user_data.get("name", "User"),
                "picture": user_data.get("picture", {}).get("data", {}).get("url", ""),
                "login_time": datetime.now().isoformat(),
                "type": "zalo"
            }
            
            encoded_name = quote(user_data.get("name", "User"))
            user_pic = user_data.get("picture", {}).get("data", {}).get("url", "")
            redirect_url = f"{REDIRECT_FRONTEND_PATH}?session_id={session_id}&user_type=zalo&user_name={encoded_name}&user_picture={quote(user_pic) if user_pic else ''}&login_time={datetime.now().isoformat()}"
            
            if state and '|' in state:
                parts = state.split('|')
                if len(parts) >= 2:
                    redirect_url += f"&share={parts[1]}"
            
            return HTMLResponse(f"<html><body><script>window.location.href = '{redirect_url}';</script></body></html>")
    except Exception as e:
        logger.error(f"Auth Error: {e}")
        return HTMLResponse(f"<html><body><h1>Lỗi hệ thống</h1><p>{str(e)}</p></body></html>", status_code=500)

@app.get("/auth/verify")
async def verify_session(session_id: str = None):
    if not session_id or session_id not in sessions:
        return {"valid": False}
    session = sessions[session_id]
    if datetime.now() - datetime.fromisoformat(session["login_time"]) > timedelta(hours=SESSION_TIMEOUT_HOURS):
        del sessions[session_id]
        return {"valid": False}
    return {"valid": True, "user": {"name": session["name"], "type": session["type"]}}

@app.post("/api/share")
async def share_chat(request: dict):
    if db is None:
        raise HTTPException(status_code=503, detail="Sharing feature unavailable")
    try:
        share_id = str(uuid.uuid4())
        db.collection("shared_chats").document(share_id).set({
            "share_id": share_id,
            "messages": request.get("messages", []),
            "user_info": request.get("user_info", {}),
            "createdAt": firestore.SERVER_TIMESTAMP
        })
        return {"share_id": share_id}
    except Exception as e:
        logger.error(f"Error sharing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/share/{share_id}")
async def get_shared_chat(share_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Sharing feature unavailable")
    try:
        doc = db.collection("shared_chats").document(share_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Shared chat not found")
        return doc.to_dict()
    except Exception as e:
        logger.error(f"Error retrieving shared chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expert-info/{expert_id}")
async def get_expert_info(expert_id: str):
    if experts_dataframe.empty:
        return {"error": "Data not loaded"}
    expert = experts_dataframe[experts_dataframe['expert_id'].astype(str) == str(expert_id)]
    if expert.empty:
        return {"error": "Expert not found"}
    row = expert.iloc[0]
    return {
        "expert_name": row.get('expert_name'),
        "expertise": row.get('expertise'),
        "address": row.get('address'),
        "zalo_link": row.get('zalo_group_link'),
        "notebook_link": row.get('notebook_link'),
        "topics": row.get('topics_json', [])
    }

@app.post("/api/submit-lead")
async def submit_lead(lead: LeadRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received interest for Topic: {lead.topic_name} by Expert: {lead.expert_name} from {lead.user_name}")
    if not lead.timestamp:
        lead.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    background_tasks.add_task(save_lead_to_sheet, lead.model_dump() if hasattr(lead, "model_dump") else lead.dict())
    return {"status": "success", "message": "Interest recorded"}

@app.get("/api/config")
async def get_frontend_config():
    port = os.environ.get("PORT", "9000")
    base_url = f"http://localhost:{port}"
    final_redirect = os.environ.get("ZALO_REDIRECT_URI") or f"{base_url}/auth/zalo/callback"
    return {
        "zalo_app_id": ZALO_APP_ID,
        "zalo_redirect_uri": final_redirect,
        "google_maps_api_key": os.environ.get("GOOGLE_MAPS_API_KEY", "")
    }

@app.get("/auth/zalo/callback", response_class=HTMLResponse)
async def zalo_callback_page():
    file_path = os.path.join(os.path.dirname(__file__), "..", "zalo_callback.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return Response(status_code=404, content="Callback file not found")

app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), ".."), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 9000)))
