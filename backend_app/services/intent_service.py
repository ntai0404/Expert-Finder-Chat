import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from services.ai_service import get_ai_response
from services.geo_service import find_nearest_experts
from models import TopicInfo, ExpertInfo, ChatResponse

from services.expert_service import search_experts, map_to_expert_info

logger = logging.getLogger(__name__)

async def handle_expert_search(user_message: str, latitude: float, longitude: float, experts_df: pd.DataFrame, unique_categories: List[str], search_intent: Dict[str, Any]) -> ChatResponse:
    """
    Core logic for handling different intent cases for Expert Finder.
    Delegates result fulfillment to expert_service.
    """
    try:
        # Case 1: Social or Emotional Interaction
        if search_intent.get('is_social_or_emotional'):
            reply = await get_ai_response(user_message, [], search_intent)
            return ChatResponse(reply=reply, nearest_experts=[])

        # Case 2: General Inquiry
        if search_intent.get('is_general_inquiry'):
            reply = await get_ai_response(user_message, [], search_intent)
            return ChatResponse(reply=reply, nearest_experts=[])
        
        # Case 3: Explicit Location Request
        if search_intent.get('is_location_request'):
            return ChatResponse(
                reply="Đang xác định vị trí của bạn để kết nối với các chuyên gia gần nhất... 📍✨", 
                nearest_experts=[], 
                trigger_location=True
            )
        
        # Case 4: Educational / Expertise Search
        expertise_required = search_intent.get('expertise')
        topic_required = search_intent.get('topic')
        
        logger.info(f"🔍 Intent: expertise='{expertise_required}', topic='{topic_required}'")
        
        # Delegate filtering and geographic search to specialized service
        nearest_data = search_experts(
            experts_df=experts_df,
            expertise_query=expertise_required,
            topic_query=topic_required,
            user_lat=latitude,
            user_lng=longitude,
            limit=5
        )
        
        logger.info(f"📊 Initial search found {len(nearest_data)} experts")
        
        if not nearest_data:
            # NO Fallback: We only want relevant experts
            logger.warning("⚠️ No matches found for the criteria.")
            reply = await get_ai_response(user_message, [], search_intent)
        else:
            # AI contextual reply based on found experts
            reply = await get_ai_response(user_message, nearest_data, search_intent)
        
        # Final mapping to Pydantic models for frontend
        expert_info_list = map_to_expert_info(nearest_data)
        logger.info(f"✅ Returning {len(expert_info_list)} expert cards")
            
        return ChatResponse(reply=reply, nearest_experts=expert_info_list)

    except Exception as e:
        logger.error(f"Error in Intent Service: {e}")
        return ChatResponse(reply="Em đang gặp chút gián đoạn kỹ thuật, anh chị vui lòng thử lại sau nhé! 🛠️", nearest_experts=[])
