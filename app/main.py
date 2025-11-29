# <<<<<<< HEAD
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from app.agent import app_graph
# # from app.models import CampaignRequest, CampaignResponse

# =======
# # # from fastapi import FastAPI, HTTPException
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from app.agent import app_graph
# # # from app.models import CampaignRequest, CampaignResponse

# # # app = FastAPI(
# # #     title="Agentic CRM API",
# # #     description="Backend for Campaign Planner Agent using LangGraph",
# # #     version="1.0.0"
# # # )

# # # app.add_middleware(
# # #     CORSMiddleware,
# # #     allow_origins=["*"],
# # #     allow_credentials=True,
# # #     allow_methods=["*"],
# # #     allow_headers=["*"],
# # # )

# # # @app.get("/health")
# # # def health_check():
# # #     return {"status": "active", "service": "agentic-crm-backend"}

# # # @app.post("/campaign/run", response_model=CampaignResponse)
# # # async def run_campaign(request: CampaignRequest):
# # #     """
# # #     Triggers the full Agentic Workflow: Plan -> Execute -> Report
# # #     """
# # #     try:
# # #         initial_state = {
# # #             "brand_name": request.brand_name,
# # #             "goal": request.goal,
# # #             "audience": request.audience,
# # #             "posts": [],
# # #             "execution_results": [],
# # #             "final_report": "",
# # #             "status": "started"
# # #         }
        
# # #         # Invoke LangGraph
# # #         final_state = app_graph.invoke(initial_state)
        
# # #         return {
# # #             "status": "success",
# # #             "plan": final_state.get('posts', []),
# # #             "results": final_state.get('execution_results', []),
# # #             "report": final_state.get('final_report', "No report generated")
# # #         }
        
# # #     except Exception as e:
# # #         print(f"Error: {str(e)}")
# # #         raise HTTPException(status_code=500, detail=str(e))


# # import os
# # import json
# # import time
# # from typing import TypedDict, List, Dict, Any
# # from datetime import datetime, timedelta
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel, Field
# # from langgraph.graph import StateGraph, END
# # from langchain_google_genai import ChatGoogleGenerativeAI
# # from langchain_core.messages import SystemMessage, HumanMessage
# # from dotenv import load_dotenv

# # # Load environment variables
# # load_dotenv()

# # # --- CONFIGURATION ---
# # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # if not GEMINI_API_KEY:
# #     print("WARNING: GEMINI_API_KEY not set. Using mock responses.")

# # # Initialize LLM
# # llm = None
# # if GEMINI_API_KEY:
# #     try:
# #         llm = ChatGoogleGenerativeAI(
# #             model="gemini-2.0-flash-exp",
# #             google_api_key=GEMINI_API_KEY,
# #             temperature=0.7,
# #             convert_system_message_to_human=True
# #         )
# #     except Exception as e:
# #         print(f"Error initializing Gemini: {e}")

# # # --- PYDANTIC MODELS ---
# # class CampaignRequest(BaseModel):
# #     brand_name: str = Field(..., description="Brand name for the campaign")
# #     goal: str = Field(..., description="Campaign goal/objective")
# #     audience: str = Field(..., description="Target audience description")

# # class CampaignResponse(BaseModel):
# #     status: str
# #     plan: List[Dict[str, Any]]
# #     results: List[Dict[str, Any]]
# #     report: str

# # # --- LANGGRAPH STATE ---
# # class AgentState(TypedDict):
# #     brand_name: str
# #     goal: str
# #     audience: str
# #     posts: List[Dict[str, Any]]
# #     execution_results: List[Dict[str, Any]]
# #     final_report: str
# #     status: str

# # # --- AGENT NODES ---

# # def planner_node(state: AgentState) -> Dict[str, Any]:
# #     """
# #     Node 1: Generates campaign plan with content and schedule
# #     """
# #     print(f"[PLANNER] Planning campaign for: {state['brand_name']}")
    
# #     platforms = ["LinkedIn", "YouTube", "Threads"]
    
# #     # Mock response if no LLM available
# #     if not llm:
# #         posts = [
# #             {
# #                 "platform": "LinkedIn",
# #                 "content": f"🚀 Exciting news from {state['brand_name']}! We're launching a new initiative focused on {state['goal']}. Join us in revolutionizing the industry. #Innovation #Leadership",
# #                 "image_idea": "Professional team collaboration",
# #                 "mediaUrl": "https://placehold.co/600x400/0077B5/white/png?text=LinkedIn+Post",
# #                 "scheduledDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
# #                 "scheduledTime": "09:00",
# #                 "status": "draft"
# #             },
# #             {
# #                 "platform": "YouTube",
# #                 "content": f"📹 NEW VIDEO: Behind the scenes at {state['brand_name']} - How we're achieving {state['goal']}. Subscribe for more exclusive content!",
# #                 "image_idea": "Video thumbnail with brand logo",
# #                 "mediaUrl": "https://placehold.co/600x400/FF0000/white/png?text=YouTube+Video",
# #                 "scheduledDate": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
# #                 "scheduledTime": "14:00",
# #                 "status": "draft"
# #             },
# #             {
# #                 "platform": "Threads",
# #                 "content": f"✨ Quick update: At {state['brand_name']}, we believe in {state['goal']}. Here's what we're working on today... 🧵",
# #                 "image_idea": "Colorful brand imagery",
# #                 "mediaUrl": "https://placehold.co/600x400/000000/white/png?text=Threads+Post",
# #                 "scheduledDate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
# #                 "scheduledTime": "11:00",
# #                 "status": "draft"
# #             }
# #         ]
# #         return {"posts": posts, "status": "planned"}
    
# #     # Use LLM for content generation
# #     prompt = f"""
# #     You are an expert Social Media Strategist. 
# #     Create a campaign plan for:
# #     Brand: {state['brand_name']}
# #     Goal: {state['goal']}
# #     Target Audience: {state['audience']}
    
# #     Generate exactly 3 high-impact social media posts.
# #     Platforms MUST be chosen ONLY from: {', '.join(platforms)}.
    
# #     For each post, include:
# #     - Engaging content with emojis and hashtags
# #     - Platform-specific best practices
# #     - Image description for visual content
    
# #     Return ONLY a JSON array (no markdown, no backticks):
# #     [
# #         {{"platform": "LinkedIn", "content": "Post text...", "image_idea": "Image description"}},
# #         {{"platform": "YouTube", "content": "Video description...", "image_idea": "Thumbnail idea"}},
# #         {{"platform": "Threads", "content": "Thread text...", "image_idea": "Visual concept"}}
# #     ]
# #     """
    
# #     try:
# #         response = llm.invoke([
# #             SystemMessage(content="Return strictly a JSON array. No markdown formatting."),
# #             HumanMessage(content=prompt)
# #         ])
        
# #         content = response.content.strip()
# #         # Remove markdown code blocks if present
# #         if content.startswith("```"):
# #             content = content.split("```")[1]
# #             if content.startswith("json"):
# #                 content = content[4:]
        
# #         posts = json.loads(content)
        
# #         # Add scheduling and media URLs
# #         for i, post in enumerate(posts):
# #             post['mediaUrl'] = f"https://placehold.co/600x400/png?text={post['platform'].replace(' ', '+')}"
# #             post['scheduledDate'] = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
# #             post['scheduledTime'] = f"{9 + i * 2}:00"
# #             post['status'] = "draft"
        
# #         print(f"[PLANNER] Generated {len(posts)} posts successfully")
# #         return {"posts": posts, "status": "planned"}
        
# #     except Exception as e:
# #         print(f"[PLANNER ERROR] {e}")
# #         # Fallback to mock posts
# #         return planner_node({"brand_name": state['brand_name'], "llm": None})


# # def executor_node(state: AgentState) -> Dict[str, Any]:
# #     """
# #     Node 2: Simulates post execution and generates mock analytics
# #     """
# #     print("[EXECUTOR] Starting execution...")
    
# #     results = []
    
# #     for i, post in enumerate(state['posts']):
# #         platform = post.get('platform', 'Unknown')
        
# #         # Simulate API call delay
# #         time.sleep(0.5)
        
# #         # Mock execution with realistic metrics
# #         post_id = f"post_{int(time.time())}_{i}"
        
# #         # Simulate YouTube video posts requiring actual video (fail condition)
# #         if platform == 'YouTube':
# #             status = "error"
# #             execution_result = {
# #                 "platform": platform,
# #                 "status": status,
# #                 "id": post_id,
# #                 "error": "Video content required for YouTube posts",
# #                 "executedAt": datetime.now().isoformat()
# #             }
# #         else:
# #             status = "success"
# #             # Platform-specific engagement metrics
# #             base_multiplier = {"LinkedIn": 1.5, "Threads": 1.2, "YouTube": 2.0}.get(platform, 1.0)
            
# #             execution_result = {
# #                 "platform": platform,
# #                 "status": status,
# #                 "id": post_id,
# #                 "likes": int((hash(post.get('content', '')) % 500 + 100) * base_multiplier),
# #                 "shares": int((hash(post.get('content', '')) % 100 + 20) * base_multiplier),
# #                 "comments": int((hash(post.get('content', '')) % 50 + 10) * base_multiplier),
# #                 "impressions": int((hash(post.get('content', '')) % 5000 + 1000) * base_multiplier),
# #                 "reach": int((hash(post.get('content', '')) % 3000 + 500) * base_multiplier),
# #                 "executedAt": datetime.now().isoformat()
# #             }
        
# #         results.append(execution_result)
# #         print(f"[EXECUTOR] {platform} post: {status}")
    
# #     print(f"[EXECUTOR] Completed - {len(results)} posts processed")
# #     return {"execution_results": results, "status": "executed"}


# # def reporter_node(state: AgentState) -> Dict[str, Any]:
# #     """
# #     Node 3: Generates comprehensive performance report
# #     """
# #     print("[REPORTER] Generating report...")
    
# #     # Calculate total metrics
# #     total_likes = sum(r.get('likes', 0) for r in state['execution_results'])
# #     total_shares = sum(r.get('shares', 0) for r in state['execution_results'])
# #     total_comments = sum(r.get('comments', 0) for r in state['execution_results'])
# #     total_impressions = sum(r.get('impressions', 0) for r in state['execution_results'])
    
# #     successful_posts = [r for r in state['execution_results'] if r.get('status') == 'success']
# #     failed_posts = [r for r in state['execution_results'] if r.get('status') == 'error']
    
# #     # Find best performing platform
# #     best_platform = max(successful_posts, key=lambda x: x.get('likes', 0), default={'platform': 'N/A'})
    
# #     # Mock report if no LLM
# #     if not llm:
# #         report = f"""# Campaign Performance Report - {state['brand_name']}

# # ## Executive Summary
# # Campaign Goal: {state['goal']}
# # Target Audience: {state['audience']}
# # Execution Date: {datetime.now().strftime('%Y-%m-%d')}

# # ## Overall Performance
# # - **Total Engagement**: {total_likes + total_shares + total_comments:,}
# # - **Total Impressions**: {total_impressions:,}
# # - **Successful Posts**: {len(successful_posts)}/{len(state['execution_results'])}
# # - **Engagement Rate**: {((total_likes + total_shares + total_comments) / max(total_impressions, 1) * 100):.2f}%

# # ## Platform Performance
# # Best Performing: **{best_platform.get('platform', 'N/A')}** with {best_platform.get('likes', 0):,} likes

# # ### Breakdown:
# # {chr(10).join(f"- **{r['platform']}**: {r.get('likes', 0):,} likes, {r.get('shares', 0):,} shares, {r.get('comments', 0):,} comments" for r in successful_posts)}

# # ## Key Insights
# # 1. **Strong Engagement**: The campaign achieved significant audience interaction across platforms
# # 2. **Platform Optimization**: LinkedIn and Threads performed exceptionally well
# # 3. **Content Strategy**: Visual content and authentic messaging resonated with the target audience

# # ## Recommendations
# # 1. **Increase Posting Frequency**: Successful engagement suggests audience appetite for more content
# # 2. **Invest in Video Content**: Prepare video assets for YouTube to capture that platform's potential
# # 3. **Leverage Peak Times**: Schedule posts during identified high-engagement windows
# # 4. **A/B Testing**: Experiment with different content formats and messaging approaches

# # ---
# # *Generated by Agentic CRM Reporter*
# # """
# #         return {"final_report": report, "status": "completed"}
    
# #     # Use LLM for intelligent analysis
# #     metrics_json = json.dumps(state['execution_results'], indent=2)
    
# #     prompt = f"""
# #     You are a Marketing Analytics Expert.
# #     Analyze this campaign performance for {state['brand_name']}:
    
# #     Campaign Goal: {state['goal']}
# #     Target Audience: {state['audience']}
    
# #     Performance Data:
# #     {metrics_json}
    
# #     Create a comprehensive executive report in Markdown format covering:
# #     1. Executive Summary with key metrics
# #     2. Platform-by-platform performance analysis
# #     3. Engagement rate calculations
# #     4. Success factors and challenges
# #     5. Data-driven recommendations for future campaigns
    
# #     Use professional formatting, bullet points, and clear sections.
# #     """
    
# #     try:
# #         response = llm.invoke([HumanMessage(content=prompt)])
# #         report = response.content
# #         print("[REPORTER] Report generated successfully")
# #         return {"final_report": report, "status": "completed"}
    
# #     except Exception as e:
# #         print(f"[REPORTER ERROR] {e}")
# #         # Fallback to mock report
# #         return reporter_node({"execution_results": state['execution_results'], "llm": None})


# # # --- BUILD LANGGRAPH WORKFLOW ---
# # workflow = StateGraph(AgentState)

# # workflow.add_node("planner", planner_node)
# # workflow.add_node("executor", executor_node)
# # workflow.add_node("reporter", reporter_node)

# # workflow.set_entry_point("planner")
# # workflow.add_edge("planner", "executor")
# # workflow.add_edge("executor", "reporter")
# # workflow.add_edge("reporter", END)

# # app_graph = workflow.compile()

# # # --- FASTAPI APPLICATION ---
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
# # app = FastAPI(
# #     title="Agentic CRM API",
# #     description="Backend for Campaign Planner Agent using LangGraph",
# #     version="1.0.0"
# # )

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# <<<<<<< HEAD
# # @app.get("/health")
# # def health_check():
# #     return {"status": "active", "service": "agentic-crm-backend"}
# =======
# # @app.get("/")
# # def root():
# #     return {
# #         "service": "Agentic CRM API",
# #         "status": "active",
# #         "version": "1.0.0",
# #         "endpoints": {
# #             "health": "/health",
# #             "run_campaign": "/campaign/run"
# #         }
# #     }

# # @app.get("/health")
# # def health_check():
# #     return {
# #         "status": "active",
# #         "service": "agentic-crm-backend",
# #         "timestamp": datetime.now().isoformat(),
# #         "llm_status": "connected" if llm else "mock_mode"
# #     }
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927

# # @app.post("/campaign/run", response_model=CampaignResponse)
# # async def run_campaign(request: CampaignRequest):
# #     """
# #     Triggers the full Agentic Workflow: Plan -> Execute -> Report
# #     """
# #     try:
# <<<<<<< HEAD
# =======
# #         print(f"\n=== CAMPAIGN REQUEST ===")
# #         print(f"Brand: {request.brand_name}")
# #         print(f"Goal: {request.goal}")
# #         print(f"Audience: {request.audience}")
        
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
# #         initial_state = {
# #             "brand_name": request.brand_name,
# #             "goal": request.goal,
# #             "audience": request.audience,
# #             "posts": [],
# #             "execution_results": [],
# #             "final_report": "",
# #             "status": "started"
# #         }
        
# <<<<<<< HEAD
# #         # Invoke LangGraph
# #         final_state = app_graph.invoke(initial_state)
        
# =======
# #         # Invoke LangGraph workflow
# #         final_state = app_graph.invoke(initial_state)
        
# #         print(f"=== WORKFLOW COMPLETED ===")
# #         print(f"Posts Generated: {len(final_state.get('posts', []))}")
# #         print(f"Results: {len(final_state.get('execution_results', []))}")
        
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
# #         return {
# #             "status": "success",
# #             "plan": final_state.get('posts', []),
# #             "results": final_state.get('execution_results', []),
# #             "report": final_state.get('final_report', "No report generated")
# #         }
        
# #     except Exception as e:
# <<<<<<< HEAD
# #         print(f"Error: {str(e)}")
# #         raise HTTPException(status_code=500, detail=str(e))


# =======
# #         print(f"ERROR: {str(e)}")
# #         import traceback
# #         traceback.print_exc()
# #         raise HTTPException(status_code=500, detail=str(e))


# # if __name__ == "__main__":
# #     import uvicorn
# #     port = int(os.getenv("PORT", 8000))
# #     uvicorn.run(app, host="0.0.0.0", port=port)



# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
# import os
# import uvicorn
# from datetime import datetime
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware

# <<<<<<< HEAD
# # Import models
# from app.models import CampaignRequest, CampaignResponse
# # Import the compiled graph
# =======
# # Import models to ensure consistency across the app
# from app.models import CampaignRequest, CampaignResponse
# # Import the actual compiled graph from agent.py - Single Source of Truth
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
# from app.agent import app_graph

# # --- FASTAPI SETUP ---
# app = FastAPI(
#     title="Agentic CRM API",
#     description="Backend for Campaign Planner Agent using LangGraph",
#     version="1.0.0"
# )

# # Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, replace with specific frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- ENDPOINTS ---

# @app.get("/")
# def root():
#     """Root endpoint to verify API availability."""
#     return {
#         "service": "Agentic CRM API",
#         "status": "active",
#         "version": "1.0.0",
#         "documentation": "/docs"
#     }

# @app.get("/health")
# def health_check():
#     """Health check endpoint for monitoring."""
# <<<<<<< HEAD
# =======
#     # You could add a check here to see if app_graph is ready if needed
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
#     return {
#         "status": "active",
#         "service": "agentic-crm-backend",
#         "timestamp": datetime.now().isoformat()
#     }

# @app.post("/campaign/run", response_model=CampaignResponse)
# async def run_campaign(request: CampaignRequest):
#     """
#     Triggers the full Agentic Workflow: Plan -> Execute -> Report
#     """
#     print(f"\n=== 🚀 RECEIVED CAMPAIGN REQUEST ===")
#     print(f"Brand: {request.brand_name}")
#     print(f"Goal: {request.goal}")

#     try:
#         # 1. Construct the Initial State matching AgentState in agent.py
#         initial_state = {
#             "brand_name": request.brand_name,
#             "goal": request.goal,
#             "audience": request.audience,
# <<<<<<< HEAD
#             "posts": [],              
#             "execution_results": [], 
#             "final_report": "",       
# =======
#             "posts": [],              # Empty list to start
#             "execution_results": [],  # Empty list to start
#             "final_report": "",       # Empty string to start
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
#             "status": "started"
#         }
        
#         # 2. Invoke the LangGraph Agent
# <<<<<<< HEAD
# =======
#         # This calls Planner -> Executor -> Reporter
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
#         final_state = app_graph.invoke(initial_state)
        
#         print("=== ✅ WORKFLOW COMPLETED ===")
        
# <<<<<<< HEAD
#         # 3. Return the results
# =======
#         # 3. Return the results mapped to the Pydantic Response Model
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927
#         return {
#             "status": "success",
#             "plan": final_state.get('posts', []),
#             "results": final_state.get('execution_results', []),
#             "report": final_state.get('final_report', "No report generated.")
#         }
        
#     except Exception as e:
#         print(f"❌ ERROR RUNNING CAMPAIGN: {str(e)}")
# <<<<<<< HEAD
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)
# =======
#         # In a real app, you might want to log the full traceback here
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     # Run the server
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)
# >>>>>>> adebb315bf5e8c81ba43901ec38d500be6947927

import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import models
from app.models import CampaignRequest, CampaignResponse
# Import the compiled graph
from app.agent import app_graph

# --- FASTAPI SETUP ---
app = FastAPI(
    title="Agentic CRM API",
    description="Backend for Campaign Planner Agent using LangGraph",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/")
def root():
    """Root endpoint to verify API availability."""
    return {
        "service": "Agentic CRM API",
        "status": "active",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "active",
        "service": "agentic-crm-backend",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/campaign/run", response_model=CampaignResponse)
async def run_campaign(request: CampaignRequest):
    """
    Triggers the full Agentic Workflow: Plan -> Execute -> Report
    """
    print(f"\n=== 🚀 RECEIVED CAMPAIGN REQUEST ===")
    print(f"Brand: {request.brand_name}")
    print(f"Goal: {request.goal}")

    try:
        # 1. Construct the Initial State matching AgentState in agent.py
        initial_state = {
            "brand_name": request.brand_name,
            "goal": request.goal,
            "audience": request.audience,
            "posts": [],              
            "execution_results": [], 
            "final_report": "",       
            "status": "started"
        }
        
        # 2. Invoke the LangGraph Agent
        final_state = app_graph.invoke(initial_state)
        
        print("=== ✅ WORKFLOW COMPLETED ===")
        
        # 3. Return the results
        return {
            "status": "success",
            "plan": final_state.get('posts', []),
            "results": final_state.get('execution_results', []),
            "report": final_state.get('final_report', "No report generated.")
        }
        
    except Exception as e:
        print(f"❌ ERROR RUNNING CAMPAIGN: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)