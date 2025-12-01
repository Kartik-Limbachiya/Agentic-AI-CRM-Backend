# app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class CampaignRequest(BaseModel):
    """Request model for creating a campaign"""
    brand_name: str = Field(..., description="Brand name for the campaign")
    goal: str = Field(..., description="Campaign goal/objective")
    audience: str = Field(..., description="Target audience description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "TechCorp",
                "goal": "Increase brand awareness and drive product sales",
                "audience": "Tech-savvy professionals aged 25-45 interested in innovation"
            }
        }

class SocialPost(BaseModel):
    """Model for a single social media post"""
    platform: str
    content: str
    image_idea: Optional[str] = None
    mediaUrl: Optional[str] = None
    scheduledDate: Optional[str] = None
    scheduledTime: Optional[str] = None
    status: Optional[str] = "draft"
    posting_strategy: Optional[str] = None
    predicted_engagement: Optional[Dict[str, str]] = None

class ExecutionResult(BaseModel):
    """Model for post execution results"""
    platform: str
    status: str
    id: Optional[str] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    impressions: Optional[int] = None
    reach: Optional[int] = None
    engagement_rate: Optional[float] = None
    executedAt: Optional[str] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None

class CampaignResponse(BaseModel):
    """Response model for campaign execution"""
    status: str
    campaign_id: Optional[str] = None
    plan: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    report: str

class UserInfo(BaseModel):
    """User information model"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    
class CampaignSummary(BaseModel):
    """Summary model for campaign listing"""
    campaign_id: str
    brand_name: str
    goal: str
    status: str
    created_at: datetime
    posts_count: int
    execution_status: Optional[str] = None