from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    latitude: float
    longitude: float

class TopicInfo(BaseModel):
    name: str
    status: str = "Sẵn sàng"
    image_url: str = ""
    link: str = ""
    staff_zalo: Optional[str] = None

class ExpertInfo(BaseModel):
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
    expert_name: Optional[str] = None
    topic_name: str
    chat_context: str
    zalo_contact: str = "" # Now used for Phone Number
    avatar_url: str = "" # New field
    phone: str = "" # Explicit field (map to zalo_contact logic)
    zalo_group_link: str = "" # New field for precise tracking
    timestamp: str = ""
