from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.agent import app_graph
from app.models import CampaignRequest, CampaignResponse

app = FastAPI(
    title="Agentic CRM API",
    description="Backend for Campaign Planner Agent using LangGraph",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "active", "service": "agentic-crm-backend"}

@app.post("/campaign/run", response_model=CampaignResponse)
async def run_campaign(request: CampaignRequest):
    """
    Triggers the full Agentic Workflow: Plan -> Execute -> Report
    """
    try:
        initial_state = {
            "brand_name": request.brand_name,
            "goal": request.goal,
            "audience": request.audience,
            "posts": [],
            "execution_results": [],
            "final_report": "",
            "status": "started"
        }
        
        # Invoke LangGraph
        final_state = app_graph.invoke(initial_state)
        
        return {
            "status": "success",
            "plan": final_state.get('posts', []),
            "results": final_state.get('execution_results', []),
            "report": final_state.get('final_report', "No report generated")
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))