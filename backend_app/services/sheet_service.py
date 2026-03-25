import pandas as pd
import os
import gspread

# Import from geo_service
from services.geo_service import geocode_address, build_address, load_cache, apply_jitter

# Import from ai_service
from services.ai_service import standardize_address_ai
import logging

logger = logging.getLogger(__name__)

# Google Sheets Configuration
# Google Sheets Configuration
KNOWLEDGE_SPREADSHEET_ID = os.getenv("KNOWLEDGE_SPREADSHEET_ID", "1FOOZFMQtm43NEW_cP94yq81Gx3RK3Hqp3xJDFEwZqKA")
LEAD_SPREADSHEET_ID = os.getenv("LEAD_SPREADSHEET_ID", "1N5XoXSnMKLXKtv8b_o-yZjZ9a2XVB2_9T6WRshU0ziE")

# Specific Sheet Names for Matrix Finder AI
EXPERT_SHEET_NAME = "Experts"
TOPIC_SHEET_NAME = "Topics"
MESSAGE_LOG_SHEET_NAME = "message_log"

def get_gspread_client():
    """Shared authentication logic for gspread"""
    try:
        key_file_path = os.environ.get("GOOGLE_SHEET_KEY_PATH", "ggsheet-key.json").strip('"').strip("'")
        
        # Robust path resolution if run from subdirectory
        if not os.path.isabs(key_file_path) and not os.path.exists(key_file_path):
            # Try looking in parent directory (if run from backend_app)
            parent_path = os.path.join("..", key_file_path)
            if os.path.exists(parent_path):
                key_file_path = parent_path

        if os.path.exists(key_file_path):
            client = gspread.service_account(filename=key_file_path)
            # logger.info(f"  ✓ Connected using key file: {key_file_path}")
            return client
        
        # Fallback to Env vars
        private_key = os.environ.get("GOOGLE_PRIVATE_KEY")
        client_email = os.environ.get("GOOGLE_CLIENT_EMAIL")
        if private_key and client_email:
            if "\\n" in private_key:
                private_key = private_key.replace("\\n", "\n")
            creds_dict = {
                "type": "service_account",
                "project_id": os.environ.get("GOOGLE_PROJECT_ID", ""),
                "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
                "private_key": private_key,
                "client_email": client_email,
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_CERT_URL", "")
            }
            return gspread.service_account_from_dict(creds_dict)
        return None
    except Exception as e:
        print(f"  ✗ Gspread Auth Error: {e}")
        return None

def load_expert_data():
    """Load both Experts and Topics from Google Sheets using gspread for reliability"""
    logger.info(f"📥 Loading expert data from: {KNOWLEDGE_SPREADSHEET_ID}")
    
    try:
        client = get_gspread_client()
        if not client:
            logger.error("  ✗ Failed to initialize Google Sheets client (Auth error)")
            return pd.DataFrame(), pd.DataFrame()

        sheet = client.open_by_key(KNOWLEDGE_SPREADSHEET_ID)
        
        # 1. Load Experts
        try:
            experts_ws = sheet.worksheet(EXPERT_SHEET_NAME)
            experts_data = experts_ws.get_all_records()
            experts_df = pd.DataFrame(experts_data)
            logger.info(f"  ✓ Experts: {len(experts_df)} entries (Tab: '{EXPERT_SHEET_NAME}')")
            logger.info(f"  ✓ Expert Columns: {list(experts_df.columns)}")
        except gspread.WorksheetNotFound:
            logger.error(f"  ✗ Tab '{EXPERT_SHEET_NAME}' not found.")
            experts_df = pd.DataFrame()
        except Exception as e:
            logger.error(f"  ✗ Error reading Experts: {e}")
            experts_df = pd.DataFrame()

        # 2. Load Topics
        try:
            topics_ws = sheet.worksheet(TOPIC_SHEET_NAME)
            topics_data = topics_ws.get_all_records()
            topics_df = pd.DataFrame(topics_data)
            logger.info(f"  ✓ Topics: {len(topics_df)} entries (Tab: '{TOPIC_SHEET_NAME}')")
            logger.info(f"  ✓ Topic Columns: {list(topics_df.columns)}")
        except gspread.WorksheetNotFound:
            logger.warning(f"  ✗ Tab '{TOPIC_SHEET_NAME}' not found.")
            topics_df = pd.DataFrame()
        except Exception as e:
            logger.error(f"  ✗ Error reading Topics: {e}")
            topics_df = pd.DataFrame()
        
        return experts_df, topics_df
    except Exception as e:
        logger.error(f"  ✗ Global Data Load Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Safe Anchors for problematic areas where OSM fails or lands in sea
SAFE_ANCHORS = {
    "Huyện Giao Thủy": (20.252, 106.519), # Ngô Đồng Town Center
    "Huyện Vĩnh Tường": (21.256, 105.478), # Vĩnh Tường Town Center
    "Huyện Hoài Đức": (21.02, 105.71),
    "Huyện Thanh Thủy": (21.12, 105.29)
}

async def process_experts(experts_df, topics_df):
    """Integrate topics into experts and standardize location"""
    logger.info(f"🧠 Processing {len(experts_df)} experts and their topics...")
    
    experts_list = []
    
    for _, row in experts_df.iterrows():
        expert_id = str(row.get('expert_id', ''))
        expert_name = str(row.get('expert_name', 'Unknown Expert'))
        
        # Get topics for this expert (Sheet uses standardized 'expert_id')
        expert_topics_df = topics_df[topics_df['expert_id'].astype(str) == expert_id]
        
        # ALWAYS geocode from address (không lấy lat/lng từ Sheet)
        address = str(row.get('address', ''))
        
        if address and len(address.strip()) > 3:
            geocode_cache = load_cache()
            coords = geocode_address(address, geocode_cache)
            if coords:
                lat, lng = coords
                logger.info(f"  ✅ Geocoded '{expert_name}': {address} → ({lat:.5f}, {lng:.5f})")
            else:
                logger.warning(f"  ⚠️ Geocode failed for '{expert_name}': {address}, using default TP.HCM")
                lat, lng = (10.762622, 106.660172)  # Default TP.HCM
        else:
            logger.warning(f"  ⚠️ No address for '{expert_name}', using default TP.HCM")
            lat, lng = (10.762622, 106.660172)
        
        expert = {
            'expert_id': expert_id,
            'expert_name': expert_name,
            'avatar_url': row.get('avatar_url', ''),
            'expertise': row.get('expertise', row.get('kinh_nghiem', '')),
            'address': row.get('address', ''),
            'latitude': float(lat),
            'longitude': float(lng),
            'zalo_group_link': row.get('zalo_group_link', ''),
            'notebook_link': row.get('notebook_link', ''),
            # Relational Mapping: Topics now use topic_name, description, status, link/LLM, link_img
            'topics_json': expert_topics_df.rename(columns={
                'topic_name': 'name',
                'description': 'description',
                'status': 'status',
                'link/LLM': 'link',
                'link_img': 'image_url'
            }).to_dict('records')
        }
        experts_list.append(expert)
    
    return pd.DataFrame(experts_list)

async def load_expert_system_data():
    """Main function to load and process expert data"""
    logger.info("=" * 60)
    logger.info("LOADING MATRIX FINDER AI KNOWLEDGE BASE")
    logger.info("=" * 60)
    
    experts_df, topics_df = load_expert_data()
    
    if experts_df.empty:
        logger.error("❌ No expert data loaded from Sheets")
        return pd.DataFrame(), pd.DataFrame(), [], [], []
    
    processed_experts_df = await process_experts(experts_df, topics_df)
    
    logger.info("=" * 60)
    logger.info(f"✅ DATA LOAD SUCCESS: {len(processed_experts_df)} experts")
    logger.info("=" * 60)
    
    # Get Dynamic Menus (User Requirement 5)
    expert_menu = []
    # Search for 'expertise' or 'kinh_nghiem'
    exp_col = 'kinh_nghiem' if 'kinh_nghiem' in experts_df.columns else 'expertise'
    if exp_col in experts_df.columns:
        exp_series = experts_df[exp_col].dropna().astype(str).str.split(',')
        expert_menu = sorted(list(set([item.strip() for sublist in exp_series for item in sublist if item.strip()])))
    
    topic_menu = []
    # New Topic Menu Source: 'topic_name'
    tp_col = 'topic_name'
    if tp_col in topics_df.columns:
        topic_menu = sorted(list(set(topics_df[tp_col].dropna().astype(str).tolist())))

    return processed_experts_df, topics_df, [], expert_menu, topic_menu

def save_lead(lead_data: dict) -> bool:
    """
    Save lead data to Google Sheet 'Leads' (Tab: message).
    Data format: {timestamp, user_name, user_id, topic_name, expert_name, context, zalo_contact, status}
    """
    try:
        client = get_gspread_client()
        if not client:
             raise FileNotFoundError(f"Authentication Failed: No key file and no Env Vars.")

        # 2. Open Sheet and Tab
        sheet = client.open_by_key(LEAD_SPREADSHEET_ID)
        worksheet = sheet.worksheet(MESSAGE_LOG_SHEET_NAME)
        
        # 3. Prepare Row (Following Sheet 3 schema in plan_sheet.md)
        row = [
            lead_data.get('timestamp', ''),
            lead_data.get('user_name', 'Khách'),
            lead_data.get('user_id', ''),
            lead_data.get('expert_id', ''),
            lead_data.get('topic_id', ''),
            lead_data.get('chat_context', ''),
            lead_data.get('action', 'Click Zalo')
        ]
        
        # 4. Append
        worksheet.append_row(row)
        logger.info(f"✅ Lead saved: {lead_data.get('user_name')} - {phone_val}")
        return True
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error saving lead: {e}")
        # traceback.print_exc() 
        return False

if __name__ == '__main__':
    # Test loading
    experts_df, topics_df = load_expert_data()
    if not experts_df.empty:
        print("\nSample data:")
        print(experts_df.head())
        print(f"\nColumns: {list(experts_df.columns)}")

save_lead_to_sheet = save_lead
