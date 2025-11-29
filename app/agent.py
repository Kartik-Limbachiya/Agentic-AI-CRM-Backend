import os
import json
import time
import requests
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

if not GEMINI_API_KEY:
    print("FATAL: GEMINI_API_KEY not found. Agent will fail.")

if not AYRSHARE_API_KEY:
    print("WARNING: AYRSHARE_API_KEY not found. Real posting will fail.")

# Initialize the LLM client
# Using gemini-1.5-flash as it is the current stable, fast model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True 
)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
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
    Node 1: Generates the campaign plan (content and schedule).
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
    
    For each post, provide:
    - platform: One of the allowed platforms.
    - content: The post text or script.
    - image_idea: A short description of a visual to go with the post.
    
    Return strict JSON format:
    [
        {{"platform": "LinkedIn", "content": "Post text...", "image_idea": "Image description"}}
    ]
    """
    
    response = llm.invoke([
        SystemMessage(content="Return strictly a JSON array. Do not use Markdown formatting."), 
        HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    
    # --- MARKDOWN STRIPPING LOGIC ---
    # Fixes the issue where Gemini wraps JSON in ```json ... ```
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.strip().startswith("json"):
            content = content.strip()[4:]
    
    try:
        posts = json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding failed: {e}. Content was: {content}")
        posts = []
    
    # Add media URLs using a placeholder service so the frontend has something to show
    for post in posts:
        image_idea = post.get('image_idea', 'Campaign Asset')
        # Simple placeholder image generator
        post['mediaUrl'] = f"[https://placehold.co/600x400/png?text=](https://placehold.co/600x400/png?text=){image_idea.replace(' ', '%20')[:20]}"
    
    print(f"[PLANNER] Plan generated with {len(posts)} posts.")
    return {"posts": posts, "status": "planned"}

def executor_node(state: AgentState):
    """
    Node 2: Executes posts via Ayrshare.
    """
    print("[AGENT: EXECUTOR] Starting Execution...")
    results = []
    
    # Map friendly names to Ayrshare platform codes
    # NOTE: 'Threads' maps to 'threads' (requires Meta Threads connection)
    # We intentionally exclude others to enforce your "Only these 3" rule.
    platform_map = {
        'LinkedIn': 'linkedin', 
        'YouTube': 'youtube', 
        'Threads': 'threads'
    }

    for post in state['posts']:
        platform_name = post.get('platform', 'Unknown')
        
        # Skip unsupported platforms
        if platform_name not in platform_map:
            print(f"   [Skip] Platform {platform_name} not supported/allowed.")
            continue

        api_platform = platform_map.get(platform_name)
        print(f"   -> Posting to {platform_name}...")
        
        # 1. YouTube Safety Check
        # Fails purposely if no videoUrl is present (since we only generated image URLs)
        if platform_name == 'YouTube' and not post.get('videoUrl'):
             print(f"      [Error] YouTube post skipped (Video required).")
             results.append({
                "platform": platform_name,
                "status": "error",
                "error": "Video content required for YouTube",
                "id": None
             })
             continue

        # 2. Real API Call to Ayrshare
        try:
            payload = {
                "post": post.get('content'),
                "platforms": [api_platform],
                "mediaUrls": [post.get('mediaUrl')] if post.get('mediaUrl') else []
            }
            
            headers = {
                'Authorization': f'Bearer {AYRSHARE_API_KEY}',
                'Content-Type': 'application/json'
            }

            response = requests.post('[https://app.ayrshare.com/api/post](https://app.ayrshare.com/api/post)', json=payload, headers=headers)
            data = response.json()

            if response.status_code == 200 and data.get('status') == 'success':
                print(f"      [Success] Posted! ID: {data.get('id')}")
                results.append({
                    "platform": platform_name,
                    "status": "success",
                    "id": data.get('id'),
                    "refId": data.get('refId'),
                    "likes": 0,
                    "shares": 0,
                    "comments": 0
                })
            else:
                print(f"      [Fail] API Error: {data}")
                results.append({
                    "platform": platform_name,
                    "status": "error",
                    "error": str(data),
                    "id": None
                })

        except Exception as e:
            print(f"      [Exception] {e}")
            results.append({
                "platform": platform_name,
                "status": "error",
                "error": str(e),
                "id": None
            })
        
    print(f"[EXECUTOR] Finished. {len(results)} posts processed.")
    return {"execution_results": results, "status": "executed"}

def reporter_node(state: AgentState):
    """
    Node 3: Generates a final report based on execution results.
    """
    print("[AGENT: REPORTER] Starting Reporting...")
    metrics_summary = json.dumps(state['execution_results'], indent=2)

    prompt = f"""
    You are a Marketing Analyst Agent.
    Analyze the following campaign performance metrics for brand {state['brand_name']}:
    
    Metrics: {metrics_summary}

    Write a concise executive summary in Markdown.
    Cover:
    1. Successful posts vs Failed posts.
    2. Platform performance (Highlight Threads if successful).
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