"""
Upload clean demo data - ADDRESS ONLY, NO COORDINATES
Hệ thống sẽ tự động geocode
"""

import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend_app'))

from services.sheet_service import get_gspread_client
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_SPREADSHEET_ID = os.getenv("PRODUCT_SPREADSHEET_ID", "1FOOZFMQtm43NEW_cP94yq81Gx3RK3Hqp3xJDFEwZqKA")

# === DỮLIỆU CHUYÊN GIA (CHỈ CÓ ADDRESS, KHÔNG CÓ LAT/LNG) ===
experts_data = [
    # Header row - XÓA latitude/longitude
    ["expert_id", "expert_name", "avatar_url", "expertise", "categories", "address", "zalo_group_link", "notebook_link"],
    
    # Expert 1: AI & Machine Learning  
    ["EXP001", "TS. Lê Quang Hiếu", "https://img.example.com/ai-expert.jpg", 
     "Trí tuệ nhân tạo, Machine Learning, Deep Learning", 
     "AI,Machine Learning,Python,Deep Learning",
     "Landmark 81, Bình Thạnh, TP.HCM",  # CHỈ ADDRESS
     "https://zalo.me/g/ai-community", 
     "https://notebooklm.google.com/notebook/ai-expert"],
    
    # Expert 2: Blockchain & Web3
    ["EXP002", "Anh Nguyễn Văn Blockchain", "https://img.example.com/blockchain.jpg",
     "Blockchain, Web3, Smart Contracts, Cryptocurrency",
     "Blockchain,Web3,Ethereum,DeFi",
     "Vinhomes Central Park, Quận Bình Thạnh, TP.HCM",
     "https://zalo.me/g/blockchain-vn",
     "https://notebooklm.google.com/notebook/blockchain"],
    
    # Expert 3: Digital Marketing
    ["EXP003", "Chị Hoàng Thanh Mai", "https://img.example.com/marketing.jpg",
     "Marketing số, Quảng cáo Facebook, Content Marketing",
     "Marketing,Social Media,Content,SEO",
     "Tòa nhà Bitexco, Quận 1, TP.HCM",
     "https://zalo.me/g/marketing-expert",
     "https://notebooklm.google.com/notebook/marketing"],
    
    # Expert 4: Cloud Architecture
    ["EXP004", "Anh Trần Minh Đức", "https://img.example.com/cloud.jpg",
     "Cloud Computing, AWS, Azure, Kiến trúc Microservices",
     "Cloud,AWS,DevOps,Microservices",
     "Lotte Center, Quận 10, TP.HCM",
     "https://zalo.me/g/cloud-architects",
     "https://notebooklm.google.com/notebook/cloud"],
    
    # Expert 5: Data Science
    ["EXP005", "TS. Phạm Thị Data", "https://img.example.com/data-science.jpg",
     "Khoa học dữ liệu, Phân tích dữ liệu, Machine Learning, Big Data",
     "Data Science,Analytics,Python,R,Big Data",
     "Saigon Centre, Quận 1, TP.HCM",
     "https://zalo.me/g/data-science-vn",
     "https://notebooklm.google.com/notebook/data-science"],
    
    # Expert 6: Mobile Development
    ["EXP006", "Anh Vũ Đức Mobile", "https://img.example.com/mobile.jpg",
     "Lập trình Mobile, Flutter, React Native, iOS & Android",
     "Mobile,Flutter,React Native,iOS,Android",
     "The Gold View, Quận 4, TP.HCM",
     "https://zalo.me/g/mobile-dev",
     "https://notebooklm.google.com/notebook/mobile"],
    
    # Expert 7: Cybersecurity
    ["EXP007", "Mr. Security Expert", "https://img.example.com/security.jpg",
     "An ninh mạng, Penetration Testing, Ethical Hacking",
     "Security,Cybersecurity,Ethical Hacking,Pentesting",
     "Viettel Complex, Quận 10, TP.HCM",
     "https://zalo.me/g/security-experts",
     "https://notebooklm.google.com/notebook/security"],
    
    # Expert 8: UI/UX Design
    ["EXP008", "Chị Ngọc Designer", "https://img.example.com/uiux.jpg",
     "Thiết kế giao diện, UX Research, Product Design",
     "UI/UX,Design,Figma,Product Design",
     "Diamond Plaza, Quận 1, TP.HCM",
     "https://zalo.me/g/designers-vn",
     "https://notebooklm.google.com/notebook/design"],
]

# Topics data (Standardized to English headers)
topics_data = [
    ["expert_id", "expert_name", "expertise", "topic_name", "status", "link", "image_url", "zalo_support"],
    
    ["EXP001", "TS. Lê Quang Hiếu", "AI & Machine Learning", 
     "Xây dựng Chatbot thông minh với RAG", "Miễn phí", 
     "https://notebooklm.google.com/notebook/rag-chatbot", 
     "https://img.example.com/rag.jpg", "0901234567"],
    
    ["EXP001", "TS. Lê Quang Hiếu", "Deep Learning",
     "Training LLM từ đầu đến cuối", "Có phí",
     "https://notebooklm.google.com/notebook/llm-training",
     "https://img.example.com/llm.jpg", "0901234567"],
    
    ["EXP001", "TS. Lê Quang Hiếu", "Computer Vision",
     "Nhận diện đối tượng với YOLO", "Miễn phí",
     "https://notebooklm.google.com/notebook/yolo",
     "https://img.example.com/yolo.jpg", "0901234567"],
    
    ["EXP002", "Anh Nguyễn Văn Blockchain", "Blockchain Basics",
     "Lập trình Smart Contract Solidity", "Miễn phí",
     "https://notebooklm.google.com/notebook/solidity",
     "https://img.example.com/solidity.jpg", "0902345678"],
    
    ["EXP002", "Anh Nguyễn Văn Blockchain", "DeFi",
     "Xây dựng ứng dụng DeFi đầu tiên", "Có phí",
     "https://notebooklm.google.com/notebook/defi",
     "https://img.example.com/defi.jpg", "0902345678"],
    
    ["EXP003", "Chị Hoàng Thanh Mai", "Content Marketing",
     "Viết content hấp dẫn với AI", "Miễn phí",
     "https://notebooklm.google.com/notebook/content-ai",
     "https://img.example.com/content.jpg", "0903456789"],
    
    ["EXP003", "Chị Hoàng Thanh Mai", "Social Media",
     "Xây dựng thương hiệu cá nhân trên LinkedIn", "Miễn phí",
     "https://notebooklm.google.com/notebook/linkedin",
     "https://img.example.com/linkedin.jpg", "0903456789"],
]

def upload_demo_data():
    """Upload demo data - ADDRESS ONLY"""
    print("="*60)
    print("🚀 UPLOADING DATA với ADDRESS ONLY (NO LAT/LNG)")
    print("="*60)
    
    try:
        client = get_gspread_client()
        if not client:
            print("❌ Failed to connect")
            return
        
        sheet = client.open_by_key(KNOWLEDGE_SPREADSHEET_ID)
        
        # Upload Experts
        print("\n📋 Uploading Experts (địa chỉ text only)...")
        experts_sheet = sheet.worksheet("Experts")
        experts_sheet.clear()
        experts_sheet.update("A1", experts_data)
        print(f"✅ Uploaded {len(experts_data)-1} experts")
        
        # Upload Topics
        print("\n📚 Uploading Topics...")
        topics_sheet = sheet.worksheet("Topics")
        topics_sheet.clear()
        topics_sheet.update("A1", topics_data)
        print(f"✅ Uploaded {len(topics_data)-1} topics")
        
        print("\n" + "="*60)
        print("✅ DONE! Hệ thống sẽ TỰ ĐỘNG geocode khi load!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upload_demo_data()
