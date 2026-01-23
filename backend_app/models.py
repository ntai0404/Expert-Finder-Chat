from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    latitude: float
    longitude: float

class TopicInfo(BaseModel):
    name: str
    description: str = ""
    status: str = "Sẵn sàng"
    image_url: str = ""
    link: str = ""
    staff_zalo: Optional[str] = None

class ExpertInfo(BaseModel):
    expert_id: Optional[str] = None
    name: str
    expertise: str
    address: str
    lat: float
    lng: float
    distance_km: float
    zalo_link: Optional[str] = None
    notebook_link: Optional[str] = None
    avatar_url: Optional[str] = None
    topics: List[TopicInfo] = []

class ChatResponse(BaseModel):
    reply: str
    nearest_experts: List[ExpertInfo] = []
    trigger_location: bool = False

class LeadRequest(BaseModel):
    user_name: Optional[str] = "Khách"
    user_id: Optional[str] = None
    expert_id: Optional[str] = None
    topic_id: Optional[str] = None
    expert_name: Optional[str] = None
    topic_name: Optional[str] = None
    chat_context: str
    action: str = "Click Zalo"
    timestamp: str = ""
