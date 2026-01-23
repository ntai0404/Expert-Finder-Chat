import pandas as pd
import logging
import json
from typing import Dict, Any, List, Optional
from services.ai_service import summarize_and_filter_results
from services.geo_service import find_nearest_experts
from models import TopicInfo, ExpertInfo, ChatResponse

from services.expert_service import search_experts, map_to_expert_info

logger = logging.getLogger(__name__)

async def handle_expert_search(user_message: str, latitude: float, longitude: float, experts_df: pd.DataFrame, unique_categories: List[str], search_intent: Dict[str, Any]) -> ChatResponse:
    """
    Core logic for Matrix Finder AI based on usecase.md UC2.
    Handles branches 3.1 to 3.6.
    """
    try:
        intent = search_intent.get("Intent", "help")
        expert_query = search_intent.get("Expert", False)
        topic_query = search_intent.get("Topic", False)

        # 3.1. Social / Emotional
        if intent in ["hello", "thank", "angry"]:
            filter_data = await summarize_and_filter_results(user_message, [], search_intent)
            return ChatResponse(reply=filter_data.get("reply", ""), nearest_experts=[])

        # 3.4. My Location
        if intent == "my_location":
            return ChatResponse(
                reply="Đang xác định vị trí của bạn để cập nhật bản đồ tri thức... 📍✨", 
                nearest_experts=[], 
                trigger_location=True
            )

        # 3.6. Help
        if intent == "help":
            reply = "Dạ, em là Matrix Finder AI - Trợ lý kết nối tri thức. Anh/chị có thể hỏi em tìm chuyên gia (vd: 'Tìm cố vấn AI') hoặc tìm đề tài học tập (vd: 'Có tài liệu về RAG không?') nhé! 🎓✨"
            return ChatResponse(reply=reply, nearest_experts=[])

        # 3.2, 3.3, 3.5. Search Branches (Expert, Topic, or Both)
        # We use a combined search logic but filter the output based on intent
        
        # Step 1: Raw Search in Database
        raw_results = search_experts(
            experts_df=experts_df,
            expertise_query=expert_query if expert_query else None,
            topic_query=topic_query if topic_query else None,
            user_lat=latitude,
            user_lng=longitude,
            limit=20
        )
        
        if not raw_results:
            # Handle 4.2 / 4.3 Exceptions
            if intent == "Expert":
                msg = "Dạ, hiện tại Matrix Finder AI chưa có sẵn thông tin về chuyên gia phù hợp với yêu cầu của anh/chị ạ. 🎓"
            elif intent == "Topic":
                msg = "Dạ, hiện tại hệ thống chưa có sẵn thông tin về đề tài nghiên cứu này. Anh/chị có thể thử với từ khóa khác nhé! ✨"
            else:
                msg = "Dạ, em chưa tìm thấy chuyên gia hay tài liệu nào phù hợp với yêu cầu này ạ."
            return ChatResponse(reply=msg, nearest_experts=[])

        # Step 2: Semantic Filtering & Summary (Call 2)
        # We send the results context to LLM to filter false positives and generate the reply
        filter_data = await summarize_and_filter_results(user_message, raw_results, search_intent)
        ai_reply = filter_data.get("reply", "")
        kept_expert_ids = [str(eid) for eid in filter_data.get("kept_expert_ids", [])]
        kept_topic_names = [str(tn).lower() for tn in filter_data.get("kept_topic_names", [])]
        
        # Step 3: Final Mapping & Topic Filtering
        expert_info_list = []
        for exp in raw_results:
            expert_id = str(exp.get('expert_id'))
            
            # Only keep expert if AI confirmed it
            if kept_expert_ids and expert_id not in kept_expert_ids:
                continue
                
            expert_obj = map_to_expert_info([exp])[0]
            
            # Case 3.3 (Topic filtering)
            if intent in ["Topic", "Expert + Topic"] and kept_topic_names:
                # Filter individual topics to only those that AI kept
                relevant_topics = []
                for topic in expert_obj.topics:
                    if topic.name.lower() in kept_topic_names:
                        relevant_topics.append(topic)
                
                # Only add expert if they have at least one relevant topic (or if intent was Expert+Topic)
                if relevant_topics:
                    expert_obj.topics = relevant_topics
                    expert_info_list.append(expert_obj)
                elif intent == "Expert + Topic":
                    # Keep expert even if topic mismatch if searching for both
                    expert_info_list.append(expert_obj)
            else:
                # Default behavior
                expert_info_list.append(expert_obj)

        return ChatResponse(reply=ai_reply, nearest_experts=expert_info_list[:10])

    except Exception as e:
        logger.error(f"Error in Intent Service: {e}")
        return ChatResponse(reply="Matrix Finder AI đang gặp chút gián đoạn kỹ thuật, anh chị vui lòng thử lại sau nhé! 🛠️", nearest_experts=[])
