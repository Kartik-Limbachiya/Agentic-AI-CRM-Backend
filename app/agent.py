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
    print("WARNING: AYRSHARE_API_KEY not found. Using mock execution mode.")

# --- CRITICAL FIX: Use YOUR actual available model ---
# From AI Studio, you have access to: gemini-2.5-flash
# Format: "gemini-2.5-flash" (WITHOUT the "models/" prefix for langchain)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # ✅ CORRECT: Your actual available model
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True 
)

print(f"✅ LLM initialized with model: gemini-2.5-flash")

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
    - content: The post text or script (engaging, with emojis and hashtags).
    - image_idea: A short description of a visual to go with the post.
    
    Return ONLY a JSON array (no markdown, no code blocks):
    [
        {{"platform": "LinkedIn", "content": "Post text...", "image_idea": "Image description"}},
        {{"platform": "YouTube", "content": "Video description...", "image_idea": "Thumbnail idea"}},
        {{"platform": "Threads", "content": "Thread text...", "image_idea": "Visual concept"}}
    ]
    """
    
    try:
        response = llm.invoke([
            SystemMessage(content="Return strictly a JSON array. Do not use Markdown formatting or code blocks."), 
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        
        # --- ENHANCED MARKDOWN STRIPPING ---
        # Remove markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Additional cleanup: remove "json" prefix if present
        if content.startswith("json"):
            content = content[4:].strip()
        
        posts = json.loads(content)
        
        if not isinstance(posts, list):
            raise ValueError("Response is not a JSON array")
        
        # Add media URLs and scheduling info
        from datetime import datetime, timedelta
        for i, post in enumerate(posts):
            image_idea = post.get('image_idea', 'Campaign Asset')
            # Use placehold.co for placeholder images
            safe_text = image_idea.replace(' ', '+')[:30]
            post['mediaUrl'] = f"https://placehold.co/600x400/png?text={safe_text}"
            
            # Add scheduling (1 day apart starting tomorrow)
            schedule_date = datetime.now() + timedelta(days=i+1)
            post['scheduledDate'] = schedule_date.strftime("%Y-%m-%d")
            post['scheduledTime'] = f"{9 + i*2}:00"
            post['status'] = "draft"
        
        print(f"[PLANNER] ✅ Plan generated with {len(posts)} posts.")
        return {"posts": posts, "status": "planned"}
    
    except json.JSONDecodeError as e:
        print(f"[PLANNER] ❌ JSON decoding failed: {e}")
        print(f"[PLANNER] Raw content was: {content[:500]}")
        # Return mock posts as fallback
        return {
            "posts": [
                {
                    "platform": "LinkedIn",
                    "content": f"🚀 Exciting update from {state['brand_name']}! {state['goal']} #Innovation",
                    "image_idea": "Professional business graphic",
                    "mediaUrl": "https://placehold.co/600x400/0077B5/white/png?text=LinkedIn",
                    "scheduledDate": "2024-01-16",
                    "scheduledTime": "09:00",
                    "status": "draft"
                }
            ],
            "status": "planned"
        }
    except Exception as e:
        print(f"[PLANNER] ❌ Error: {e}")
        raise

def executor_node(state: AgentState):
    """
    Node 2: Executes posts via Ayrshare (or mock mode if no API key).
    """
    print("[AGENT: EXECUTOR] Starting Execution...")
    results = []
    
    # Map friendly names to Ayrshare platform codes
    platform_map = {
        'LinkedIn': 'linkedin', 
        'YouTube': 'youtube', 
        'Threads': 'threads'
    }

    for i, post in enumerate(state['posts']):
        platform_name = post.get('platform', 'Unknown')
        
        # Skip unsupported platforms
        if platform_name not in platform_map:
            print(f"   [Skip] Platform {platform_name} not supported/allowed.")
            continue

        api_platform = platform_map.get(platform_name)
        print(f"   -> Processing {platform_name}...")
        
        # 1. YouTube Safety Check
        # Purposely fail if no videoUrl is present
        if platform_name == 'YouTube' and not post.get('videoUrl'):
            print(f"      [Error] YouTube requires video content (mock failure)")
            results.append({
                "platform": platform_name,
                "status": "error",
                "error": "Video content required for YouTube",
                "id": f"mock_error_{i}"
            })
            continue

        # 2. Real or Mock Execution
        if AYRSHARE_API_KEY:
            # REAL API CALL
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

                response = requests.post('https://app.ayrshare.com/api/post', 
                                       json=payload, 
                                       headers=headers,
                                       timeout=10)
                data = response.json()

                if response.status_code == 200 and data.get('status') == 'success':
                    print(f"      [Success] ✅ Posted! ID: {data.get('id')}")
                    results.append({
                        "platform": platform_name,
                        "status": "success",
                        "id": data.get('id'),
                        "refId": data.get('refId'),
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "impressions": 0,
                        "reach": 0
                    })
                else:
                    print(f"      [Fail] ❌ API Error: {data}")
                    results.append({
                        "platform": platform_name,
                        "status": "error",
                        "error": str(data),
                        "id": None
                    })

            except Exception as e:
                print(f"      [Exception] ❌ {e}")
                results.append({
                    "platform": platform_name,
                    "status": "error",
                    "error": str(e),
                    "id": None
                })
        else:
            # MOCK EXECUTION (no Ayrshare key)
            print(f"      [Mock] ✅ Simulated post")
            time.sleep(0.5)  # Simulate API delay
            
            # Generate realistic mock metrics
            base_multiplier = {"LinkedIn": 1.5, "Threads": 1.2, "YouTube": 2.0}.get(platform_name, 1.0)
            content_hash = hash(post.get('content', ''))
            
            results.append({
                "platform": platform_name,
                "status": "success",
                "id": f"mock_{int(time.time())}_{i}",
                "likes": int((abs(content_hash) % 500 + 100) * base_multiplier),
                "shares": int((abs(content_hash) % 100 + 20) * base_multiplier),
                "comments": int((abs(content_hash) % 50 + 10) * base_multiplier),
                "impressions": int((abs(content_hash) % 5000 + 1000) * base_multiplier),
                "reach": int((abs(content_hash) % 3000 + 500) * base_multiplier)
            })
        
    print(f"[EXECUTOR] ✅ Finished. {len(results)} posts processed.")
    return {"execution_results": results, "status": "executed"}

def reporter_node(state: AgentState):
    """
    Node 3: Generates a final report based on execution results.
    """
    print("[AGENT: REPORTER] Starting Reporting...")
    
    # Calculate summary metrics
    successful = [r for r in state['execution_results'] if r.get('status') == 'success']
    failed = [r for r in state['execution_results'] if r.get('status') == 'error']
    
    total_likes = sum(r.get('likes', 0) for r in successful)
    total_shares = sum(r.get('shares', 0) for r in successful)
    total_comments = sum(r.get('comments', 0) for r in successful)
    total_impressions = sum(r.get('impressions', 0) for r in successful)
    
    metrics_summary = json.dumps(state['execution_results'], indent=2)

    prompt = f"""
    You are a Marketing Analyst Agent.
    Analyze the following campaign performance for {state['brand_name']}:
    
    Campaign Goal: {state['goal']}
    Target Audience: {state['audience']}
    
    Performance Metrics:
    {metrics_summary}
    
    Summary Stats:
    - Successful Posts: {len(successful)}
    - Failed Posts: {len(failed)}
    - Total Engagement: {total_likes + total_shares + total_comments}
    - Total Impressions: {total_impressions}

    Write a concise executive summary in Markdown format.
    Include:
    1. Overall Performance Assessment
    2. Platform-by-platform breakdown
    3. Key Success Factors
    4. Recommendations for next campaign
    
    Keep it professional and data-driven.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        print("[REPORTER] ✅ Report generated.")
        return {"final_report": response.content, "status": "completed"}
    except Exception as e:
        print(f"[REPORTER] ❌ Error: {e}")
        # Fallback report
        report = f"""# Campaign Report - {state['brand_name']}

## Performance Summary
- **Successful Posts**: {len(successful)}/{len(state['execution_results'])}
- **Total Engagement**: {total_likes + total_shares + total_comments:,}
- **Total Impressions**: {total_impressions:,}

## Platform Breakdown
{chr(10).join(f"- **{r['platform']}**: {r.get('likes', 0)} likes, {r.get('shares', 0)} shares" for r in successful)}

## Recommendation
Continue optimizing content for platforms showing strong engagement.
"""
        return {"final_report": report, "status": "completed"}

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

print("✅ LangGraph workflow compiled successfully")
