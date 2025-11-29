import os
import json
import time
import requests
from typing import TypedDict, List, Dict, Any
from datetime import datetime, timedelta
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
    raise ValueError("GEMINI_API_KEY is required")

if not AYRSHARE_API_KEY:
    print("INFO: AYRSHARE_API_KEY not set. Using mock execution mode.")

# Initialize LLM with YOUR actual model from AI Studio
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # ✅ YOUR MODEL from AI Studio
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True 
)

print("✅ LLM initialized with model: gemini-2.5-flash")

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    brand_name: str
    goal: str
    audience: str
    posts: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    final_report: str
    status: str

# --- AGENT NODES ---

def planner_node(state: AgentState):
    """
    Node 1: Generates campaign plan with content and schedule.
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
- platform: One of {platforms}
- content: Engaging post text with emojis and hashtags
- image_idea: Visual concept description

Return ONLY a JSON array (no markdown, no explanations):
[
    {{"platform": "LinkedIn", "content": "Post text...", "image_idea": "Image description"}},
    {{"platform": "YouTube", "content": "Video description...", "image_idea": "Thumbnail concept"}},
    {{"platform": "Threads", "content": "Thread text...", "image_idea": "Visual idea"}}
]
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content="Return only a JSON array. No markdown, no code blocks, no explanations."), 
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:] if len(lines) > 1 else lines
            # Remove last line (```) if present
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Remove "json" prefix if present
        if content.startswith("json"):
            content = content[4:].strip()
        
        # Parse JSON
        posts = json.loads(content)
        
        if not isinstance(posts, list):
            raise ValueError("Response must be a JSON array")
        
        # Enhance posts with metadata
        for i, post in enumerate(posts):
            image_idea = post.get('image_idea', 'Campaign Asset')
            safe_text = image_idea.replace(' ', '+')[:30]
            post['mediaUrl'] = f"https://placehold.co/600x400/png?text={safe_text}"
            
            # Add scheduling (spread over 3 days)
            schedule_date = datetime.now() + timedelta(days=i+1)
            post['scheduledDate'] = schedule_date.strftime("%Y-%m-%d")
            post['scheduledTime'] = f"{9 + (i*2)}:00"
            post['status'] = "draft"
        
        print(f"[PLANNER] ✅ Generated {len(posts)} posts successfully")
        return {"posts": posts, "status": "planned"}
    
    except json.JSONDecodeError as e:
        print(f"[PLANNER] ❌ JSON decode error: {e}")
        print(f"[PLANNER] Raw content: {content[:300]}")
        
        # Fallback: Return basic mock posts
        fallback_posts = [
            {
                "platform": "LinkedIn",
                "content": f"🚀 Exciting news from {state['brand_name']}! We're focused on {state['goal']}. #Innovation #Leadership",
                "image_idea": "Professional team collaboration",
                "mediaUrl": "https://placehold.co/600x400/0077B5/white/png?text=LinkedIn",
                "scheduledDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "scheduledTime": "09:00",
                "status": "draft"
            },
            {
                "platform": "YouTube", 
                "content": f"📹 Behind the scenes at {state['brand_name']} - {state['goal']}. Subscribe!",
                "image_idea": "Video thumbnail",
                "mediaUrl": "https://placehold.co/600x400/FF0000/white/png?text=YouTube",
                "scheduledDate": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "scheduledTime": "14:00",
                "status": "draft"
            },
            {
                "platform": "Threads",
                "content": f"✨ At {state['brand_name']}, we're working on {state['goal']}. Thread 🧵",
                "image_idea": "Colorful visual",
                "mediaUrl": "https://placehold.co/600x400/000000/white/png?text=Threads",
                "scheduledDate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "scheduledTime": "11:00",
                "status": "draft"
            }
        ]
        
        print("[PLANNER] ⚠️ Using fallback posts")
        return {"posts": fallback_posts, "status": "planned"}
    
    except Exception as e:
        print(f"[PLANNER] ❌ Unexpected error: {e}")
        raise


def executor_node(state: AgentState):
    """
    Node 2: Executes posts (real API or mock simulation).
    """
    print("[AGENT: EXECUTOR] Starting Execution...")
    results = []
    
    platform_map = {
        'LinkedIn': 'linkedin', 
        'YouTube': 'youtube', 
        'Threads': 'threads'
    }

    for i, post in enumerate(state['posts']):
        platform_name = post.get('platform', 'Unknown')
        
        if platform_name not in platform_map:
            print(f"   [SKIP] Platform {platform_name} not supported")
            continue

        api_platform = platform_map[platform_name]
        print(f"   -> Processing {platform_name}...")
        
        # YouTube requires video content (simulate failure)
        if platform_name == 'YouTube' and not post.get('videoUrl'):
            print(f"      [ERROR] YouTube requires video")
            results.append({
                "platform": platform_name,
                "status": "error",
                "error": "Video content required for YouTube",
                "id": f"error_{int(time.time())}_{i}"
            })
            continue

        # Real API or Mock Mode
        if AYRSHARE_API_KEY:
            # REAL AYRSHARE API CALL
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

                response = requests.post(
                    'https://app.ayrshare.com/api/post',
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                data = response.json()

                if response.status_code == 200 and data.get('status') == 'success':
                    print(f"      [SUCCESS] ✅ Posted! ID: {data.get('id')}")
                    results.append({
                        "platform": platform_name,
                        "status": "success",
                        "id": data.get('id'),
                        "refId": data.get('refId'),
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "impressions": 0,
                        "reach": 0,
                        "executedAt": datetime.now().isoformat()
                    })
                else:
                    print(f"      [FAIL] ❌ API Error: {data}")
                    results.append({
                        "platform": platform_name,
                        "status": "error",
                        "error": str(data),
                        "id": None
                    })

            except Exception as e:
                print(f"      [EXCEPTION] ❌ {e}")
                results.append({
                    "platform": platform_name,
                    "status": "error",
                    "error": str(e),
                    "id": None
                })
        else:
            # MOCK EXECUTION MODE
            print(f"      [MOCK] ✅ Simulated post")
            time.sleep(0.3)  # Simulate API delay
            
            # Generate realistic mock metrics
            multipliers = {"LinkedIn": 1.5, "Threads": 1.2, "YouTube": 2.0}
            base_mult = multipliers.get(platform_name, 1.0)
            content_hash = abs(hash(post.get('content', '')))
            
            results.append({
                "platform": platform_name,
                "status": "success",
                "id": f"mock_{int(time.time())}_{i}",
                "likes": int((content_hash % 500 + 100) * base_mult),
                "shares": int((content_hash % 100 + 20) * base_mult),
                "comments": int((content_hash % 50 + 10) * base_mult),
                "impressions": int((content_hash % 5000 + 1000) * base_mult),
                "reach": int((content_hash % 3000 + 500) * base_mult),
                "executedAt": datetime.now().isoformat()
            })
    
    print(f"[EXECUTOR] ✅ Completed - {len(results)} posts processed")
    return {"execution_results": results, "status": "executed"}


def reporter_node(state: AgentState):
    """
    Node 3: Generates performance report using AI analysis.
    """
    print("[AGENT: REPORTER] Starting Reporting...")
    
    # Calculate metrics
    successful = [r for r in state['execution_results'] if r.get('status') == 'success']
    failed = [r for r in state['execution_results'] if r.get('status') == 'error']
    
    total_engagement = sum(
        r.get('likes', 0) + r.get('shares', 0) + r.get('comments', 0) 
        for r in successful
    )
    total_impressions = sum(r.get('impressions', 0) for r in successful)
    
    metrics_json = json.dumps(state['execution_results'], indent=2)

    prompt = f"""
You are a Marketing Analytics Expert.
Analyze this campaign for {state['brand_name']}:

Campaign Goal: {state['goal']}
Target Audience: {state['audience']}

Performance Data:
{metrics_json}

Summary:
- Successful: {len(successful)}/{len(state['execution_results'])} posts
- Total Engagement: {total_engagement:,}
- Total Impressions: {total_impressions:,}
- Engagement Rate: {(total_engagement/max(total_impressions,1)*100):.2f}%

Create a concise executive report in Markdown format with:
1. Executive Summary
2. Platform Performance Analysis  
3. Key Success Factors
4. Recommendations for Next Campaign

Be specific and data-driven.
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        report = response.content
        print("[REPORTER] ✅ Report generated successfully")
        return {"final_report": report, "status": "completed"}
    
    except Exception as e:
        print(f"[REPORTER] ❌ Error generating report: {e}")
        
        # Fallback report
        fallback_report = f"""# Campaign Performance Report - {state['brand_name']}

## Executive Summary
Campaign Goal: {state['goal']}
Target Audience: {state['audience']}

## Overall Performance
- **Successful Posts**: {len(successful)}/{len(state['execution_results'])}
- **Total Engagement**: {total_engagement:,}
- **Total Impressions**: {total_impressions:,}
- **Engagement Rate**: {(total_engagement/max(total_impressions,1)*100):.2f}%

## Platform Breakdown
{chr(10).join(f"- **{r['platform']}**: {r.get('likes', 0):,} likes, {r.get('shares', 0):,} shares, {r.get('comments', 0):,} comments" for r in successful)}

## Recommendations
1. Continue focusing on platforms showing strong engagement
2. Optimize content for peak audience activity times
3. Experiment with different content formats and messaging
4. Consider increasing posting frequency on top-performing platforms

---
*Generated by Agentic CRM Reporter*
"""
        return {"final_report": fallback_report, "status": "completed"}


# --- BUILD LANGGRAPH WORKFLOW ---
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
