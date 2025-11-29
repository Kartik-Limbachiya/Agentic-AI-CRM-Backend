from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class CampaignRequest(BaseModel):
    brand_name: str
    goal: str
    audience: str

# Optional: You can define a more specific model for posts if you want strict validation
class SocialPost(BaseModel):
    platform: str
    content: str
    image_idea: Optional[str] = None
    mediaUrl: Optional[str] = None

class CampaignResponse(BaseModel):
    status: str
    plan: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    report: str