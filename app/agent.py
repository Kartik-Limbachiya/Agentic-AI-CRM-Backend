# import os
# import json
# import time
# import requests
# from typing import TypedDict, List, Dict, Any
# from datetime import datetime, timedelta
# from langgraph.graph import StateGraph, END
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import SystemMessage, HumanMessage
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # --- CONFIGURATION ---
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

# if not GEMINI_API_KEY:
#     print("FATAL: GEMINI_API_KEY not found. Agent will fail.")
#     raise ValueError("GEMINI_API_KEY is required")

# if not AYRSHARE_API_KEY:
#     print("INFO: AYRSHARE_API_KEY not set. Using mock execution mode.")

# # Initialize LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=GEMINI_API_KEY,
#     temperature=0.7,
#     convert_system_message_to_human=True 
# )

# print("✅ LLM initialized with model: gemini-2.0-flash-exp")

# # --- STATE DEFINITION ---
# class AgentState(TypedDict):
#     brand_name: str
#     goal: str
#     audience: str
#     posts: List[Dict[str, Any]]
#     execution_results: List[Dict[str, Any]]
#     final_report: str
#     status: str
#     campaign_id: str  # For Firebase tracking
#     user_id: str  # For user-specific campaigns

# # --- IMAGE GENERATION HELPER ---
# def generate_image_prompt(post_content: str, platform: str, brand_name: str) -> str:
#     """Generate image using AI image generation API or placeholder"""
#     try:
#         # Extract key themes from content for image generation
#         image_prompt = f"Professional social media image for {platform}: {brand_name} - {post_content[:100]}"
        
#         # Using Unsplash as a free alternative for POC
#         # In production, use DALL-E, Midjourney API, or Stable Diffusion
#         keywords = extract_keywords(post_content)
#         unsplash_url = f"https://source.unsplash.com/800x600/?{keywords},{platform.lower()}"
        
#         return unsplash_url
#     except Exception as e:
#         print(f"Image generation error: {e}")
#         # Fallback to themed placeholder
#         return f"https://placehold.co/800x600/{get_platform_color(platform)}/white?text={brand_name}"

# def extract_keywords(text: str) -> str:
#     """Extract keywords for image search"""
#     # Simple keyword extraction (in production, use NLP)
#     words = text.lower().split()
#     keywords = [w for w in words if len(w) > 4 and w.isalpha()][:3]
#     return ",".join(keywords) if keywords else "business,professional"

# def get_platform_color(platform: str) -> str:
#     """Get brand color for platform"""
#     colors = {
#         "LinkedIn": "0077B5",
#         "YouTube": "FF0000",
#         "Threads": "000000",
#         "Instagram": "E4405F",
#         "Twitter": "1DA1F2",
#         "Facebook": "4267B2"
#     }
#     return colors.get(platform, "333333")

# # --- AGENT NODES ---

# def planner_node(state: AgentState):
#     """
#     Node 1: Generates campaign plan with content, schedule, and images.
#     """
#     print(f"[AGENT: PLANNER] Starting Planning for: {state['brand_name']}")
    
#     platforms = ["LinkedIn", "YouTube", "Threads", "Instagram", "Twitter"]

#     prompt = f"""
# You are an expert Social Media Strategist and Content Creator.

# Create a comprehensive campaign plan for:
# Brand: {state['brand_name']}
# Goal: {state['goal']}
# Target Audience: {state['audience']}

# Generate exactly 5 high-impact social media posts across different platforms.
# Choose the BEST platforms from: {', '.join(platforms)}

# For each post, provide:
# - platform: One of the platforms listed above
# - content: Engaging, platform-appropriate post text with emojis and hashtags (150-280 characters)
# - image_idea: Detailed visual concept description (be specific: colors, objects, mood, composition)
# - posting_strategy: Best time to post and why

# IMPORTANT: 
# - Make content authentic and engaging
# - Use platform-specific best practices
# - Include clear CTAs (Call-to-Actions)
# - Optimize for each platform's audience

# Return ONLY a JSON array (no markdown, no explanations):
# [
#     {{
#         "platform": "LinkedIn",
#         "content": "Professional post text with 🚀 emojis #hashtags",
#         "image_idea": "Detailed description: Professional team collaboration in modern office, bright natural lighting, diverse team, laptop screens showing analytics",
#         "posting_strategy": "Tuesday 10 AM - peak professional engagement time"
#     }},
#     ...
# ]
# """
    
#     try:
#         response = llm.invoke([
#             SystemMessage(content="Return only a JSON array. No markdown, no code blocks, no explanations."), 
#             HumanMessage(content=prompt)
#         ])
        
#         content = response.content.strip()
        
#         # Clean up response
#         if content.startswith("```"):
#             lines = content.split("\n")
#             lines = lines[1:] if len(lines) > 1 else lines
#             if lines and lines[-1].strip() == "```":
#                 lines = lines[:-1]
#             content = "\n".join(lines).strip()
        
#         if content.startswith("json"):
#             content = content[4:].strip()
        
#         posts = json.loads(content)
        
#         if not isinstance(posts, list):
#             raise ValueError("Response must be a JSON array")
        
#         # Enhance posts with metadata and images
#         for i, post in enumerate(posts):
#             # Generate or use provided image
#             if 'image_url' in post and post['image_url']:
#                 post['mediaUrl'] = post['image_url']
#             else:
#                 # Generate image based on content
#                 post['mediaUrl'] = generate_image_prompt(
#                     post.get('content', ''),
#                     post.get('platform', 'LinkedIn'),
#                     state['brand_name']
#                 )
            
#             # Add scheduling (spread over 5 days, optimal times)
#             schedule_date = datetime.now() + timedelta(days=i+1)
#             post['scheduledDate'] = schedule_date.strftime("%Y-%m-%d")
            
#             # Platform-specific optimal times
#             optimal_times = {
#                 "LinkedIn": "10:00",
#                 "Instagram": "11:00",
#                 "Twitter": "12:00",
#                 "Facebook": "13:00",
#                 "YouTube": "14:00",
#                 "Threads": "15:00"
#             }
#             post['scheduledTime'] = optimal_times.get(post['platform'], "09:00")
#             post['status'] = "draft"
            
#             # Add engagement predictions
#             post['predicted_engagement'] = {
#                 "likes": f"{200 + (i * 50)}-{400 + (i * 100)}",
#                 "shares": f"{20 + (i * 10)}-{50 + (i * 20)}",
#                 "comments": f"{10 + (i * 5)}-{30 + (i * 10)}"
#             }
        
#         print(f"[PLANNER] ✅ Generated {len(posts)} posts successfully")
#         return {"posts": posts, "status": "planned"}
    
#     except json.JSONDecodeError as e:
#         print(f"[PLANNER] ❌ JSON decode error: {e}")
#         print(f"[PLANNER] Raw content: {content[:300]}")
        
#         # Enhanced fallback posts
#         fallback_posts = []
#         platforms_used = ["LinkedIn", "Instagram", "Twitter", "YouTube", "Facebook"]
        
#         for i, platform in enumerate(platforms_used):
#             schedule_date = datetime.now() + timedelta(days=i+1)
#             fallback_posts.append({
#                 "platform": platform,
#                 "content": f"🚀 Exciting update from {state['brand_name']}! We're working towards {state['goal']}. Join us on this journey! #Innovation #Growth #{platform}",
#                 "image_idea": f"Professional {platform} branded image with {state['brand_name']} logo",
#                 "mediaUrl": generate_image_prompt(state['goal'], platform, state['brand_name']),
#                 "scheduledDate": schedule_date.strftime("%Y-%m-%d"),
#                 "scheduledTime": ["10:00", "11:00", "12:00", "14:00", "15:00"][i],
#                 "status": "draft",
#                 "posting_strategy": f"Optimal engagement time for {platform}",
#                 "predicted_engagement": {
#                     "likes": f"{200 + (i * 50)}-{400 + (i * 100)}",
#                     "shares": f"{20 + (i * 10)}-{50 + (i * 20)}",
#                     "comments": f"{10 + (i * 5)}-{30 + (i * 10)}"
#                 }
#             })
        
#         print("[PLANNER] ⚠️ Using enhanced fallback posts")
#         return {"posts": fallback_posts, "status": "planned"}
    
#     except Exception as e:
#         print(f"[PLANNER] ❌ Unexpected error: {e}")
#         raise


# def executor_node(state: AgentState):
#     """
#     Node 2: Executes posts (real API or mock simulation).
#     """
#     print("[AGENT: EXECUTOR] Starting Execution...")
#     results = []
    
#     platform_map = {
#         'LinkedIn': 'linkedin',
#         'YouTube': 'youtube',
#         'Threads': 'threads'
#     }

#     for i, post in enumerate(state['posts']):
#         platform_name = post.get('platform', 'Unknown')
        
#         if platform_name not in platform_map:
#             print(f"   [SKIP] Platform {platform_name} not supported")
#             continue

#         api_platform = platform_map[platform_name]
#         print(f"   -> Processing {platform_name}...")
        
#         # YouTube requires video content (simulate)
#         if platform_name == 'YouTube' and not post.get('videoUrl'):
#             print(f"      [INFO] YouTube post noted - requires video content")
#             results.append({
#                 "platform": platform_name,
#                 "status": "scheduled",
#                 "message": "Video content required - scheduled for production",
#                 "id": f"youtube_{int(time.time())}_{i}",
#                 "scheduled_date": post.get('scheduledDate'),
#                 "scheduled_time": post.get('scheduledTime')
#             })
#             continue

#         # Real API or Mock Mode
#         if AYRSHARE_API_KEY:
#             # REAL AYRSHARE API CALL
#             try:
#                 payload = {
#                     "post": post.get('content'),
#                     "platforms": [api_platform],
#                     "mediaUrls": [post.get('mediaUrl')] if post.get('mediaUrl') else [],
#                     "scheduleDate": f"{post.get('scheduledDate')} {post.get('scheduledTime')}"
#                 }
                
#                 headers = {
#                     'Authorization': f'Bearer {AYRSHARE_API_KEY}',
#                     'Content-Type': 'application/json'
#                 }

#                 response = requests.post(
#                     'https://app.ayrshare.com/api/post',
#                     json=payload,
#                     headers=headers,
#                     timeout=15
#                 )
#                 data = response.json()

#                 if response.status_code == 200 and data.get('status') == 'success':
#                     print(f"      [SUCCESS] ✅ Scheduled! ID: {data.get('id')}")
#                     results.append({
#                         "platform": platform_name,
#                         "status": "scheduled",
#                         "id": data.get('id'),
#                         "refId": data.get('refId'),
#                         "scheduled_date": post.get('scheduledDate'),
#                         "scheduled_time": post.get('scheduledTime'),
#                         "executedAt": datetime.now().isoformat()
#                     })
#                 else:
#                     print(f"      [FAIL] ❌ API Error: {data}")
#                     results.append({
#                         "platform": platform_name,
#                         "status": "error",
#                         "error": str(data),
#                         "id": None
#                     })

#             except Exception as e:
#                 print(f"      [EXCEPTION] ❌ {e}")
#                 results.append({
#                     "platform": platform_name,
#                     "status": "error",
#                     "error": str(e),
#                     "id": None
#                 })
#         else:
#             # MOCK EXECUTION MODE with realistic metrics
#             print(f"      [MOCK] ✅ Simulated post")
#             time.sleep(0.5)
            
#             # Generate realistic mock metrics based on platform
#             multipliers = {
#                 "LinkedIn": 1.5,
#                 "Instagram": 2.5,
#                 "Twitter": 1.8,
#                 "Facebook": 2.0,
#                 "YouTube": 3.0,
#                 "Threads": 1.3
#             }
#             base_mult = multipliers.get(platform_name, 1.0)
            
#             # Use content hash for consistent but varied results
#             content_hash = abs(hash(post.get('content', '')))
            
#             results.append({
#                 "platform": platform_name,
#                 "status": "success",
#                 "id": f"mock_{int(time.time())}_{i}",
#                 "likes": int((content_hash % 500 + 200) * base_mult),
#                 "shares": int((content_hash % 100 + 30) * base_mult),
#                 "comments": int((content_hash % 50 + 15) * base_mult),
#                 "impressions": int((content_hash % 5000 + 2000) * base_mult),
#                 "reach": int((content_hash % 3000 + 1000) * base_mult),
#                 "engagement_rate": round((content_hash % 10 + 3) / 100, 4),
#                 "executedAt": datetime.now().isoformat(),
#                 "scheduled_date": post.get('scheduledDate'),
#                 "scheduled_time": post.get('scheduledTime')
#             })
    
#     print(f"[EXECUTOR] ✅ Completed - {len(results)} posts processed")
#     return {"execution_results": results, "status": "executed"}


# def reporter_node(state: AgentState):
#     """
#     Node 3: Generates comprehensive performance report with AI analysis.
#     """
#     print("[AGENT: REPORTER] Starting Reporting...")
    
#     # Calculate comprehensive metrics
#     successful = [r for r in state['execution_results'] if r.get('status') == 'success']
#     failed = [r for r in state['execution_results'] if r.get('status') == 'error']
#     scheduled = [r for r in state['execution_results'] if r.get('status') == 'scheduled']
    
#     total_engagement = sum(
#         r.get('likes', 0) + r.get('shares', 0) + r.get('comments', 0) 
#         for r in successful
#     )
#     total_impressions = sum(r.get('impressions', 0) for r in successful)
#     total_reach = sum(r.get('reach', 0) for r in successful)
    
#     avg_engagement_rate = sum(r.get('engagement_rate', 0) for r in successful) / max(len(successful), 1)
    
#     # Platform breakdown
#     platform_performance = {}
#     for result in successful:
#         platform = result.get('platform')
#         if platform not in platform_performance:
#             platform_performance[platform] = {
#                 'likes': 0,
#                 'shares': 0,
#                 'comments': 0,
#                 'impressions': 0,
#                 'reach': 0
#             }
#         platform_performance[platform]['likes'] += result.get('likes', 0)
#         platform_performance[platform]['shares'] += result.get('shares', 0)
#         platform_performance[platform]['comments'] += result.get('comments', 0)
#         platform_performance[platform]['impressions'] += result.get('impressions', 0)
#         platform_performance[platform]['reach'] += result.get('reach', 0)
    
#     metrics_json = json.dumps({
#         'successful_posts': len(successful),
#         'failed_posts': len(failed),
#         'scheduled_posts': len(scheduled),
#         'total_posts': len(state['execution_results']),
#         'total_engagement': total_engagement,
#         'total_impressions': total_impressions,
#         'total_reach': total_reach,
#         'avg_engagement_rate': avg_engagement_rate,
#         'platform_performance': platform_performance
#     }, indent=2)

#     prompt = f"""
# You are a Senior Marketing Analytics Expert with 10+ years of experience.

# Analyze this social media campaign for {state['brand_name']}:

# **Campaign Objectives:**
# - Goal: {state['goal']}
# - Target Audience: {state['audience']}

# **Performance Metrics:**
# {metrics_json}

# **Campaign Content Summary:**
# {json.dumps([{
#     'platform': p.get('platform'),
#     'content_preview': p.get('content', '')[:100],
#     'scheduled': p.get('scheduledDate')
# } for p in state['posts']], indent=2)}

# Create a comprehensive executive report in professional Markdown format with:

# ## 1. Executive Summary
# - High-level overview of campaign performance
# - Key achievements and milestones
# - Overall ROI assessment

# ## 2. Performance Metrics Deep Dive
# - Detailed breakdown of engagement metrics
# - Platform-by-platform analysis
# - Comparison against industry benchmarks

# ## 3. Audience Insights
# - How well we reached the target audience
# - Engagement patterns and behaviors
# - Demographic insights (if available)

# ## 4. Content Performance Analysis
# - Which posts performed best and why
# - Content themes that resonated
# - Optimal posting times discovered

# ## 5. Strategic Recommendations
# - Specific, actionable next steps
# - Budget allocation suggestions
# - Content strategy improvements
# - Platform optimization opportunities

# ## 6. Risk Assessment & Mitigation
# - Any underperforming areas
# - Potential challenges
# - Mitigation strategies

# Be data-driven, specific, and provide actionable insights. Use professional business language.
# """
    
#     try:
#         response = llm.invoke([HumanMessage(content=prompt)])
#         report = response.content
        
#         # Add metadata to report
#         full_report = f"""# Social Media Campaign Report
# **Campaign:** {state['brand_name']} - {state['goal']}
# **Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
# **Campaign Period:** {min([p.get('scheduledDate', 'N/A') for p in state['posts']])} to {max([p.get('scheduledDate', 'N/A') for p in state['posts']])}

# ---

# {report}

# ---

# ## Appendix: Raw Data

# ### Overall Metrics
# - **Total Posts:** {len(state['execution_results'])}
# - **Successfully Executed:** {len(successful)}
# - **Scheduled:** {len(scheduled)}
# - **Failed:** {len(failed)}
# - **Total Engagement:** {total_engagement:,}
# - **Total Impressions:** {total_impressions:,}
# - **Total Reach:** {total_reach:,}
# - **Average Engagement Rate:** {avg_engagement_rate:.2%}

# ### Platform Breakdown
# {chr(10).join(f"**{platform}:**" + chr(10) + chr(10).join(f"- {k.title()}: {v:,}" for k, v in metrics.items()) for platform, metrics in platform_performance.items())}

# ---
# *Report generated by Agentic CRM - AI-Powered Campaign Manager*
# """
        
#         print("[REPORTER] ✅ Comprehensive report generated successfully")
#         return {"final_report": full_report, "status": "completed"}
    
#     except Exception as e:
#         print(f"[REPORTER] ❌ Error generating report: {e}")
        
#         # Enhanced fallback report
#         fallback_report = f"""# Campaign Performance Report - {state['brand_name']}

# ## Executive Summary
# Campaign Goal: {state['goal']}
# Target Audience: {state['audience']}
# Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

# ## Overall Performance
# - **Total Posts:** {len(state['execution_results'])}
# - **Successfully Executed:** {len(successful)}
# - **Scheduled for Later:** {len(scheduled)}
# - **Failed Posts:** {len(failed)}
# - **Total Engagement:** {total_engagement:,} interactions
# - **Total Impressions:** {total_impressions:,} views
# - **Total Reach:** {total_reach:,} unique users
# - **Engagement Rate:** {avg_engagement_rate:.2%}

# ## Platform Performance
# {chr(10).join(f"### {platform}" + chr(10) + chr(10).join(f"- **{k.title()}:** {v:,}" for k, v in metrics.items()) + chr(10) for platform, metrics in platform_performance.items())}

# ## Key Insights
# 1. **Highest Engagement:** {max(successful, key=lambda x: x.get('likes', 0))['platform'] if successful else 'N/A'}
# 2. **Best Reach:** {max(successful, key=lambda x: x.get('reach', 0))['platform'] if successful else 'N/A'}
# 3. **Campaign Velocity:** {len(successful)}/{len(state['posts'])} posts executed

# ## Recommendations
# 1. Continue focusing on high-performing platforms
# 2. Optimize posting times based on engagement patterns
# 3. Experiment with different content formats
# 4. Consider increasing budget for top-performing channels
# 5. A/B test messaging for improved engagement

# ## Next Steps
# 1. Monitor scheduled posts performance
# 2. Gather audience feedback
# 3. Prepare follow-up campaign based on insights
# 4. Refine targeting parameters

# ---
# *Generated by Agentic CRM Reporter*
# """
#         return {"final_report": fallback_report, "status": "completed"}


# # --- BUILD LANGGRAPH WORKFLOW ---
# workflow = StateGraph(AgentState)

# workflow.add_node("planner", planner_node)
# workflow.add_node("executor", executor_node)
# workflow.add_node("reporter", reporter_node)

# workflow.set_entry_point("planner")
# workflow.add_edge("planner", "executor")
# workflow.add_edge("executor", "reporter")
# workflow.add_edge("reporter", END)

# app_graph = workflow.compile()

# print("✅ LangGraph workflow compiled successfully with enhanced features")






# import os
# import json
# import time
# import requests
# from typing import TypedDict, List, Dict, Any
# from datetime import datetime, timedelta
# from langgraph.graph import StateGraph, END
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import SystemMessage, HumanMessage
# from dotenv import load_dotenv
# import schedule
# from concurrent.futures import ThreadPoolExecutor

# # Load environment variables
# load_dotenv()

# # Configuration
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY is required")

# # Initialize LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash-exp",
#     google_api_key=GEMINI_API_KEY,
#     temperature=0.7,
#     convert_system_message_to_human=True 
# )

# # State Definition
# class AgentState(TypedDict):
#     brand_name: str
#     goal: str
#     audience: str
#     additional_context: str  # New: additional business context
#     posts: List[Dict[str, Any]]
#     calendar: Dict[str, List[Dict[str, Any]]]  # Date -> Posts mapping
#     execution_results: List[Dict[str, Any]]
#     performance_metrics: Dict[str, Any]
#     final_report: str
#     status: str
#     campaign_id: str
#     user_id: str
#     scheduled_jobs: List[str]  # Track scheduled tasks


# # ============= ENHANCED IMAGE GENERATION =============
# def generate_image_prompt(post_content: str, platform: str, brand_name: str) -> str:
#     """Enhanced image generation with AI-powered prompts"""
#     try:
#         # Use AI to generate better image descriptions
#         image_prompt = f"""Create a professional image description for a {platform} post:
#         Brand: {brand_name}
#         Content: {post_content[:200]}
        
#         Generate a detailed visual concept with:
#         - Main subject/focus
#         - Color scheme
#         - Mood/atmosphere
#         - Composition style
        
#         Return only the image description, no explanations."""
        
#         response = llm.invoke([HumanMessage(content=image_prompt)])
#         description = response.content.strip()
        
#         # Use Unsplash for free high-quality images
#         keywords = extract_keywords(description)
#         return f"https://source.unsplash.com/1200x628/?{keywords},{platform.lower()}"
#     except Exception as e:
#         print(f"Image generation error: {e}")
#         return f"https://placehold.co/1200x628/0066CC/white?text={brand_name}"


# def extract_keywords(text: str) -> str:
#     """Extract meaningful keywords for image search"""
#     common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
#     words = [w.lower() for w in text.split() if len(w) > 3 and w.lower() not in common_words]
#     return ",".join(words[:5])


# # ============= AGENT NODE 1: STRATEGIC PLANNER =============
# def strategic_planner_node(state: AgentState):
#     """
#     Enhanced planner with multi-platform strategy
#     """
#     print(f"\n🎯 [STRATEGIC PLANNER] Analyzing: {state['brand_name']}")
    
#     platforms = {
#         "LinkedIn": {"best_time": "10:00", "optimal_days": ["Tuesday", "Wednesday", "Thursday"]},
#         "Instagram": {"best_time": "11:00", "optimal_days": ["Monday", "Wednesday", "Friday"]},
#         "Twitter": {"best_time": "12:00", "optimal_days": ["Tuesday", "Thursday", "Friday"]},
#         "Facebook": {"best_time": "13:00", "optimal_days": ["Monday", "Wednesday", "Friday"]},
#         "YouTube": {"best_time": "14:00", "optimal_days": ["Wednesday", "Saturday"]},
#         "Threads": {"best_time": "15:00", "optimal_days": ["Monday", "Tuesday", "Thursday"]},
#         "TikTok": {"best_time": "18:00", "optimal_days": ["Friday", "Saturday", "Sunday"]},
#     }

#     prompt = f"""You are a Senior Social Media Strategist with expertise in multi-platform campaigns.

# **Campaign Brief:**
# - Brand: {state['brand_name']}
# - Goal: {state['goal']}
# - Target Audience: {state['audience']}
# - Context: {state.get('additional_context', 'N/A')}

# **Task:** Create a comprehensive 7-post campaign across different platforms.

# **Requirements:**
# 1. Select the BEST 7 platforms from: {', '.join(platforms.keys())}
# 2. Each post must be platform-optimized with:
#    - Engaging content (150-280 characters)
#    - Platform-specific hashtags (3-5 relevant)
#    - Emojis for engagement
#    - Clear CTA (Call-to-Action)
# 3. Include visual concept for each post
# 4. Strategic posting times

# **Output Format (JSON only, no markdown):**
# [
#     {{
#         "platform": "Platform Name",
#         "content": "Engaging post text with emojis 🚀 and #hashtags",
#         "image_concept": "Detailed visual description: subject, colors, mood, composition",
#         "optimal_time": "HH:MM",
#         "optimal_day": "Day of week",
#         "content_type": "educational/promotional/engaging/storytelling",
#         "target_kpi": "engagement/reach/conversions"
#     }}
# ]

# Return ONLY the JSON array, no explanations."""

#     try:
#         response = llm.invoke([
#             SystemMessage(content="Return only valid JSON array. No markdown, no code blocks."),
#             HumanMessage(content=prompt)
#         ])
        
#         content = response.content.strip()
        
#         # Clean response
#         if content.startswith("```"):
#             lines = content.split("\n")[1:-1]
#             content = "\n".join(lines).strip()
#         if content.startswith("json"):
#             content = content[4:].strip()
        
#         posts = json.loads(content)
        
#         # Enhance posts with metadata and images
#         start_date = datetime.now()
#         for i, post in enumerate(posts):
#             # Find next optimal day for this platform
#             days_ahead = 0
#             while start_date + timedelta(days=days_ahead) < datetime.now() or \
#                   (start_date + timedelta(days=days_ahead)).strftime("%A") not in post.get('optimal_day', ''):
#                 days_ahead += 1
#                 if days_ahead > 14:  # Safety limit
#                     break
            
#             scheduled_date = start_date + timedelta(days=days_ahead if days_ahead <= 14 else i+1)
            
#             post.update({
#                 'post_id': f"post_{int(time.time())}_{i}",
#                 'mediaUrl': generate_image_prompt(post['content'], post['platform'], state['brand_name']),
#                 'scheduledDate': scheduled_date.strftime("%Y-%m-%d"),
#                 'scheduledTime': post.get('optimal_time', f"{9+i}:00"),
#                 'status': 'draft',
#                 'created_at': datetime.now().isoformat(),
#                 'predicted_metrics': {
#                     "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
#                     "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
#                     "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
#                 }
#             })
        
#         print(f"✅ Generated {len(posts)} strategic posts")
#         return {"posts": posts, "status": "planned"}
    
#     except json.JSONDecodeError as e:
#         print(f"⚠️ JSON Error: {e}")
#         # Fallback with enhanced posts
#         fallback_posts = create_fallback_posts(state, platforms, 7)
#         return {"posts": fallback_posts, "status": "planned"}
    
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         fallback_posts = create_fallback_posts(state, platforms, 7)
#         return {"posts": fallback_posts, "status": "planned"}


# def create_fallback_posts(state: AgentState, platforms: Dict, count: int) -> List[Dict]:
#     """Create enhanced fallback posts"""
#     posts = []
#     platform_list = list(platforms.keys())[:count]
    
#     for i, platform in enumerate(platform_list):
#         scheduled_date = datetime.now() + timedelta(days=i+1)
#         posts.append({
#             "post_id": f"post_{int(time.time())}_{i}",
#             "platform": platform,
#             "content": f"🚀 {state['brand_name']} is {state['goal']}! Join us on this exciting journey. #Innovation #{platform} #GrowthMindset",
#             "image_concept": f"Professional {platform} branded visual",
#             "mediaUrl": generate_image_prompt(state['goal'], platform, state['brand_name']),
#             "scheduledDate": scheduled_date.strftime("%Y-%m-%d"),
#             "scheduledTime": platforms[platform]["best_time"],
#             "status": "draft",
#             "content_type": "promotional",
#             "target_kpi": "engagement",
#             "created_at": datetime.now().isoformat(),
#             "predicted_metrics": {
#                 "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
#                 "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
#                 "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
#             }
#         })
    
#     return posts


# # ============= AGENT NODE 2: CALENDAR MANAGER =============
# def calendar_manager_node(state: AgentState):
#     """
#     Create and organize campaign calendar
#     """
#     print("\n📅 [CALENDAR MANAGER] Building campaign calendar...")
    
#     calendar = {}
#     scheduled_jobs = []
    
#     # Organize posts by date
#     for post in state['posts']:
#         date = post['scheduledDate']
#         if date not in calendar:
#             calendar[date] = []
#         calendar[date].append({
#             'post_id': post['post_id'],
#             'platform': post['platform'],
#             'time': post['scheduledTime'],
#             'content_preview': post['content'][:50] + '...',
#             'status': post['status']
#         })
    
#     # Sort calendar entries
#     for date in calendar:
#         calendar[date].sort(key=lambda x: x['time'])
    
#     # Create summary
#     total_days = len(calendar)
#     total_posts = len(state['posts'])
#     platforms_used = list(set([p['platform'] for p in state['posts']]))
    
#     print(f"✅ Calendar created: {total_posts} posts across {total_days} days")
#     print(f"   Platforms: {', '.join(platforms_used)}")
    
#     return {
#         "calendar": calendar,
#         "scheduled_jobs": scheduled_jobs,
#         "status": "calendar_ready"
#     }


# # ============= AGENT NODE 3: SMART EXECUTOR =============
# def smart_executor_node(state: AgentState):
#     """
#     Enhanced executor with retry logic and error handling
#     """
#     print("\n🚀 [SMART EXECUTOR] Initializing execution...")
    
#     results = []
#     platform_map = {
#         'LinkedIn': 'linkedin',
#         'Instagram': 'instagram',
#         'Facebook': 'facebook',
#         'Twitter': 'twitter',
#         'YouTube': 'youtube',
#         'Threads': 'threads',
#         'TikTok': 'tiktok'
#     }
    
#     def execute_post(post, index):
#         """Execute individual post with retry logic"""
#         platform_name = post.get('platform', 'Unknown')
        
#         if platform_name not in platform_map:
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": platform_name,
#                 "status": "skipped",
#                 "message": f"Platform {platform_name} not supported",
#                 "timestamp": datetime.now().isoformat()
#             }
        
#         api_platform = platform_map[platform_name]
#         print(f"   📤 Executing {platform_name} post...")
        
#         # YouTube requires video - handle separately
#         if platform_name == 'YouTube' and not post.get('videoUrl'):
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": platform_name,
#                 "status": "pending_video",
#                 "message": "Video content required - flagged for production",
#                 "scheduled_date": post.get('scheduledDate'),
#                 "scheduled_time": post.get('scheduledTime'),
#                 "timestamp": datetime.now().isoformat()
#             }
        
#         # Real API execution or mock mode
#         if AYRSHARE_API_KEY:
#             return execute_via_api(post, api_platform)
#         else:
#             return execute_mock(post, platform_name, index)
    
#     # Execute posts in parallel
#     with ThreadPoolExecutor(max_workers=3) as executor:
#         futures = [executor.submit(execute_post, post, i) for i, post in enumerate(state['posts'])]
#         results = [future.result() for future in futures]
    
#     success_count = len([r for r in results if r['status'] in ['success', 'scheduled']])
#     print(f"✅ Execution completed: {success_count}/{len(results)} successful")
    
#     return {
#         "execution_results": results,
#         "status": "executed"
#     }


# def execute_via_api(post: Dict, api_platform: str) -> Dict:
#     """Execute post via Ayrshare API"""
#     try:
#         payload = {
#             "post": post.get('content'),
#             "platforms": [api_platform],
#             "mediaUrls": [post.get('mediaUrl')] if post.get('mediaUrl') else [],
#             "scheduleDate": f"{post.get('scheduledDate')} {post.get('scheduledTime')}"
#         }
        
#         headers = {
#             'Authorization': f'Bearer {AYRSHARE_API_KEY}',
#             'Content-Type': 'application/json'
#         }
        
#         response = requests.post(
#             'https://app.ayrshare.com/api/post',
#             json=payload,
#             headers=headers,
#             timeout=15
#         )
        
#         data = response.json()
        
#         if response.status_code == 200 and data.get('status') == 'success':
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": post['platform'],
#                 "status": "scheduled",
#                 "api_id": data.get('id'),
#                 "refId": data.get('refId'),
#                 "scheduled_date": post.get('scheduledDate'),
#                 "scheduled_time": post.get('scheduledTime'),
#                 "timestamp": datetime.now().isoformat()
#             }
#         else:
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": post['platform'],
#                 "status": "error",
#                 "error": str(data),
#                 "timestamp": datetime.now().isoformat()
#             }
    
#     except Exception as e:
#         return {
#             "post_id": post.get('post_id'),
#             "platform": post['platform'],
#             "status": "error",
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         }


# def execute_mock(post: Dict, platform_name: str, index: int) -> Dict:
#     """Mock execution with realistic metrics"""
#     time.sleep(0.5)  # Simulate API call
    
#     # Platform-specific multipliers for realistic metrics
#     multipliers = {
#         "LinkedIn": 1.5,
#         "Instagram": 2.5,
#         "Twitter": 1.8,
#         "Facebook": 2.0,
#         "YouTube": 3.0,
#         "Threads": 1.3,
#         "TikTok": 4.0
#     }
    
#     base_mult = multipliers.get(platform_name, 1.0)
#     content_hash = abs(hash(post.get('content', '')))
    
#     return {
#         "post_id": post.get('post_id'),
#         "platform": platform_name,
#         "status": "success",
#         "mock_id": f"mock_{int(time.time())}_{index}",
#         "metrics": {
#             "likes": int((content_hash % 500 + 200) * base_mult),
#             "shares": int((content_hash % 100 + 30) * base_mult),
#             "comments": int((content_hash % 50 + 15) * base_mult),
#             "impressions": int((content_hash % 5000 + 2000) * base_mult),
#             "reach": int((content_hash % 3000 + 1000) * base_mult),
#             "engagement_rate": round((content_hash % 10 + 3) / 100, 4),
#             "clicks": int((content_hash % 200 + 50) * base_mult)
#         },
#         "executedAt": datetime.now().isoformat(),
#         "scheduled_date": post.get('scheduledDate'),
#         "scheduled_time": post.get('scheduledTime')
#     }


# # ============= AGENT NODE 4: PERFORMANCE TRACKER =============
# def performance_tracker_node(state: AgentState):
#     """
#     Track and analyze campaign performance
#     """
#     print("\n📊 [PERFORMANCE TRACKER] Analyzing campaign metrics...")
    
#     successful = [r for r in state['execution_results'] if r.get('status') == 'success']
    
#     # Aggregate metrics
#     total_metrics = {
#         'total_posts': len(state['execution_results']),
#         'successful_posts': len(successful),
#         'total_likes': sum(r.get('metrics', {}).get('likes', 0) for r in successful),
#         'total_shares': sum(r.get('metrics', {}).get('shares', 0) for r in successful),
#         'total_comments': sum(r.get('metrics', {}).get('comments', 0) for r in successful),
#         'total_impressions': sum(r.get('metrics', {}).get('impressions', 0) for r in successful),
#         'total_reach': sum(r.get('metrics', {}).get('reach', 0) for r in successful),
#         'total_clicks': sum(r.get('metrics', {}).get('clicks', 0) for r in successful),
#     }
    
#     # Calculate averages
#     if len(successful) > 0:
#         total_metrics['avg_engagement_rate'] = sum(
#             r.get('metrics', {}).get('engagement_rate', 0) for r in successful
#         ) / len(successful)
#         total_metrics['avg_likes_per_post'] = total_metrics['total_likes'] / len(successful)
    
#     # Platform breakdown
#     platform_performance = {}
#     for result in successful:
#         platform = result.get('platform')
#         metrics = result.get('metrics', {})
        
#         if platform not in platform_performance:
#             platform_performance[platform] = {
#                 'posts': 0,
#                 'likes': 0,
#                 'shares': 0,
#                 'comments': 0,
#                 'impressions': 0,
#                 'reach': 0,
#                 'engagement_rate': 0
#             }
        
#         platform_performance[platform]['posts'] += 1
#         for key in ['likes', 'shares', 'comments', 'impressions', 'reach']:
#             platform_performance[platform][key] += metrics.get(key, 0)
#         platform_performance[platform]['engagement_rate'] += metrics.get('engagement_rate', 0)
    
#     # Calculate platform averages
#     for platform, metrics in platform_performance.items():
#         posts_count = metrics['posts']
#         if posts_count > 0:
#             metrics['engagement_rate'] = metrics['engagement_rate'] / posts_count
    
#     total_metrics['platform_breakdown'] = platform_performance
    
#     print(f"✅ Performance tracked: {total_metrics['total_impressions']:,} total impressions")
    
#     return {
#         "performance_metrics": total_metrics,
#         "status": "tracked"
#     }


# # ============= AGENT NODE 5: INTELLIGENT REPORTER =============
# def intelligent_reporter_node(state: AgentState):
#     """
#     Generate comprehensive AI-powered report
#     """
#     print("\n📝 [INTELLIGENT REPORTER] Generating executive report...")
    
#     metrics = state['performance_metrics']
    
#     prompt = f"""You are a Senior Marketing Analytics Director. Create an executive-level campaign performance report.

# **Campaign Overview:**
# - Brand: {state['brand_name']}
# - Objective: {state['goal']}
# - Target Audience: {state['audience']}
# - Campaign Duration: {len(state['calendar'])} days
# - Total Posts: {metrics['total_posts']}

# **Performance Data:**
# {json.dumps(metrics, indent=2)}

# **Required Report Structure:**

# # Executive Summary
# Provide 3-4 sentences highlighting key achievements, ROI indicators, and overall campaign success.

# # Key Performance Indicators
# - Total Reach: {metrics.get('total_reach', 0):,}
# - Total Impressions: {metrics.get('total_impressions', 0):,}
# - Total Engagement: {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,}
# - Average Engagement Rate: {metrics.get('avg_engagement_rate', 0):.2%}
# - Total Clicks: {metrics.get('total_clicks', 0):,}

# # Platform Performance Analysis
# Analyze each platform's performance with:
# - Standout performers and why
# - Underperformers and potential reasons
# - Platform-specific insights

# # Audience Engagement Insights
# - What content types resonated most
# - Engagement patterns observed
# - Audience behavior insights

# # Strategic Recommendations
# Provide 5-7 specific, actionable recommendations for:
# 1. Content optimization
# 2. Platform strategy
# 3. Posting schedule
# 4. Budget allocation
# 5. Future campaign improvements

# # ROI Assessment
# - Campaign effectiveness score (1-10)
# - Cost-per-engagement estimate
# - Projected business impact

# **Important:** Write in professional business language. Be specific with numbers. Provide actionable insights."""

#     try:
#         response = llm.invoke([HumanMessage(content=prompt)])
#         report_content = response.content
        
#         # Add metadata header
#         full_report = f"""# {state['brand_name']} - Social Media Campaign Report
# **Campaign Goal:** {state['goal']}
# **Target Audience:** {state['audience']}
# **Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
# **Campaign Period:** {min([p.get('scheduledDate', '') for p in state['posts']])} to {max([p.get('scheduledDate', '') for p in state['posts']])}

# ---

# {report_content}

# ---

# ## Appendix: Detailed Metrics

# ### Overall Campaign Metrics
# - **Total Posts Scheduled:** {metrics['total_posts']}
# - **Successfully Executed:** {metrics['successful_posts']}
# - **Total Reach:** {metrics.get('total_reach', 0):,} users
# - **Total Impressions:** {metrics.get('total_impressions', 0):,} views
# - **Total Engagement:** {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,} interactions
# - **Total Clicks:** {metrics.get('total_clicks', 0):,}
# - **Average Engagement Rate:** {metrics.get('avg_engagement_rate', 0):.2%}

# ### Platform-by-Platform Breakdown
# """
        
#         for platform, perf in metrics.get('platform_breakdown', {}).items():
#             full_report += f"""
# **{platform}:**
# - Posts: {perf['posts']}
# - Reach: {perf['reach']:,}
# - Impressions: {perf['impressions']:,}
# - Likes: {perf['likes']:,}
# - Shares: {perf['shares']:,}
# - Comments: {perf['comments']:,}
# - Engagement Rate: {perf['engagement_rate']:.2%}
# """
        
#         full_report += "\n\n---\n*Report generated by Agentic CRM - AI-Powered Campaign Manager*\n"
        
#         print("✅ Executive report generated successfully")
#         return {"final_report": full_report, "status": "completed"}
    
#     except Exception as e:
#         print(f"❌ Error generating report: {e}")
#         # Create fallback report
#         fallback_report = create_fallback_report(state, metrics)
#         return {"final_report": fallback_report, "status": "completed"}


# def create_fallback_report(state: AgentState, metrics: Dict) -> str:
#     """Create a structured fallback report"""
#     return f"""# Campaign Performance Report - {state['brand_name']}

# ## Executive Summary
# Campaign for {state['brand_name']} targeting {state['audience']} with the goal of {state['goal']}.

# ## Key Metrics
# - Total Posts: {metrics['total_posts']}
# - Successful Executions: {metrics['successful_posts']}
# - Total Reach: {metrics.get('total_reach', 0):,}
# - Total Impressions: {metrics.get('total_impressions', 0):,}
# - Total Engagement: {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,}

# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
# """


# # ============= BUILD WORKFLOW =============
# def build_campaign_manager_workflow():
#     """Build the complete agentic workflow"""
    
#     workflow = StateGraph(AgentState)
    
#     # Add all nodes
#     workflow.add_node("strategic_planner", strategic_planner_node)
#     workflow.add_node("calendar_manager", calendar_manager_node)
#     workflow.add_node("smart_executor", smart_executor_node)
#     workflow.add_node("performance_tracker", performance_tracker_node)
#     workflow.add_node("intelligent_reporter", intelligent_reporter_node)
    
#     # Define workflow edges
#     workflow.set_entry_point("strategic_planner")
#     workflow.add_edge("strategic_planner", "calendar_manager")
#     workflow.add_edge("calendar_manager", "smart_executor")
#     workflow.add_edge("smart_executor", "performance_tracker")
#     workflow.add_edge("performance_tracker", "intelligent_reporter")
#     workflow.add_edge("intelligent_reporter", END)
    
#     return workflow.compile()


# # ============= MAIN EXECUTION =============
# if __name__ == "__main__":
#     print("=" * 70)
#     print("🤖 AGENTIC CAMPAIGN MANAGER v2.0")
#     print("=" * 70)
    
#     # Initialize workflow
#     campaign_workflow = build_campaign_manager_workflow()
    
#     # Example campaign
#     initial_state = {
#         "brand_name": "TechInnovate AI",
#         "goal": "Launch our new AI-powered analytics platform and generate 1000 signups",
#         "audience": "B2B SaaS founders, CTOs, and data scientists aged 30-50",
#         "additional_context": "We're a Series A startup with $5M funding. Focus on ROI and data-driven decision making.",
#         "posts": [],
#         "calendar": {},
#         "execution_results": [],
#         "performance_metrics": {},
#         "final_report": "",
#         "status": "initiated",
#         "campaign_id": f"camp_{int(time.time())}",
#         "user_id": "demo_user",
#         "scheduled_jobs": []
#     }
    
#     print(f"\n🎯 Campaign Objective: {initial_state['goal']}")
#     print(f"👥 Target Audience: {initial_state['audience']}")
#     print("\n" + "=" * 70)
    
#     # Run workflow
#     try:
#         final_state = campaign_workflow.invoke(initial_state)
        
#         print("\n" + "=" * 70)
#         print("✅ CAMPAIGN WORKFLOW COMPLETED SUCCESSFULLY")
#         print("=" * 70)
        
#         # Display summary
#         print(f"\n📊 CAMPAIGN SUMMARY:")
#         print(f"   - Posts Created: {len(final_state['posts'])}")
#         print(f"   - Calendar Days: {len(final_state['calendar'])}")
#         print(f"   - Executed Posts: {len(final_state['execution_results'])}")
#         print(f"   - Total Reach: {final_state['performance_metrics'].get('total_reach', 0):,}")
#         print(f"   - Status: {final_state['status']}")
        
#         # Save report
#         report_filename = f"campaign_report_{final_state['campaign_id']}.md"
#         with open(report_filename, 'w') as f:
#             f.write(final_state['final_report'])
#         print(f"\n📄 Report saved: {report_filename}")
        
#     except Exception as e:
#         print(f"\n❌ WORKFLOW ERROR: {e}")
#         raise

# print("\n✅ Agentic Campaign Manager initialized successfully!")



# import os
# import json
# import time
# import requests
# from typing import TypedDict, List, Dict, Any
# from datetime import datetime, timedelta
# from langgraph.graph import StateGraph, END
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import SystemMessage, HumanMessage
# from dotenv import load_dotenv
# import schedule
# from concurrent.futures import ThreadPoolExecutor

# # Load environment variables
# load_dotenv()

# # Configuration
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY is required")

# # Initialize LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash-exp",
#     google_api_key=GEMINI_API_KEY,
#     temperature=0.7,
#     convert_system_message_to_human=True 
# )

# # State Definition
# class AgentState(TypedDict):
#     brand_name: str
#     goal: str
#     audience: str
#     additional_context: str  # New: additional business context
#     posts: List[Dict[str, Any]]
#     calendar: Dict[str, List[Dict[str, Any]]]  # Date -> Posts mapping
#     execution_results: List[Dict[str, Any]]
#     performance_metrics: Dict[str, Any]
#     final_report: str
#     status: str
#     campaign_id: str
#     user_id: str
#     scheduled_jobs: List[str]  # Track scheduled tasks


# # ============= REAL IMAGE GENERATION =============
# def generate_image_with_pollinations(post_content: str, platform: str, brand_name: str) -> str:
#     """
#     Generate real images using Pollinations AI (FREE, no API key needed)
#     https://pollinations.ai/
#     """
#     try:
#         # Create AI-powered image prompt
#         image_prompt = f"""Professional {platform} social media post image for {brand_name}: 
#         {post_content[:150]}. 
#         Modern, clean, corporate style, high quality, professional photography"""
        
#         # Clean prompt for URL
#         clean_prompt = image_prompt.replace('\n', ' ').strip()
#         encoded_prompt = requests.utils.quote(clean_prompt)
        
#         # Pollinations.ai FREE image generation (no API key required)
#         # Dimensions optimized for social media
#         dimensions = {
#             "LinkedIn": "1200x627",  # LinkedIn recommended
#             "Threads": "1080x1080",  # Square format
#         }
        
#         size = dimensions.get(platform, "1200x628")
#         image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={size.split('x')[0]}&height={size.split('x')[1]}&nologo=true&enhance=true"
        
#         print(f"   🎨 Generated image for {platform}: {size}")
#         return image_url
        
#     except Exception as e:
#         print(f"⚠️ Image generation failed: {e}")
#         # Fallback to Unsplash (also free, no API key)
#         keywords = extract_keywords_simple(post_content)
#         return f"https://source.unsplash.com/1200x628/?{keywords},business,professional"


# def extract_keywords_simple(text: str) -> str:
#     """Extract keywords for fallback image search"""
#     words = text.lower().split()
#     stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
#     keywords = [w for w in words if len(w) > 4 and w not in stop_words]
#     return ",".join(keywords[:3]) if keywords else "business,technology"


# # ============= AGENT NODE 1: STRATEGIC PLANNER =============
# def strategic_planner_node(state: AgentState):
#     """
#     Strategic planner - ONLY LinkedIn and Threads (Ayrshare free tier)
#     """
#     print(f"\n🎯 [STRATEGIC PLANNER] Analyzing: {state['brand_name']}")
    
#     # ONLY LinkedIn and Threads available on Ayrshare free tier
#     platforms = {
#         "LinkedIn": {"best_time": "10:00", "optimal_days": ["Tuesday", "Wednesday", "Thursday"]},
#         "Threads": {"best_time": "15:00", "optimal_days": ["Monday", "Tuesday", "Thursday"]},
#     }

#     prompt = f"""You are a Senior Social Media Strategist focusing on LinkedIn and Threads.

# **Campaign Brief:**
# - Brand: {state['brand_name']}
# - Goal: {state['goal']}
# - Target Audience: {state['audience']}
# - Context: {state.get('additional_context', 'N/A')}

# **Task:** Create a strategic 6-post campaign:
# - 3 posts for LinkedIn (B2B professional)
# - 3 posts for Threads (engaging, conversational)

# **Requirements for LinkedIn:**
# 1. Professional, thought-leadership tone
# 2. Industry insights and expertise
# 3. 150-200 characters (LinkedIn best practice)
# 4. 3-4 professional hashtags
# 5. Clear business value proposition

# **Requirements for Threads:**
# 1. Conversational, authentic tone
# 2. Engaging questions or hot takes
# 3. 250-280 characters (maximize engagement)
# 4. 2-3 trending hashtags
# 5. Community-building focus

# **Output Format (JSON only, no markdown):**
# [
#     {{
#         "platform": "LinkedIn",
#         "content": "Professional post text with relevant emojis 💼 and #hashtags",
#         "image_concept": "Professional corporate image description",
#         "optimal_time": "10:00",
#         "optimal_day": "Tuesday",
#         "content_type": "thought-leadership/case-study/insights",
#         "target_kpi": "engagement/reach/leads"
#     }},
#     {{
#         "platform": "Threads",
#         "content": "Engaging conversational post 🔥 with #hashtags",
#         "image_concept": "Eye-catching social media visual description",
#         "optimal_time": "15:00",
#         "optimal_day": "Monday",
#         "content_type": "engaging/question/trending",
#         "target_kpi": "engagement/viral-potential"
#     }}
# ]

# Return ONLY the JSON array, no explanations."""

#     try:
#         response = llm.invoke([
#             SystemMessage(content="Return only valid JSON array. No markdown, no code blocks."),
#             HumanMessage(content=prompt)
#         ])
        
#         content = response.content.strip()
        
#         # Clean response
#         if content.startswith("```"):
#             lines = content.split("\n")[1:-1]
#             content = "\n".join(lines).strip()
#         if content.startswith("json"):
#             content = content[4:].strip()
        
#         posts = json.loads(content)
        
#         # Enhance posts with metadata and REAL IMAGES
#         start_date = datetime.now()
#         for i, post in enumerate(posts):
#             # Find next optimal day
#             days_ahead = i + 1
#             scheduled_date = start_date + timedelta(days=days_ahead)
            
#             # Generate REAL image using Pollinations AI
#             image_url = generate_image_with_pollinations(
#                 post['content'], 
#                 post['platform'], 
#                 state['brand_name']
#             )
            
#             post.update({
#                 'post_id': f"post_{int(time.time())}_{i}",
#                 'mediaUrl': image_url,
#                 'scheduledDate': scheduled_date.strftime("%Y-%m-%d"),
#                 'scheduledTime': post.get('optimal_time', f"{9+i}:00"),
#                 'status': 'draft',
#                 'created_at': datetime.now().isoformat(),
#                 'predicted_metrics': {
#                     "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
#                     "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
#                     "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
#                 }
#             })
        
#         print(f"✅ Generated {len(posts)} strategic posts with real images")
#         return {"posts": posts, "status": "planned"}
    
#     except json.JSONDecodeError as e:
#         print(f"⚠️ JSON Error: {e}")
#         fallback_posts = create_fallback_posts(state, platforms, 6)
#         return {"posts": fallback_posts, "status": "planned"}
    
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         fallback_posts = create_fallback_posts(state, platforms, 6)
#         return {"posts": fallback_posts, "status": "planned"}


# def create_fallback_posts(state: AgentState, platforms: Dict, count: int) -> List[Dict]:
#     """Create enhanced fallback posts"""
#     posts = []
#     platform_list = list(platforms.keys())[:count]
    
#     for i, platform in enumerate(platform_list):
#         scheduled_date = datetime.now() + timedelta(days=i+1)
#         posts.append({
#             "post_id": f"post_{int(time.time())}_{i}",
#             "platform": platform,
#             "content": f"🚀 {state['brand_name']} is {state['goal']}! Join us on this exciting journey. #Innovation #{platform} #GrowthMindset",
#             "image_concept": f"Professional {platform} branded visual",
#             "mediaUrl": generate_image_prompt(state['goal'], platform, state['brand_name']),
#             "scheduledDate": scheduled_date.strftime("%Y-%m-%d"),
#             "scheduledTime": platforms[platform]["best_time"],
#             "status": "draft",
#             "content_type": "promotional",
#             "target_kpi": "engagement",
#             "created_at": datetime.now().isoformat(),
#             "predicted_metrics": {
#                 "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
#                 "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
#                 "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
#             }
#         })
    
#     return posts


# # ============= AGENT NODE 2: CALENDAR MANAGER =============
# def calendar_manager_node(state: AgentState):
#     """
#     Create and organize campaign calendar
#     """
#     print("\n📅 [CALENDAR MANAGER] Building campaign calendar...")
    
#     calendar = {}
#     scheduled_jobs = []
    
#     # Organize posts by date
#     for post in state['posts']:
#         date = post['scheduledDate']
#         if date not in calendar:
#             calendar[date] = []
#         calendar[date].append({
#             'post_id': post['post_id'],
#             'platform': post['platform'],
#             'time': post['scheduledTime'],
#             'content_preview': post['content'][:50] + '...',
#             'status': post['status']
#         })
    
#     # Sort calendar entries
#     for date in calendar:
#         calendar[date].sort(key=lambda x: x['time'])
    
#     # Create summary
#     total_days = len(calendar)
#     total_posts = len(state['posts'])
#     platforms_used = list(set([p['platform'] for p in state['posts']]))
    
#     print(f"✅ Calendar created: {total_posts} posts across {total_days} days")
#     print(f"   Platforms: {', '.join(platforms_used)}")
    
#     return {
#         "calendar": calendar,
#         "scheduled_jobs": scheduled_jobs,
#         "status": "calendar_ready"
#     }


# # ============= AGENT NODE 3: SMART EXECUTOR =============
# def smart_executor_node(state: AgentState):
#     """
#     NO RETRY - Single attempt execution to preserve API limits (20/month)
#     """
#     print("\n🚀 [SMART EXECUTOR] Starting execution (NO RETRY MODE)...")
#     print("⚠️  API Limit: 20 calls/month - Using efficient single-attempt strategy")
    
#     results = []
#     platform_map = {
#         'LinkedIn': 'linkedin',
#         'Threads': 'threads',  # Only these 2 platforms on free tier
#     }
    
#     # Count available API calls
#     api_calls_needed = len([p for p in state['posts'] if p.get('platform') in platform_map])
#     print(f"📊 Posts to execute: {api_calls_needed}")
#     print(f"💡 Each post = 1 API call (No retries to save quota)")
    
#     for i, post in enumerate(state['posts']):
#         platform_name = post.get('platform', 'Unknown')
        
#         if platform_name not in platform_map:
#             print(f"   ⚠️  {platform_name} not available on Ayrshare free tier - Skipped")
#             results.append({
#                 "post_id": post.get('post_id'),
#                 "platform": platform_name,
#                 "status": "skipped",
#                 "message": f"Platform {platform_name} not available on free tier (LinkedIn/Threads only)",
#                 "timestamp": datetime.now().isoformat()
#             })
#             continue
        
#         api_platform = platform_map[platform_name]
#         print(f"   📤 [{i+1}/{api_calls_needed}] Executing {platform_name} post...")
        
#         # Execute - NO RETRY
#         if AYRSHARE_API_KEY:
#             result = execute_via_api_single_attempt(post, api_platform)
#         else:
#             result = execute_mock(post, platform_name, i)
        
#         results.append(result)
        
#         # Small delay between API calls to avoid rate limiting
#         if AYRSHARE_API_KEY and i < len(state['posts']) - 1:
#             time.sleep(1)
    
#     success_count = len([r for r in results if r['status'] in ['success', 'scheduled']])
#     print(f"✅ Execution completed: {success_count}/{len(results)} successful")
#     print(f"💾 API calls used: {api_calls_needed} (Remaining: ~{20 - api_calls_needed}/20)")
    
#     return {
#         "execution_results": results,
#         "status": "executed"
#     }


# def execute_via_api_single_attempt(post: Dict, api_platform: str) -> Dict:
#     """
#     Execute post via Ayrshare API - SINGLE ATTEMPT (no retry)
#     """
#     try:
#         payload = {
#             "post": post.get('content'),
#             "platforms": [api_platform],
#             "mediaUrls": [post.get('mediaUrl')] if post.get('mediaUrl') else [],
#             "scheduleDate": f"{post.get('scheduledDate')} {post.get('scheduledTime')}"
#         }
        
#         headers = {
#             'Authorization': f'Bearer {AYRSHARE_API_KEY}',
#             'Content-Type': 'application/json'
#         }
        
#         print(f"      🔄 API call to {api_platform}...")
#         response = requests.post(
#             'https://app.ayrshare.com/api/post',
#             json=payload,
#             headers=headers,
#             timeout=20
#         )
        
#         data = response.json()
        
#         if response.status_code == 200 and data.get('status') == 'success':
#             print(f"      ✅ Scheduled successfully! ID: {data.get('id')}")
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": post['platform'],
#                 "status": "scheduled",
#                 "api_id": data.get('id'),
#                 "refId": data.get('refId'),
#                 "scheduled_date": post.get('scheduledDate'),
#                 "scheduled_time": post.get('scheduledTime'),
#                 "timestamp": datetime.now().isoformat(),
#                 "api_response": data
#             }
#         else:
#             print(f"      ❌ API Error: {data.get('message', 'Unknown error')}")
#             return {
#                 "post_id": post.get('post_id'),
#                 "platform": post['platform'],
#                 "status": "error",
#                 "error": data.get('message', str(data)),
#                 "error_code": data.get('code'),
#                 "timestamp": datetime.now().isoformat()
#             }
    
#     except requests.Timeout:
#         print(f"      ⏱️  API Timeout")
#         return {
#             "post_id": post.get('post_id'),
#             "platform": post['platform'],
#             "status": "error",
#             "error": "API request timeout after 20 seconds",
#             "timestamp": datetime.now().isoformat()
#         }
    
#     except Exception as e:
#         print(f"      ❌ Exception: {str(e)}")
#         return {
#             "post_id": post.get('post_id'),
#             "platform": post['platform'],
#             "status": "error",
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         }


# def execute_mock(post: Dict, platform_name: str, index: int) -> Dict:
#     """Mock execution with realistic metrics"""
#     time.sleep(0.5)  # Simulate API call
    
#     # Platform-specific multipliers for realistic metrics
#     multipliers = {
#         "LinkedIn": 1.5,
#         "Instagram": 2.5,
#         "Twitter": 1.8,
#         "Facebook": 2.0,
#         "YouTube": 3.0,
#         "Threads": 1.3,
#         "TikTok": 4.0
#     }
    
#     base_mult = multipliers.get(platform_name, 1.0)
#     content_hash = abs(hash(post.get('content', '')))
    
#     return {
#         "post_id": post.get('post_id'),
#         "platform": platform_name,
#         "status": "success",
#         "mock_id": f"mock_{int(time.time())}_{index}",
#         "metrics": {
#             "likes": int((content_hash % 500 + 200) * base_mult),
#             "shares": int((content_hash % 100 + 30) * base_mult),
#             "comments": int((content_hash % 50 + 15) * base_mult),
#             "impressions": int((content_hash % 5000 + 2000) * base_mult),
#             "reach": int((content_hash % 3000 + 1000) * base_mult),
#             "engagement_rate": round((content_hash % 10 + 3) / 100, 4),
#             "clicks": int((content_hash % 200 + 50) * base_mult)
#         },
#         "executedAt": datetime.now().isoformat(),
#         "scheduled_date": post.get('scheduledDate'),
#         "scheduled_time": post.get('scheduledTime')
#     }


# # ============= AGENT NODE 4: PERFORMANCE TRACKER =============
# def performance_tracker_node(state: AgentState):
#     """
#     Track and analyze campaign performance
#     """
#     print("\n📊 [PERFORMANCE TRACKER] Analyzing campaign metrics...")
    
#     successful = [r for r in state['execution_results'] if r.get('status') == 'success']
    
#     # Aggregate metrics
#     total_metrics = {
#         'total_posts': len(state['execution_results']),
#         'successful_posts': len(successful),
#         'total_likes': sum(r.get('metrics', {}).get('likes', 0) for r in successful),
#         'total_shares': sum(r.get('metrics', {}).get('shares', 0) for r in successful),
#         'total_comments': sum(r.get('metrics', {}).get('comments', 0) for r in successful),
#         'total_impressions': sum(r.get('metrics', {}).get('impressions', 0) for r in successful),
#         'total_reach': sum(r.get('metrics', {}).get('reach', 0) for r in successful),
#         'total_clicks': sum(r.get('metrics', {}).get('clicks', 0) for r in successful),
#     }
    
#     # Calculate averages
#     if len(successful) > 0:
#         total_metrics['avg_engagement_rate'] = sum(
#             r.get('metrics', {}).get('engagement_rate', 0) for r in successful
#         ) / len(successful)
#         total_metrics['avg_likes_per_post'] = total_metrics['total_likes'] / len(successful)
    
#     # Platform breakdown
#     platform_performance = {}
#     for result in successful:
#         platform = result.get('platform')
#         metrics = result.get('metrics', {})
        
#         if platform not in platform_performance:
#             platform_performance[platform] = {
#                 'posts': 0,
#                 'likes': 0,
#                 'shares': 0,
#                 'comments': 0,
#                 'impressions': 0,
#                 'reach': 0,
#                 'engagement_rate': 0
#             }
        
#         platform_performance[platform]['posts'] += 1
#         for key in ['likes', 'shares', 'comments', 'impressions', 'reach']:
#             platform_performance[platform][key] += metrics.get(key, 0)
#         platform_performance[platform]['engagement_rate'] += metrics.get('engagement_rate', 0)
    
#     # Calculate platform averages
#     for platform, metrics in platform_performance.items():
#         posts_count = metrics['posts']
#         if posts_count > 0:
#             metrics['engagement_rate'] = metrics['engagement_rate'] / posts_count
    
#     total_metrics['platform_breakdown'] = platform_performance
    
#     print(f"✅ Performance tracked: {total_metrics['total_impressions']:,} total impressions")
    
#     return {
#         "performance_metrics": total_metrics,
#         "status": "tracked"
#     }


# # ============= AGENT NODE 5: INTELLIGENT REPORTER =============
# def intelligent_reporter_node(state: AgentState):
#     """
#     Generate comprehensive AI-powered report
#     """
#     print("\n📝 [INTELLIGENT REPORTER] Generating executive report...")
    
#     metrics = state['performance_metrics']
    
#     prompt = f"""You are a Senior Marketing Analytics Director. Create an executive-level campaign performance report.

# **Campaign Overview:**
# - Brand: {state['brand_name']}
# - Objective: {state['goal']}
# - Target Audience: {state['audience']}
# - Campaign Duration: {len(state['calendar'])} days
# - Total Posts: {metrics['total_posts']}

# **Performance Data:**
# {json.dumps(metrics, indent=2)}

# **Required Report Structure:**

# # Executive Summary
# Provide 3-4 sentences highlighting key achievements, ROI indicators, and overall campaign success.

# # Key Performance Indicators
# - Total Reach: {metrics.get('total_reach', 0):,}
# - Total Impressions: {metrics.get('total_impressions', 0):,}
# - Total Engagement: {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,}
# - Average Engagement Rate: {metrics.get('avg_engagement_rate', 0):.2%}
# - Total Clicks: {metrics.get('total_clicks', 0):,}

# # Platform Performance Analysis
# Analyze each platform's performance with:
# - Standout performers and why
# - Underperformers and potential reasons
# - Platform-specific insights

# # Audience Engagement Insights
# - What content types resonated most
# - Engagement patterns observed
# - Audience behavior insights

# # Strategic Recommendations
# Provide 5-7 specific, actionable recommendations for:
# 1. Content optimization
# 2. Platform strategy
# 3. Posting schedule
# 4. Budget allocation
# 5. Future campaign improvements

# # ROI Assessment
# - Campaign effectiveness score (1-10)
# - Cost-per-engagement estimate
# - Projected business impact

# **Important:** Write in professional business language. Be specific with numbers. Provide actionable insights."""

#     try:
#         response = llm.invoke([HumanMessage(content=prompt)])
#         report_content = response.content
        
#         # Add metadata header
#         full_report = f"""# {state['brand_name']} - Social Media Campaign Report
# **Campaign Goal:** {state['goal']}
# **Target Audience:** {state['audience']}
# **Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
# **Campaign Period:** {min([p.get('scheduledDate', '') for p in state['posts']])} to {max([p.get('scheduledDate', '') for p in state['posts']])}

# ---

# {report_content}

# ---

# ## Appendix: Detailed Metrics

# ### Overall Campaign Metrics
# - **Total Posts Scheduled:** {metrics['total_posts']}
# - **Successfully Executed:** {metrics['successful_posts']}
# - **Total Reach:** {metrics.get('total_reach', 0):,} users
# - **Total Impressions:** {metrics.get('total_impressions', 0):,} views
# - **Total Engagement:** {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,} interactions
# - **Total Clicks:** {metrics.get('total_clicks', 0):,}
# - **Average Engagement Rate:** {metrics.get('avg_engagement_rate', 0):.2%}

# ### Platform-by-Platform Breakdown
# """
        
#         for platform, perf in metrics.get('platform_breakdown', {}).items():
#             full_report += f"""
# **{platform}:**
# - Posts: {perf['posts']}
# - Reach: {perf['reach']:,}
# - Impressions: {perf['impressions']:,}
# - Likes: {perf['likes']:,}
# - Shares: {perf['shares']:,}
# - Comments: {perf['comments']:,}
# - Engagement Rate: {perf['engagement_rate']:.2%}
# """
        
#         full_report += "\n\n---\n*Report generated by Agentic CRM - AI-Powered Campaign Manager*\n"
        
#         print("✅ Executive report generated successfully")
#         return {"final_report": full_report, "status": "completed"}
    
#     except Exception as e:
#         print(f"❌ Error generating report: {e}")
#         # Create fallback report
#         fallback_report = create_fallback_report(state, metrics)
#         return {"final_report": fallback_report, "status": "completed"}


# def create_fallback_report(state: AgentState, metrics: Dict) -> str:
#     """Create a structured fallback report"""
#     return f"""# Campaign Performance Report - {state['brand_name']}

# ## Executive Summary
# Campaign for {state['brand_name']} targeting {state['audience']} with the goal of {state['goal']}.

# ## Key Metrics
# - Total Posts: {metrics['total_posts']}
# - Successful Executions: {metrics['successful_posts']}
# - Total Reach: {metrics.get('total_reach', 0):,}
# - Total Impressions: {metrics.get('total_impressions', 0):,}
# - Total Engagement: {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,}

# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
# """


# # ============= BUILD WORKFLOW =============
# def build_campaign_manager_workflow():
#     """Build the complete agentic workflow"""
    
#     workflow = StateGraph(AgentState)
    
#     # Add all nodes
#     workflow.add_node("strategic_planner", strategic_planner_node)
#     workflow.add_node("calendar_manager", calendar_manager_node)
#     workflow.add_node("smart_executor", smart_executor_node)
#     workflow.add_node("performance_tracker", performance_tracker_node)
#     workflow.add_node("intelligent_reporter", intelligent_reporter_node)
    
#     # Define workflow edges
#     workflow.set_entry_point("strategic_planner")
#     workflow.add_edge("strategic_planner", "calendar_manager")
#     workflow.add_edge("calendar_manager", "smart_executor")
#     workflow.add_edge("smart_executor", "performance_tracker")
#     workflow.add_edge("performance_tracker", "intelligent_reporter")
#     workflow.add_edge("intelligent_reporter", END)
    
#     return workflow.compile()


# # ============= MAIN EXECUTION =============
# if __name__ == "__main__":
#     print("=" * 70)
#     print("🤖 AGENTIC CAMPAIGN MANAGER v2.0")
#     print("=" * 70)
    
#     # Initialize workflow
#     campaign_workflow = build_campaign_manager_workflow()
    
#     # Example campaign
#     initial_state = {
#         "brand_name": "TechInnovate AI",
#         "goal": "Launch our new AI-powered analytics platform and generate 1000 signups",
#         "audience": "B2B SaaS founders, CTOs, and data scientists aged 30-50",
#         "additional_context": "We're a Series A startup with $5M funding. Focus on ROI and data-driven decision making.",
#         "posts": [],
#         "calendar": {},
#         "execution_results": [],
#         "performance_metrics": {},
#         "final_report": "",
#         "status": "initiated",
#         "campaign_id": f"camp_{int(time.time())}",
#         "user_id": "demo_user",
#         "scheduled_jobs": []
#     }
    
#     print(f"\n🎯 Campaign Objective: {initial_state['goal']}")
#     print(f"👥 Target Audience: {initial_state['audience']}")
#     print("\n" + "=" * 70)
    
#     # Run workflow
#     try:
#         final_state = campaign_workflow.invoke(initial_state)
        
#         print("\n" + "=" * 70)
#         print("✅ CAMPAIGN WORKFLOW COMPLETED SUCCESSFULLY")
#         print("=" * 70)
        
#         # Display summary
#         print(f"\n📊 CAMPAIGN SUMMARY:")
#         print(f"   - Posts Created: {len(final_state['posts'])}")
#         print(f"   - Calendar Days: {len(final_state['calendar'])}")
#         print(f"   - Executed Posts: {len(final_state['execution_results'])}")
#         print(f"   - Total Reach: {final_state['performance_metrics'].get('total_reach', 0):,}")
#         print(f"   - Status: {final_state['status']}")
        
#         # Save report
#         report_filename = f"campaign_report_{final_state['campaign_id']}.md"
#         with open(report_filename, 'w') as f:
#             f.write(final_state['final_report'])
#         print(f"\n📄 Report saved: {report_filename}")
        
#     except Exception as e:
#         print(f"\n❌ WORKFLOW ERROR: {e}")
#         raise

# print("\n✅ Agentic Campaign Manager initialized successfully!")



# app/agent.py
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

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required")

if not AYRSHARE_API_KEY:
    print("INFO: AYRSHARE_API_KEY not set. Using mock execution mode.")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True 
)

print("✅ LLM initialized with model: gemini-2.0-flash-exp")


# ============= STATE DEFINITION =============
class AgentState(TypedDict):
    brand_name: str
    goal: str
    audience: str
    additional_context: str
    posts: List[Dict[str, Any]]
    calendar: Dict[str, List[Dict[str, Any]]]
    execution_results: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    final_report: str
    status: str
    campaign_id: str
    user_id: str
    scheduled_jobs: List[str]


# ============= IMAGE GENERATION =============
def generate_image_with_pollinations(post_content: str, platform: str, brand_name: str) -> str:
    """
    Generate real images using Pollinations AI (FREE, no API key needed)
    https://pollinations.ai/
    """
    try:
        # Create AI-powered image prompt
        image_prompt = f"""Professional {platform} social media post image for {brand_name}: 
        {post_content[:150]}. 
        Modern, clean, corporate style, high quality, professional photography"""
        
        # Clean prompt for URL
        clean_prompt = image_prompt.replace('\n', ' ').strip()
        encoded_prompt = requests.utils.quote(clean_prompt)
        
        # Pollinations.ai FREE image generation
        dimensions = {
            "LinkedIn": "1200x627",
            "Threads": "1080x1080",
        }
        
        size = dimensions.get(platform, "1200x628")
        width, height = size.split('x')
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&enhance=true"
        
        print(f"   🎨 Generated image for {platform}: {size}")
        return image_url
        
    except Exception as e:
        print(f"⚠️ Image generation failed: {e}")
        # Fallback to Unsplash
        keywords = extract_keywords_simple(post_content)
        return f"https://source.unsplash.com/1200x628/?{keywords},business,professional"


def extract_keywords_simple(text: str) -> str:
    """Extract keywords for fallback image search"""
    words = text.lower().split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
    keywords = [w for w in words if len(w) > 4 and w not in stop_words]
    return ",".join(keywords[:3]) if keywords else "business,technology"


# ============= STRATEGIC PLANNER =============
def strategic_planner_node(state: AgentState):
    """
    Strategic planner - ONLY LinkedIn and Threads (Ayrshare free tier)
    """
    print(f"\n🎯 [STRATEGIC PLANNER] Analyzing: {state['brand_name']}")
    
    # ONLY LinkedIn and Threads available on Ayrshare free tier
    platforms = {
        "LinkedIn": {"best_time": "10:00", "optimal_days": ["Tuesday", "Wednesday", "Thursday"]},
        "Threads": {"best_time": "15:00", "optimal_days": ["Monday", "Tuesday", "Thursday"]},
    }

    prompt = f"""You are a Senior Social Media Strategist focusing on LinkedIn and Threads.

**Campaign Brief:**
- Brand: {state['brand_name']}
- Goal: {state['goal']}
- Target Audience: {state['audience']}
- Context: {state.get('additional_context', 'N/A')}

**Task:** Create a strategic 6-post campaign:
- 3 posts for LinkedIn (B2B professional)
- 3 posts for Threads (engaging, conversational)

**Requirements for LinkedIn:**
1. Professional, thought-leadership tone
2. Industry insights and expertise
3. 150-200 characters (LinkedIn best practice)
4. 3-4 professional hashtags
5. Clear business value proposition

**Requirements for Threads:**
1. Conversational, authentic tone
2. Engaging questions or hot takes
3. 250-280 characters (maximize engagement)
4. 2-3 trending hashtags
5. Community-building focus

**Output Format (JSON only, no markdown):**
[
    {{
        "platform": "LinkedIn",
        "content": "Professional post text with relevant emojis 💼 and #hashtags",
        "image_concept": "Professional corporate image description",
        "optimal_time": "10:00",
        "optimal_day": "Tuesday",
        "content_type": "thought-leadership",
        "target_kpi": "engagement"
    }}
]

Return ONLY the JSON array with 6 posts (3 LinkedIn + 3 Threads), no explanations."""

    try:
        response = llm.invoke([
            SystemMessage(content="Return only valid JSON array. No markdown, no code blocks."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        
        # Clean response
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        if content.startswith("json"):
            content = content[4:].strip()
        
        posts = json.loads(content)
        
        # Enhance posts with metadata and REAL IMAGES
        start_date = datetime.now()
        for i, post in enumerate(posts):
            days_ahead = i + 1
            scheduled_date = start_date + timedelta(days=days_ahead)
            
            # Generate REAL image
            image_url = generate_image_with_pollinations(
                post['content'], 
                post['platform'], 
                state['brand_name']
            )
            
            post.update({
                'post_id': f"post_{int(time.time())}_{i}",
                'mediaUrl': image_url,
                'scheduledDate': scheduled_date.strftime("%Y-%m-%d"),
                'scheduledTime': post.get('optimal_time', f"{9+i}:00"),
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'predicted_metrics': {
                    "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
                    "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
                    "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
                }
            })
        
        print(f"✅ Generated {len(posts)} strategic posts with real images")
        return {"posts": posts, "status": "planned"}
    
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON Error: {e}")
        fallback_posts = create_fallback_posts(state, platforms, 6)
        return {"posts": fallback_posts, "status": "planned"}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        fallback_posts = create_fallback_posts(state, platforms, 6)
        return {"posts": fallback_posts, "status": "planned"}


def create_fallback_posts(state: AgentState, platforms: Dict, count: int) -> List[Dict]:
    """Create fallback posts with REAL images"""
    posts = []
    platform_list = ["LinkedIn", "Threads"] * (count // 2 + 1)
    platform_list = platform_list[:count]
    
    for i, platform in enumerate(platform_list):
        scheduled_date = datetime.now() + timedelta(days=i+1)
        
        content = f"🚀 {state['brand_name']} is transforming {state['goal']}! " \
                  f"Join us on this exciting journey. #Innovation #{platform.replace(' ', '')} #GrowthMindset"
        
        # Generate REAL image
        image_url = generate_image_with_pollinations(content, platform, state['brand_name'])
        
        posts.append({
            "post_id": f"post_{int(time.time())}_{i}",
            "platform": platform,
            "content": content,
            "image_concept": f"Professional {platform} branded visual",
            "mediaUrl": image_url,
            "scheduledDate": scheduled_date.strftime("%Y-%m-%d"),
            "scheduledTime": platforms[platform]["best_time"],
            "status": "draft",
            "content_type": "promotional",
            "target_kpi": "engagement",
            "created_at": datetime.now().isoformat(),
            "predicted_metrics": {
                "reach": f"{1000 + (i * 500)}-{3000 + (i * 1000)}",
                "engagement_rate": f"{2.5 + (i * 0.5):.1f}%",
                "clicks": f"{50 + (i * 25)}-{150 + (i * 50)}"
            }
        })
    
    return posts


# ============= CALENDAR MANAGER =============
def calendar_manager_node(state: AgentState):
    """Create campaign calendar"""
    print("\n📅 [CALENDAR MANAGER] Building campaign calendar...")
    
    calendar = {}
    scheduled_jobs = []
    
    for post in state['posts']:
        date = post['scheduledDate']
        if date not in calendar:
            calendar[date] = []
        calendar[date].append({
            'post_id': post['post_id'],
            'platform': post['platform'],
            'time': post['scheduledTime'],
            'content_preview': post['content'][:50] + '...',
            'status': post['status']
        })
    
    for date in calendar:
        calendar[date].sort(key=lambda x: x['time'])
    
    total_days = len(calendar)
    total_posts = len(state['posts'])
    platforms_used = list(set([p['platform'] for p in state['posts']]))
    
    print(f"✅ Calendar created: {total_posts} posts across {total_days} days")
    print(f"   Platforms: {', '.join(platforms_used)}")
    
    return {
        "calendar": calendar,
        "scheduled_jobs": scheduled_jobs,
        "status": "calendar_ready"
    }


# ============= SMART EXECUTOR =============
def smart_executor_node(state: AgentState):
    """NO RETRY execution to preserve API limits"""
    print("\n🚀 [SMART EXECUTOR] Starting execution (NO RETRY MODE)...")
    print("⚠️  API Limit: 20 calls/month - Using efficient single-attempt strategy")
    
    results = []
    platform_map = {
        'LinkedIn': 'linkedin',
        'Threads': 'threads',
    }
    
    api_calls_needed = len([p for p in state['posts'] if p.get('platform') in platform_map])
    print(f"📊 Posts to execute: {api_calls_needed}")
    print(f"💡 Each post = 1 API call (No retries to save quota)")
    
    for i, post in enumerate(state['posts']):
        platform_name = post.get('platform', 'Unknown')
        
        if platform_name not in platform_map:
            print(f"   ⚠️  {platform_name} not available on free tier - Skipped")
            results.append({
                "post_id": post.get('post_id'),
                "platform": platform_name,
                "status": "skipped",
                "message": f"Platform not available on free tier",
                "timestamp": datetime.now().isoformat()
            })
            continue
        
        api_platform = platform_map[platform_name]
        print(f"   📤 [{i+1}/{api_calls_needed}] Executing {platform_name} post...")
        
        if AYRSHARE_API_KEY:
            result = execute_via_api_single_attempt(post, api_platform)
        else:
            result = execute_mock(post, platform_name, i)
        
        results.append(result)
        
        if AYRSHARE_API_KEY and i < len(state['posts']) - 1:
            time.sleep(1)
    
    success_count = len([r for r in results if r['status'] in ['success', 'scheduled']])
    print(f"✅ Execution completed: {success_count}/{len(results)} successful")
    print(f"💾 API calls used: {api_calls_needed} (Remaining: ~{20 - api_calls_needed}/20)")
    
    return {
        "execution_results": results,
        "status": "executed"
    }


def execute_via_api_single_attempt(post: Dict, api_platform: str) -> Dict:
    """Execute via Ayrshare API - SINGLE ATTEMPT"""
    try:
        payload = {
            "post": post.get('content'),
            "platforms": [api_platform],
            "mediaUrls": [post.get('mediaUrl')] if post.get('mediaUrl') else [],
            "scheduleDate": f"{post.get('scheduledDate')} {post.get('scheduledTime')}"
        }
        
        headers = {
            'Authorization': f'Bearer {AYRSHARE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        print(f"      🔄 API call to {api_platform}...")
        response = requests.post(
            'https://app.ayrshare.com/api/post',
            json=payload,
            headers=headers,
            timeout=20
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get('status') == 'success':
            print(f"      ✅ Scheduled successfully! ID: {data.get('id')}")
            return {
                "post_id": post.get('post_id'),
                "platform": post['platform'],
                "status": "scheduled",
                "api_id": data.get('id'),
                "refId": data.get('refId'),
                "scheduled_date": post.get('scheduledDate'),
                "scheduled_time": post.get('scheduledTime'),
                "timestamp": datetime.now().isoformat()
            }
        else:
            print(f"      ❌ API Error: {data.get('message', 'Unknown')}")
            return {
                "post_id": post.get('post_id'),
                "platform": post['platform'],
                "status": "error",
                "error": data.get('message', str(data)),
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        print(f"      ❌ Exception: {str(e)}")
        return {
            "post_id": post.get('post_id'),
            "platform": post['platform'],
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def execute_mock(post: Dict, platform_name: str, index: int) -> Dict:
    """Mock execution with realistic metrics"""
    time.sleep(0.5)
    
    multipliers = {
        "LinkedIn": 1.5,
        "Threads": 1.3,
    }
    
    base_mult = multipliers.get(platform_name, 1.0)
    content_hash = abs(hash(post.get('content', '')))
    
    return {
        "post_id": post.get('post_id'),
        "platform": platform_name,
        "status": "success",
        "mock_id": f"mock_{int(time.time())}_{index}",
        "metrics": {
            "likes": int((content_hash % 500 + 200) * base_mult),
            "shares": int((content_hash % 100 + 30) * base_mult),
            "comments": int((content_hash % 50 + 15) * base_mult),
            "impressions": int((content_hash % 5000 + 2000) * base_mult),
            "reach": int((content_hash % 3000 + 1000) * base_mult),
            "engagement_rate": round((content_hash % 10 + 3) / 100, 4),
            "clicks": int((content_hash % 200 + 50) * base_mult)
        },
        "executedAt": datetime.now().isoformat(),
        "scheduled_date": post.get('scheduledDate'),
        "scheduled_time": post.get('scheduledTime')
    }


# ============= PERFORMANCE TRACKER =============
def performance_tracker_node(state: AgentState):
    """Track campaign performance"""
    print("\n📊 [PERFORMANCE TRACKER] Analyzing metrics...")
    
    successful = [r for r in state['execution_results'] if r.get('status') == 'success']
    
    total_metrics = {
        'total_posts': len(state['execution_results']),
        'successful_posts': len(successful),
        'total_likes': sum(r.get('metrics', {}).get('likes', 0) for r in successful),
        'total_shares': sum(r.get('metrics', {}).get('shares', 0) for r in successful),
        'total_comments': sum(r.get('metrics', {}).get('comments', 0) for r in successful),
        'total_impressions': sum(r.get('metrics', {}).get('impressions', 0) for r in successful),
        'total_reach': sum(r.get('metrics', {}).get('reach', 0) for r in successful),
        'total_clicks': sum(r.get('metrics', {}).get('clicks', 0) for r in successful),
    }
    
    if len(successful) > 0:
        total_metrics['avg_engagement_rate'] = sum(
            r.get('metrics', {}).get('engagement_rate', 0) for r in successful
        ) / len(successful)
    
    platform_performance = {}
    for result in successful:
        platform = result.get('platform')
        metrics = result.get('metrics', {})
        
        if platform not in platform_performance:
            platform_performance[platform] = {
                'posts': 0, 'likes': 0, 'shares': 0, 'comments': 0,
                'impressions': 0, 'reach': 0, 'engagement_rate': 0
            }
        
        platform_performance[platform]['posts'] += 1
        for key in ['likes', 'shares', 'comments', 'impressions', 'reach']:
            platform_performance[platform][key] += metrics.get(key, 0)
        platform_performance[platform]['engagement_rate'] += metrics.get('engagement_rate', 0)
    
    for platform, metrics in platform_performance.items():
        if metrics['posts'] > 0:
            metrics['engagement_rate'] = metrics['engagement_rate'] / metrics['posts']
    
    total_metrics['platform_breakdown'] = platform_performance
    
    print(f"✅ Performance tracked: {total_metrics['total_impressions']:,} impressions")
    
    return {
        "performance_metrics": total_metrics,
        "status": "tracked"
    }


# ============= INTELLIGENT REPORTER =============
def intelligent_reporter_node(state: AgentState):
    """Generate AI-powered report"""
    print("\n📝 [INTELLIGENT REPORTER] Generating report...")
    
    metrics = state['performance_metrics']
    
    report = f"""# {state['brand_name']} - Campaign Performance Report

**Campaign Goal:** {state['goal']}
**Target Audience:** {state['audience']}
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

## Executive Summary

Campaign successfully executed with {metrics['successful_posts']} posts across LinkedIn and Threads platforms.

## Key Performance Indicators

- **Total Reach:** {metrics.get('total_reach', 0):,} users
- **Total Impressions:** {metrics.get('total_impressions', 0):,} views
- **Total Engagement:** {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0):,} interactions
- **Average Engagement Rate:** {metrics.get('avg_engagement_rate', 0):.2%}
- **Total Clicks:** {metrics.get('total_clicks', 0):,}

## Platform Performance
"""
    
    for platform, perf in metrics.get('platform_breakdown', {}).items():
        report += f"""
### {platform}
- Posts: {perf['posts']}
- Reach: {perf['reach']:,}
- Impressions: {perf['impressions']:,}
- Engagement Rate: {perf['engagement_rate']:.2%}
"""
    
    report += "\n\n---\n*Report generated by Agentic CRM v2.0*\n"
    
    print("✅ Report generated successfully")
    
    return {
        "final_report": report,
        "status": "completed"
    }


# ============= BUILD WORKFLOW =============
def build_campaign_manager_workflow():
    """Build the complete workflow"""
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("strategic_planner", strategic_planner_node)
    workflow.add_node("calendar_manager", calendar_manager_node)
    workflow.add_node("smart_executor", smart_executor_node)
    workflow.add_node("performance_tracker", performance_tracker_node)
    workflow.add_node("intelligent_reporter", intelligent_reporter_node)
    
    workflow.set_entry_point("strategic_planner")
    workflow.add_edge("strategic_planner", "calendar_manager")
    workflow.add_edge("calendar_manager", "smart_executor")
    workflow.add_edge("smart_executor", "performance_tracker")
    workflow.add_edge("performance_tracker", "intelligent_reporter")
    workflow.add_edge("intelligent_reporter", END)
    
    return workflow.compile()


print("✅ Campaign Manager workflow initialized successfully!")