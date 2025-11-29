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