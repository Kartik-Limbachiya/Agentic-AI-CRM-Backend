# import os
# import uvicorn
# from datetime import datetime
# from fastapi import FastAPI, HTTPException, Depends, Header
# from fastapi.middleware.cors import CORSMiddleware
# from typing import Optional

# # Import models
# from app.models import CampaignRequest, CampaignResponse, UserInfo
# # Import the compiled graph
# from app.agent import app_graph
# # Import Firebase service
# from app.firebase_config import firebase_service

# # --- FASTAPI SETUP ---
# app = FastAPI(
#     title="Agentic CRM API",
#     description="AI-Powered Campaign Planner & Executor using LangGraph with Firebase",
#     version="2.0.0"
# )

# # Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- AUTHENTICATION DEPENDENCY ---
# async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
#     """
#     Verify Firebase ID token from Authorization header
#     Returns user_id if valid, None otherwise
#     """
#     if not authorization:
#         return None
    
#     try:
#         # Extract token from "Bearer <token>"
#         if authorization.startswith("Bearer "):
#             token = authorization.split("Bearer ")[1]
#             user_info = firebase_service.verify_user_token(token)
#             return user_info['uid'] if user_info else None
#     except Exception as e:
#         print(f"Token verification error: {e}")
#         return None
    
#     return None

# # --- ENDPOINTS ---

# @app.get("/")
# def root():
#     """Root endpoint to verify API availability."""
#     return {
#         "service": "Agentic CRM API",
#         "status": "active",
#         "version": "2.0.0",
#         "features": [
#             "AI Campaign Planning",
#             "Multi-platform Scheduling",
#             "Real-time Execution",
#             "Performance Analytics",
#             "Firebase Integration",
#             "User Authentication"
#         ],
#         "documentation": "/docs"
#     }

# @app.get("/health")
# def health_check():
#     """Health check endpoint for monitoring."""
#     return {
#         "status": "healthy",
#         "service": "agentic-crm-backend",
#         "timestamp": datetime.now().isoformat(),
#         "firebase": "connected"
#     }

# @app.post("/campaign/run", response_model=CampaignResponse)
# async def run_campaign(
#     request: CampaignRequest,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Triggers the full Agentic Workflow: Plan -> Execute -> Report
#     With Firebase integration for data persistence
#     """
#     print(f"\n=== 🚀 RECEIVED CAMPAIGN REQUEST ===")
#     print(f"Brand: {request.brand_name}")
#     print(f"Goal: {request.goal}")
#     print(f"User ID: {user_id or 'anonymous'}")
    
#     try:
#         # Use provided user_id or generate anonymous ID
#         effective_user_id = user_id or "anonymous"
        
#         # 1. Create campaign in Firebase
#         campaign_id = firebase_service.create_campaign(
#             user_id=effective_user_id,
#             campaign_data={
#                 "brand_name": request.brand_name,
#                 "goal": request.goal,
#                 "audience": request.audience
#             }
#         )
        
#         # Log activity
#         firebase_service.log_campaign_activity(
#             campaign_id,
#             "campaign_started",
#             {"brand": request.brand_name, "goal": request.goal}
#         )
        
#         # 2. Construct the Initial State
#         initial_state = {
#             "brand_name": request.brand_name,
#             "goal": request.goal,
#             "audience": request.audience,
#             "posts": [],
#             "execution_results": [],
#             "final_report": "",
#             "status": "started",
#             "campaign_id": campaign_id,
#             "user_id": effective_user_id
#         }
        
#         # 3. Update status to planning
#         firebase_service.update_campaign_status(campaign_id, "planning")
#         firebase_service.log_campaign_activity(campaign_id, "planning_started")
        
#         # 4. Invoke the LangGraph Agent (Planning Phase)
#         print("🤖 Starting Planning Phase...")
#         final_state = app_graph.invoke(initial_state)
        
#         # 5. Save posts to Firebase
#         if final_state.get('posts'):
#             firebase_service.save_campaign_posts(campaign_id, final_state['posts'])
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "planning_completed",
#                 {"posts_generated": len(final_state['posts'])}
#             )
        
#         # 6. Save execution results to Firebase
#         if final_state.get('execution_results'):
#             firebase_service.save_execution_results(campaign_id, final_state['execution_results'])
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "execution_completed",
#                 {"posts_executed": len(final_state['execution_results'])}
#             )
        
#         # 7. Save report to Firebase
#         if final_state.get('final_report'):
#             firebase_service.save_campaign_report(campaign_id, final_state['final_report'])
#             firebase_service.log_campaign_activity(campaign_id, "report_generated")
        
#         # 8. Increment user's campaign count
#         if user_id:
#             firebase_service.increment_user_campaigns(effective_user_id)
        
#         print("=== ✅ WORKFLOW COMPLETED ===")
        
#         # 9. Return the results with campaign_id
#         return {
#             "status": "success",
#             "campaign_id": campaign_id,
#             "plan": final_state.get('posts', []),
#             "results": final_state.get('execution_results', []),
#             "report": final_state.get('final_report', "No report generated.")
#         }
        
#     except Exception as e:
#         print(f"❌ ERROR RUNNING CAMPAIGN: {str(e)}")
        
#         # Log error to Firebase if campaign was created
#         if 'campaign_id' in locals():
#             firebase_service.update_campaign_status(
#                 campaign_id,
#                 "failed",
#                 {"error": str(e)}
#             )
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "campaign_failed",
#                 {"error": str(e)}
#             )
        
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/campaign/{campaign_id}")
# async def get_campaign(
#     campaign_id: str,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Retrieve a specific campaign by ID
#     """
#     try:
#         campaign = firebase_service.get_campaign(campaign_id)
        
#         if not campaign:
#             raise HTTPException(status_code=404, detail="Campaign not found")
        
#         # Check if user has access to this campaign (if authenticated)
#         if user_id and campaign.get('user_id') != user_id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         return campaign
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error retrieving campaign: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/campaigns")
# async def get_user_campaigns(
#     user_id: Optional[str] = Depends(verify_firebase_token),
#     limit: int = 10
# ):
#     """
#     Get all campaigns for the authenticated user
#     """
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Authentication required")
    
#     try:
#         campaigns = firebase_service.get_user_campaigns(user_id, limit)
#         return {
#             "campaigns": campaigns,
#             "count": len(campaigns)
#         }
        
#     except Exception as e:
#         print(f"Error retrieving campaigns: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/user/profile")
# async def create_user_profile(
#     user_info: UserInfo,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Create or update user profile
#     """
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Authentication required")
    
#     try:
#         firebase_service.create_user_profile(user_id, {
#             "email": user_info.email,
#             "name": user_info.name
#         })
        
#         return {
#             "status": "success",
#             "message": "User profile created/updated",
#             "user_id": user_id
#         }
        
#     except Exception as e:
#         print(f"Error creating user profile: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/campaign/{campaign_id}")
# async def delete_campaign(
#     campaign_id: str,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Delete a campaign (soft delete by updating status)
#     """
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Authentication required")
    
#     try:
#         campaign = firebase_service.get_campaign(campaign_id)
        
#         if not campaign:
#             raise HTTPException(status_code=404, detail="Campaign not found")
        
#         if campaign.get('user_id') != user_id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         firebase_service.update_campaign_status(campaign_id, "deleted")
        
#         return {
#             "status": "success",
#             "message": "Campaign deleted",
#             "campaign_id": campaign_id
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error deleting campaign: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/campaign/{campaign_id}/activities")
# async def get_campaign_activities(
#     campaign_id: str,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Get real-time activity log for a campaign
#     """
#     try:
#         # Note: This would require reading from Realtime Database
#         # Implementation depends on your frontend real-time listener setup
#         return {
#             "campaign_id": campaign_id,
#             "message": "Use Firebase Realtime Database listener in frontend for live updates",
#             "path": f"campaign_activities/{campaign_id}"
#         }
        
#     except Exception as e:
#         print(f"Error retrieving activities: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# # --- STARTUP EVENT ---
# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup"""
#     print("=" * 50)
#     print("🚀 Agentic CRM API Starting...")
#     print("=" * 50)
#     print("✅ Firebase initialized")
#     print("✅ LangGraph workflow ready")
#     print("✅ API endpoints active")
#     print("=" * 50)

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)




# import os
# import uvicorn
# from datetime import datetime
# from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from typing import Optional
# from pydantic import BaseModel, Field

# # Import models
# from app.models import CampaignRequest, CampaignResponse, UserInfo
# # Import the enhanced compiled graph
# from app.agent import build_campaign_manager_workflow
# # Import Firebase service
# from app.firebase_config import firebase_service

# # Initialize FastAPI
# app = FastAPI(
#     title="Agentic CRM API v2.0",
#     description="AI-Powered Campaign Manager with Real Image Generation - LinkedIn & Threads Only",
#     version="2.0.0"
# )

# # CORS Configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your frontend domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize the workflow
# campaign_workflow = build_campaign_manager_workflow()


# # ============= AUTHENTICATION =============
# async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
#     """Verify Firebase ID token from Authorization header"""
#     if not authorization:
#         return None
    
#     try:
#         if authorization.startswith("Bearer "):
#             token = authorization.split("Bearer ")[1]
#             user_info = firebase_service.verify_user_token(token)
#             return user_info['uid'] if user_info else None
#     except Exception as e:
#         print(f"Token verification error: {e}")
#         return None
    
#     return None


# # ============= EXTENDED REQUEST MODEL =============
# class EnhancedCampaignRequest(BaseModel):
#     """Enhanced campaign request with additional context"""
#     brand_name: str = Field(..., description="Brand name")
#     goal: str = Field(..., description="Campaign objective")
#     audience: str = Field(..., description="Target audience")
#     additional_context: Optional[str] = Field(None, description="Additional business context")
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "brand_name": "TechInnovate AI",
#                 "goal": "Launch AI analytics platform and get 1000 signups",
#                 "audience": "B2B SaaS founders, CTOs, data scientists aged 30-50",
#                 "additional_context": "Series A startup, $5M funding, focus on ROI"
#             }
#         }


# # ============= ENDPOINTS =============

# @app.get("/")
# def root():
#     """Root endpoint"""
#     return {
#         "service": "Agentic CRM API v2.0",
#         "status": "active",
#         "version": "2.0.0",
#         "platforms": ["LinkedIn", "Threads"],
#         "image_generation": "Pollinations.ai (FREE)",
#         "api_limit": "20 posts/month (Ayrshare Free)",
#         "features": [
#             "Real AI Image Generation",
#             "Strategic Campaign Planning",
#             "Smart Calendar Management",
#             "Zero-Retry Execution",
#             "Performance Analytics",
#             "Executive Reporting"
#         ],
#         "documentation": "/docs"
#     }


# @app.get("/health")
# def health_check():
#     """Health check with system status"""
#     return {
#         "status": "healthy",
#         "service": "agentic-crm-backend-v2",
#         "timestamp": datetime.now().isoformat(),
#         "firebase": "connected",
#         "ai_model": "gemini-2.0-flash-exp",
#         "image_gen": "pollinations.ai",
#         "platforms": ["LinkedIn", "Threads"]
#     }


# @app.get("/api/limits")
# def get_api_limits():
#     """Get current API usage limits"""
#     return {
#         "ayrshare_free_tier": {
#             "total_calls": 20,
#             "platforms": ["LinkedIn", "Threads"],
#             "reset": "monthly",
#             "retry_policy": "none (single attempt only)"
#         },
#         "image_generation": {
#             "provider": "Pollinations.ai",
#             "limit": "unlimited",
#             "cost": "free"
#         },
#         "recommendations": [
#             "Plan campaigns carefully - only 20 API calls/month",
#             "Use draft mode to preview before executing",
#             "Each post execution = 1 API call (no retries)",
#             "LinkedIn and Threads only on free tier"
#         ]
#     }


# @app.post("/campaign/run", response_model=CampaignResponse)
# async def run_campaign(
#     request: EnhancedCampaignRequest,
#     background_tasks: BackgroundTasks,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Execute full agentic workflow: Plan → Calendar → Execute → Track → Report
#     Now with REAL image generation and efficient API usage
#     """
#     print(f"\n{'='*70}")
#     print(f"🚀 NEW CAMPAIGN REQUEST")
#     print(f"{'='*70}")
#     print(f"Brand: {request.brand_name}")
#     print(f"Goal: {request.goal}")
#     print(f"User: {user_id or 'anonymous'}")
#     print(f"{'='*70}\n")
    
#     try:
#         # Use provided user_id or generate anonymous ID
#         effective_user_id = user_id or "anonymous"
        
#         # Create campaign in Firebase
#         campaign_id = firebase_service.create_campaign(
#             user_id=effective_user_id,
#             campaign_data={
#                 "brand_name": request.brand_name,
#                 "goal": request.goal,
#                 "audience": request.audience,
#                 "additional_context": request.additional_context
#             }
#         )
        
#         firebase_service.log_campaign_activity(
#             campaign_id,
#             "campaign_initiated",
#             {
#                 "brand": request.brand_name,
#                 "platforms": ["LinkedIn", "Threads"],
#                 "image_gen": "pollinations.ai"
#             }
#         )
        
#         # Construct initial state
#         initial_state = {
#             "brand_name": request.brand_name,
#             "goal": request.goal,
#             "audience": request.audience,
#             "additional_context": request.additional_context or "",
#             "posts": [],
#             "calendar": {},
#             "execution_results": [],
#             "performance_metrics": {},
#             "final_report": "",
#             "status": "initiated",
#             "campaign_id": campaign_id,
#             "user_id": effective_user_id,
#             "scheduled_jobs": []
#         }
        
#         # Execute workflow
#         firebase_service.update_campaign_status(campaign_id, "planning")
#         firebase_service.log_campaign_activity(campaign_id, "strategic_planning_started")
        
#         print("🤖 Starting AI Workflow...\n")
#         final_state = campaign_workflow.invoke(initial_state)
        
#         # Save results to Firebase
#         if final_state.get('posts'):
#             firebase_service.save_campaign_posts(campaign_id, final_state['posts'])
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "posts_generated",
#                 {
#                     "count": len(final_state['posts']),
#                     "platforms": list(set([p['platform'] for p in final_state['posts']]))
#                 }
#             )
        
#         if final_state.get('calendar'):
#             firebase_service.update_campaign_status(
#                 campaign_id,
#                 "calendar_ready",
#                 {"calendar": final_state['calendar']}
#             )
        
#         if final_state.get('execution_results'):
#             firebase_service.save_execution_results(campaign_id, final_state['execution_results'])
            
#             # Log API usage
#             api_calls_used = len([r for r in final_state['execution_results'] 
#                                   if r.get('status') in ['success', 'scheduled', 'error']])
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "execution_completed",
#                 {
#                     "api_calls_used": api_calls_used,
#                     "remaining_calls": f"~{20 - api_calls_used}/20",
#                     "successful": len([r for r in final_state['execution_results'] 
#                                       if r.get('status') == 'scheduled'])
#                 }
#             )
        
#         if final_state.get('final_report'):
#             firebase_service.save_campaign_report(campaign_id, final_state['final_report'])
#             firebase_service.log_campaign_activity(campaign_id, "report_generated")
        
#         # Increment user campaign count
#         if user_id:
#             firebase_service.increment_user_campaigns(effective_user_id)
        
#         print(f"\n{'='*70}")
#         print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
#         print(f"{'='*70}\n")
        
#         # Return enhanced response
#         return {
#             "status": "success",
#             "campaign_id": campaign_id,
#             "plan": final_state.get('posts', []),
#             "results": final_state.get('execution_results', []),
#             "report": final_state.get('final_report', "No report generated."),
#             "metadata": {
#                 "platforms": ["LinkedIn", "Threads"],
#                 "posts_count": len(final_state.get('posts', [])),
#                 "images_generated": len([p for p in final_state.get('posts', []) if p.get('mediaUrl')]),
#                 "api_calls_used": len([r for r in final_state.get('execution_results', []) 
#                                       if r.get('status') in ['success', 'scheduled', 'error']]),
#                 "calendar_days": len(final_state.get('calendar', {}))
#             }
#         }
        
#     except Exception as e:
#         print(f"\n❌ WORKFLOW ERROR: {str(e)}\n")
        
#         # Log error to Firebase
#         if 'campaign_id' in locals():
#             firebase_service.update_campaign_status(
#                 campaign_id,
#                 "failed",
#                 {"error": str(e)}
#             )
#             firebase_service.log_campaign_activity(
#                 campaign_id,
#                 "campaign_failed",
#                 {"error": str(e)}
#             )
        
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/campaign/preview")
# async def preview_campaign(
#     request: EnhancedCampaignRequest,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """
#     Generate campaign preview WITHOUT executing (saves API calls)
#     """
#     try:
#         print(f"👁️  Generating preview for: {request.brand_name}")
        
#         # Create temporary state for preview
#         preview_state = {
#             "brand_name": request.brand_name,
#             "goal": request.goal,
#             "audience": request.audience,
#             "additional_context": request.additional_context or "",
#             "posts": [],
#             "calendar": {},
#             "execution_results": [],
#             "performance_metrics": {},
#             "final_report": "",
#             "status": "preview",
#             "campaign_id": f"preview_{int(datetime.now().timestamp())}",
#             "user_id": user_id or "anonymous",
#             "scheduled_jobs": []
#         }
        
#         # Only run planner and calendar nodes (no execution)
#         from app.agent import strategic_planner_node, calendar_manager_node
        
#         preview_state = strategic_planner_node(preview_state)
#         preview_state = calendar_manager_node(preview_state)
        
#         return {
#             "status": "preview_ready",
#             "posts": preview_state.get('posts', []),
#             "calendar": preview_state.get('calendar', {}),
#             "metadata": {
#                 "note": "This is a PREVIEW - no API calls made",
#                 "platforms": ["LinkedIn", "Threads"],
#                 "posts_count": len(preview_state.get('posts', [])),
#                 "images_generated": len([p for p in preview_state.get('posts', []) if p.get('mediaUrl')]),
#                 "calendar_days": len(preview_state.get('calendar', {}))
#             }
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


# @app.get("/campaign/{campaign_id}")
# async def get_campaign(
#     campaign_id: str,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """Retrieve campaign by ID"""
#     try:
#         campaign = firebase_service.get_campaign(campaign_id)
        
#         if not campaign:
#             raise HTTPException(status_code=404, detail="Campaign not found")
        
#         # Check access permissions
#         if user_id and campaign.get('user_id') != user_id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         return campaign
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/campaigns")
# async def get_user_campaigns(
#     user_id: Optional[str] = Depends(verify_firebase_token),
#     limit: int = 10
# ):
#     """Get all campaigns for authenticated user"""
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Authentication required")
    
#     try:
#         campaigns = firebase_service.get_user_campaigns(user_id, limit)
#         return {
#             "campaigns": campaigns,
#             "count": len(campaigns)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.delete("/campaign/{campaign_id}")
# async def delete_campaign(
#     campaign_id: str,
#     user_id: Optional[str] = Depends(verify_firebase_token)
# ):
#     """Soft delete campaign"""
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Authentication required")
    
#     try:
#         campaign = firebase_service.get_campaign(campaign_id)
        
#         if not campaign:
#             raise HTTPException(status_code=404, detail="Campaign not found")
        
#         if campaign.get('user_id') != user_id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         firebase_service.update_campaign_status(campaign_id, "deleted")
        
#         return {
#             "status": "success",
#             "message": "Campaign deleted",
#             "campaign_id": campaign_id
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # ============= STARTUP EVENT =============
# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup"""
#     print("\n" + "="*70)
#     print("🚀 AGENTIC CRM API v2.0 - STARTING")
#     print("="*70)
#     print("✅ Firebase initialized")
#     print("✅ AI Model: gemini-2.0-flash-exp")
#     print("✅ Image Gen: Pollinations.ai (FREE)")
#     print("✅ Platforms: LinkedIn, Threads")
#     print("✅ API Limit: 20 calls/month")
#     print("✅ Workflow: Plan → Calendar → Execute → Track → Report")
#     print("="*70)
#     print("📡 Server ready at http://localhost:8000")
#     print("📚 Docs available at http://localhost:8000/docs")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)




# app/main.py - PRODUCTION READY VERSION
import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel, Field

# Import models
from app.models import CampaignRequest, CampaignResponse, UserInfo
# Import the enhanced compiled graph
from app.agent import build_campaign_manager_workflow
# Import Firebase service
from app.firebase_config import firebase_service

# Initialize FastAPI
app = FastAPI(
    title="Agentic CRM API v2.0",
    description="AI-Powered Campaign Manager - LinkedIn & Threads Only (Free Tier)",
    version="2.0.0"
)

# CORS Configuration - CRITICAL FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-production-domain.com"  # Add your production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize the workflow
campaign_workflow = build_campaign_manager_workflow()


# ============= AUTHENTICATION - FIXED =============
async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    OPTIONAL authentication - allows both authenticated and anonymous users
    """
    # Allow anonymous access for testing
    if not authorization or authorization == "null":
        return None
    
    try:
        if authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1]
            user_info = firebase_service.verify_user_token(token)
            return user_info['uid'] if user_info else None
    except Exception as e:
        print(f"⚠️ Token verification error: {e}")
        return None
    
    return None


# ============= EXTENDED REQUEST MODEL =============
class EnhancedCampaignRequest(BaseModel):
    """Enhanced campaign request"""
    brand_name: str = Field(..., description="Brand name")
    goal: str = Field(..., description="Campaign objective")
    audience: str = Field(..., description="Target audience")
    additional_context: Optional[str] = Field(None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "TechInnovate AI",
                "goal": "Launch AI platform and get 1000 signups",
                "audience": "B2B SaaS founders, CTOs, data scientists aged 30-50",
                "additional_context": "Series A startup, $5M funding"
            }
        }


# ============= ENDPOINTS =============

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Agentic CRM API v2.0",
        "status": "active",
        "version": "2.0.0",
        "platforms": ["LinkedIn", "Threads"],
        "image_generation": "Pollinations.ai (FREE - Unlimited)",
        "api_limit": "20 posts/month (Ayrshare Free Tier)",
        "authentication": "Optional (Firebase or Anonymous)",
        "features": [
            "✅ Real AI Image Generation (Pollinations.ai)",
            "✅ Strategic Campaign Planning (AI-powered)",
            "✅ Smart Calendar Management",
            "✅ Single-Attempt Execution (No retry to save quota)",
            "✅ Performance Analytics",
            "✅ Executive Reporting",
            "✅ LinkedIn & Threads Support"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "create_campaign": "POST /campaign/run",
            "preview_campaign": "POST /campaign/preview (FREE - No API calls)",
            "get_campaign": "GET /campaign/{id}",
            "list_campaigns": "GET /campaigns",
            "api_limits": "GET /api/limits"
        }
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "agentic-crm-backend-v2",
        "timestamp": datetime.now().isoformat(),
        "firebase": "connected",
        "ai_model": "gemini-2.0-flash-exp",
        "image_gen": "pollinations.ai (unlimited)",
        "platforms": ["LinkedIn", "Threads"],
        "ready": True
    }


@app.get("/api/limits")
def get_api_limits():
    """Get current API usage limits and best practices"""
    return {
        "ayrshare_free_tier": {
            "total_monthly_calls": 20,
            "supported_platforms": ["LinkedIn", "Threads"],
            "unsupported_platforms": ["Twitter", "Facebook", "Instagram", "YouTube", "TikTok"],
            "reset_period": "monthly",
            "retry_policy": "NONE - Single attempt only to preserve quota",
            "scheduling": "Supported",
            "media_support": "Images via URL"
        },
        "image_generation": {
            "provider": "Pollinations.ai",
            "limit": "unlimited",
            "cost": "free",
            "quality": "high",
            "formats": ["PNG", "JPG"],
            "dimensions": {
                "LinkedIn": "1200x627",
                "Threads": "1080x1080"
            }
        },
        "best_practices": [
            "🎯 Use /campaign/preview to review posts before executing (FREE)",
            "💰 Plan campaigns carefully - only 20 API calls per month",
            "🚫 No retry logic - each execution counts as 1 API call",
            "📅 Schedule posts in advance to maximize reach",
            "🖼️ Images auto-generated for every post (unlimited)",
            "✅ LinkedIn for B2B, Threads for engagement"
        ],
        "upgrade_options": {
            "premium_plan": "More platforms + higher limits",
            "business_plan": "All platforms + analytics",
            "link": "https://www.ayrshare.com/business-plan-for-multiple-users/"
        }
    }


@app.post("/campaign/preview")
async def preview_campaign(request: EnhancedCampaignRequest):
    """
    🎯 PREVIEW MODE - Generate campaign plan WITHOUT executing
    ✅ FREE - No API calls used
    ✅ See posts, images, and schedule before committing
    """
    try:
        print(f"\n{'='*70}")
        print(f"👁️  PREVIEW MODE - No API calls will be made")
        print(f"{'='*70}")
        print(f"Brand: {request.brand_name}")
        print(f"Goal: {request.goal}")
        print(f"{'='*70}\n")
        
        # Create preview state
        preview_state = {
            "brand_name": request.brand_name,
            "goal": request.goal,
            "audience": request.audience,
            "additional_context": request.additional_context or "",
            "posts": [],
            "calendar": {},
            "execution_results": [],
            "performance_metrics": {},
            "final_report": "",
            "status": "preview",
            "campaign_id": f"preview_{int(datetime.now().timestamp())}",
            "user_id": "preview_user",
            "scheduled_jobs": []
        }
        
        # Only run planner and calendar (no execution)
        from app.agent import strategic_planner_node, calendar_manager_node
        
        preview_state = strategic_planner_node(preview_state)
        preview_state = calendar_manager_node(preview_state)
        
        print(f"✅ Preview generated: {len(preview_state.get('posts', []))} posts")
        print(f"📅 Calendar spans {len(preview_state.get('calendar', {}))} days")
        print(f"💰 API calls used: 0 (Preview mode)\n")
        
        return {
            "status": "preview_ready",
            "posts": preview_state.get('posts', []),
            "calendar": preview_state.get('calendar', {}),
            "metadata": {
                "note": "This is a PREVIEW - no API calls made",
                "platforms": list(set([p['platform'] for p in preview_state.get('posts', [])])),
                "posts_count": len(preview_state.get('posts', [])),
                "images_generated": len([p for p in preview_state.get('posts', []) if p.get('mediaUrl')]),
                "calendar_days": len(preview_state.get('calendar', {}))
            }
        }
    
    except Exception as e:
        print(f"❌ Preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@app.post("/campaign/run", response_model=CampaignResponse)
async def run_campaign(
    request: EnhancedCampaignRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = Depends(verify_firebase_token)
):
    """
    🚀 EXECUTE CAMPAIGN - Full workflow with API calls
    ⚠️  Uses Ayrshare API quota (20 calls/month)
    💡 Use /campaign/preview first to review before executing
    """
    print(f"\n{'='*70}")
    print(f"🚀 CAMPAIGN EXECUTION STARTED")
    print(f"{'='*70}")
    print(f"Brand: {request.brand_name}")
    print(f"Goal: {request.goal}")
    print(f"User: {user_id or 'anonymous'}")
    print(f"⚠️  This will use API quota!")
    print(f"{'='*70}\n")
    
    try:
        # Use provided user_id or anonymous
        effective_user_id = user_id or "anonymous"
        
        # Create campaign in Firebase
        campaign_id = firebase_service.create_campaign(
            user_id=effective_user_id,
            campaign_data={
                "brand_name": request.brand_name,
                "goal": request.goal,
                "audience": request.audience,
                "additional_context": request.additional_context
            }
        )
        
        firebase_service.log_campaign_activity(
            campaign_id,
            "campaign_initiated",
            {
                "brand": request.brand_name,
                "platforms": ["LinkedIn", "Threads"],
                "image_gen": "pollinations.ai"
            }
        )
        
        # Construct initial state
        initial_state = {
            "brand_name": request.brand_name,
            "goal": request.goal,
            "audience": request.audience,
            "additional_context": request.additional_context or "",
            "posts": [],
            "calendar": {},
            "execution_results": [],
            "performance_metrics": {},
            "final_report": "",
            "status": "initiated",
            "campaign_id": campaign_id,
            "user_id": effective_user_id,
            "scheduled_jobs": []
        }
        
        # Execute workflow
        firebase_service.update_campaign_status(campaign_id, "planning")
        
        print("🤖 Starting AI Workflow...\n")
        final_state = campaign_workflow.invoke(initial_state)
        
        # Save results to Firebase
        if final_state.get('posts'):
            firebase_service.save_campaign_posts(campaign_id, final_state['posts'])
        
        if final_state.get('calendar'):
            firebase_service.update_campaign_status(
                campaign_id,
                "calendar_ready",
                {"calendar": final_state['calendar']}
            )
        
        if final_state.get('execution_results'):
            firebase_service.save_execution_results(campaign_id, final_state['execution_results'])
            
            # Calculate API usage
            api_calls_used = len([r for r in final_state['execution_results'] 
                                  if r.get('status') in ['success', 'scheduled', 'error']])
            
            print(f"\n💰 API USAGE SUMMARY:")
            print(f"   Calls used this campaign: {api_calls_used}")
            print(f"   Remaining quota: ~{20 - api_calls_used}/20")
            
            firebase_service.log_campaign_activity(
                campaign_id,
                "execution_completed",
                {
                    "api_calls_used": api_calls_used,
                    "remaining_quota": f"~{20 - api_calls_used}/20"
                }
            )
        
        if final_state.get('final_report'):
            firebase_service.save_campaign_report(campaign_id, final_state['final_report'])
        
        # Increment user campaign count
        if user_id:
            firebase_service.increment_user_campaigns(effective_user_id)
        
        print(f"\n{'='*70}")
        print("✅ CAMPAIGN COMPLETED SUCCESSFULLY")
        print(f"{'='*70}\n")
        
        # Return response
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "plan": final_state.get('posts', []),
            "results": final_state.get('execution_results', []),
            "report": final_state.get('final_report', "Report generation in progress..."),
            "metadata": {
                "platforms": ["LinkedIn", "Threads"],
                "posts_count": len(final_state.get('posts', [])),
                "images_generated": len([p for p in final_state.get('posts', []) if p.get('mediaUrl')]),
                "api_calls_used": len([r for r in final_state.get('execution_results', []) 
                                      if r.get('status') in ['success', 'scheduled', 'error']]),
                "calendar_days": len(final_state.get('calendar', {}))
            }
        }
        
    except Exception as e:
        print(f"\n❌ CAMPAIGN FAILED: {str(e)}\n")
        
        # Log error to Firebase
        if 'campaign_id' in locals():
            firebase_service.update_campaign_status(
                campaign_id,
                "failed",
                {"error": str(e)}
            )
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaign/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    user_id: Optional[str] = Depends(verify_firebase_token)
):
    """Retrieve campaign by ID"""
    try:
        campaign = firebase_service.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Allow anonymous access or owner access
        if user_id and campaign.get('user_id') not in [user_id, "anonymous", "preview_user"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns")
async def get_user_campaigns(
    user_id: Optional[str] = Depends(verify_firebase_token),
    limit: int = 10
):
    """Get all campaigns for user (requires auth)"""
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Please sign in to view your campaigns."
        )
    
    try:
        campaigns = firebase_service.get_user_campaigns(user_id, limit)
        return {
            "campaigns": campaigns,
            "count": len(campaigns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/campaign/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user_id: Optional[str] = Depends(verify_firebase_token)
):
    """Soft delete campaign (requires auth)"""
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        campaign = firebase_service.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        firebase_service.update_campaign_status(campaign_id, "deleted")
        
        return {
            "status": "success",
            "message": "Campaign deleted",
            "campaign_id": campaign_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= STARTUP EVENT =============
@app.on_event("startup")
async def startup_event():
    """Initialize services"""
    print("\n" + "="*70)
    print("🚀 AGENTIC CRM API v2.0 - PRODUCTION READY")
    print("="*70)
    print("✅ Firebase initialized")
    print("✅ AI Model: gemini-2.0-flash-exp")
    print("✅ Image Gen: Pollinations.ai (FREE, unlimited)")
    print("✅ Platforms: LinkedIn, Threads (Ayrshare Free Tier)")
    print("✅ API Limit: 20 calls/month")
    print("✅ Authentication: Optional (Firebase or Anonymous)")
    print("="*70)
    print("📡 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("💡 Use /campaign/preview before /campaign/run to save quota")
    print("="*70 + "\n")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )