import pandas as pd
import logging
from typing import List, Dict, Any
from models import ExpertInfo, TopicInfo
from services.geo_service import find_nearest_experts

logger = logging.getLogger(__name__)

def search_experts(
    experts_df: pd.DataFrame, 
    expertise_query: str = None, 
    topic_query: str = None,
    user_lat: float = None, 
    user_lng: float = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    try:
        logger.info(f"🔎 search_experts called with: expertise_query='{expertise_query}', topic_query='{topic_query}', limit={limit}")
        
        # 0. Prep query keywords (Normalize: lower + no spaces for matching)
        def normalize(text):
            return str(text).lower().replace(" ", "") if text else ""

        q_expertise = normalize(expertise_query)
        q_topic = normalize(topic_query)
        
        if not q_expertise and not q_topic:
            logger.warning("⚠️ search_experts called with NO active filters. Returning empty results to prevent leak.")
            return []

        logger.info(f"📋 Input DataFrame: {len(experts_df)} experts")
        
        # 1. Parallel Search (Cross-field)
        matches = []
        results_df = experts_df.copy()
        for idx, row in results_df.iterrows():
            # Data normalization
            exp_text = normalize(row.get('expertise', ''))
            cat_text = normalize(row.get('categories', ''))
            topics_list = row.get('topics_json', [])
            
            # Combine all topic names into one string for easier searching
            topics_combined = "".join([normalize(t.get('name', '')) for t in topics_list if isinstance(t, dict)])
            
            # BIG POOL: Search in all fields
            pool = f"{exp_text}|{cat_text}|{topics_combined}"
            
            is_match = False
            # If AI extracted expertise, check pool
            if q_expertise and q_expertise in pool:
                is_match = True
            # If AI extracted topic, check pool
            if q_topic and q_topic in pool:
                is_match = True
            
            matches.append(is_match)

        # 2. Apply matches
        results_df = results_df[matches]
        logger.info(f"📊 After cross-field filter: {len(results_df)} experts found")

        # 3. Geographic Search (if results found)
        if results_df.empty:
            logger.warning("❌ No matches found after cross-field search, returning []")
            return []

        if user_lat and user_lng:
            nearest_experts = find_nearest_experts(user_lat, user_lng, results_df, limit=limit)
            logger.info(f"📍 Geographic search returned {len(nearest_experts)} experts")
        else:
            nearest_experts = results_df.head(limit).to_dict('records')
            logger.info(f"📋 No location provided, returning top {len(nearest_experts)} experts")
            for item in nearest_experts:
                if 'distance_km' not in item:
                    item['distance_km'] = 0.0

        return nearest_experts
        
    except Exception as e:
        logger.error(f"❌ Error in search_experts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def map_to_expert_info(raw_experts: List[Dict[str, Any]]) -> List[ExpertInfo]:
    """
    Transform raw dictionary data from database/geo_service to ExpertInfo Pydantic models.
    """
    expert_info_list = []
    
    for item in raw_experts:
        # Map topics
        topics_raw = item.get('topics_json', []) or item.get('topics', [])
        topic_list = []
        
        for t in topics_raw:
            topic_list.append(TopicInfo(
                name=t.get('topic_name') or t.get('name', 'Kiến thức chuyên môn'),
                status=t.get('status', 'Sẵn sàng'),
                link=t.get('link/LLM') or t.get('link', ''),
                image_url=t.get('link_img') or t.get('image_url', ''),
                description=t.get('description', '')
            ))
            
        expert_info_list.append(ExpertInfo(
            expert_id=str(item.get('expert_id', '')),
            name=item.get('expert_name', 'Chuyên gia'),
            expertise=item.get('expertise', ''),
            address=item.get('address', ''),
            lat=float(item.get('latitude', 0.0)),
            lng=float(item.get('longitude', 0.0)),
            distance_km=float(item.get('distance_km', 0.0)),
            zalo_link=item.get('zalo_group_link') or item.get('zalo_link'),
            notebook_link=item.get('notebook_link'),
            avatar_url=item.get('avatar_url'),
            topics=topic_list
        ))
        
    return expert_info_list

if __name__ == "__main__":
    # Quick test with mock data
    mock_df = pd.DataFrame([
        {
            "expert_id": "1",
            "expert_name": "Dr. Smith",
            "expertise": "AI, Machine Learning",
            "categories": "Công nghệ",
            "address": "TP.HCM",
            "latitude": 10.7,
            "longitude": 106.6,
            "topics_json": [{"Chủ đề tri thức": "Neural Networks", "Trạng thái": "Mới"}]
        }
    ])
    
    print("Testing search...")
    res = search_experts(mock_df, expertise_query="AI", user_lat=10.7, user_lng=106.6)
    print(f"Results: {len(res)}")
    
    print("Testing mapping...")
    models = map_to_expert_info(res)
    print(f"Models: {models}")
