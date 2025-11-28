import os
import json
import time
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI # <-- CORRECTED IMPORT
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables (critical for local development)
load_dotenv()

# --- CONFIGURATION ---
# Load secrets from environment (set in .env, Dockerfile, or CI/CD)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

if not GEMINI_API_KEY:
    print("FATAL: GEMINI_API_KEY not found. Agent will fail.")

# Initialize the LLM client with the corrected class name and fix for SystemMessages
llm = ChatGoogleGenerativeAI( # <-- CORRECTED CLASS NAME
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    # FIX: This parameter resolves the SystemMessage error.
    convert_system_message_to_human=True 
)

# --- STATE DEFINITION (LangGraph) ---
class AgentState(TypedDict):
    """
    Represents the state passed between nodes in the LangGraph workflow.
    """
    brand_name: str
    goal: str
    audience: str
    posts: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    final_report: str
    status: str

# --- NODES ---

def planner_node(state: AgentState):
    """
    Node 1: Generates the campaign plan (content and schedule) using Gemini.
    """
    print(f"[AGENT: PLANNER] Starting Planning for: {state['brand_name']}")
    
    platforms = ["LinkedIn", "YouTube", "Threads"]

    prompt = f"""
    You are an expert Social Media Strategist. 
    Create a campaign plan for:
    Brand: {state['brand_name']}
    Goal: {state['goal']}
    Target Audience: {state['audience']}
    
    Generate exactly 3 high-impact social media posts.
    The platforms MUST be chosen ONLY from: {', '.join(platforms)}.
    
    Return strict JSON format (DO NOT include markdown fences, e.g., ```json):
    [
        {{"platform": "LinkedIn", "content": "Post text/script...", "image_idea": "Image description for placeholder"}},
        ...
    ]
    """
    
    response = llm.invoke([
        SystemMessage(content="Return strictly a JSON array of objects. Do not use any introductory text or markdown formatting."), 
        HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    
    try:
        posts = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding failed: {e}. Falling back to empty plan.")
        posts = []
    
    for post in posts:
        image_idea = post.get('image_idea', 'Campaign Asset')
        post['mediaUrl'] = f"[https://placehold.co/600x400/png?text=](https://placehold.co/600x400/png?text=){image_idea.replace(' ', '%20')}"
    
    print(f"[PLANNER] Plan generated with {len(posts)} posts.")
    return {"posts": posts, "status": "planned"}

def executor_node(state: AgentState):
    """
    Node 2: Executes the posts via Ayrshare (or simulation) and simulates follow-up analytics.
    """
    print("[AGENT: EXECUTOR] Starting Execution and Follow-up...")
    results = []
    platform_map = {'LinkedIn': 'linkedin', 'YouTube': 'youtube', 'Threads': 'threads'}

    for post in state['posts']:
        platform = post.get('platform', 'Unknown')
        api_platform = platform_map.get(platform)
        
        # --- EXECUTION MOCK ---
        time.sleep(1) 
        post_id = f"mock_id_{hash(post.get('content',''))}"
        status = "success"
        
        if platform == 'YouTube' and post.get('mediaUrl'):
             status = "error" 
             print(f"[MOCK] YouTube post failed (simulated image/video requirement error).")

        # --- FOLLOW-UP MOCK (Analytics Retrieval) ---
        results.append({
            "platform": platform,
            "status": status,
            "id": post_id,
            "likes": int(time.time() * 1000 % 500) + 50,
            "shares": int(time.time() * 1000 % 100) + 10,
            "comments": int(time.time() * 1000 % 50) + 5
        })
        
    print(f"[EXECUTOR] Finished execution. {len(results)} posts processed.")
    return {"execution_results": results, "status": "executed"}

def reporter_node(state: AgentState):
    """
    Node 3: Analyzes execution results and generates a final report using Gemini.
    """
    print("[AGENT: REPORTER] Starting Reporting...")
    
    metrics_summary = json.dumps(state['execution_results'], indent=2)

    prompt = f"""
    You are a Marketing Analyst Agent.
    Analyze the following campaign performance metrics for brand {state['brand_name']}:
    
    Metrics: {metrics_summary}

    Write a concise executive summary in Markdown format (no introductory text).
    The report MUST cover:
    1. Total Engagement achieved.
    2. Best and worst performing platforms.
    3. Recommendations for the next campaign.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    print("[REPORTER] Report generated.")
    return {"final_report": response.content, "status": "completed"}

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reporter", reporter_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reporter")
workflow.add_edge("reporter", END)

app_graph = workflow.compile()