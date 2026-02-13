import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"
tavily_search = TavilySearchResults(max_results=5, search_depth="advanced")

# --- Nodes ---

def node_analyze_resume(state: list):
    """
    STEP 1: Analyze First
    Gemini reviews the raw resume to generate a score and tips.
    """
    resume_text = state[0]
    today_str = datetime.now().strftime("%B %d, %Y")

    prompt = f"""
    TODAY'S DATE: {today_str}
    You are an applicant tracking system used by companies to analyze resume for the required job roles. Be strict while calculating the ATS score and give proper actionable points to implement on the resume to make it better based on the data of resume: {resume_text}
    
    Return strictly JSON with:
    1. "resume_score": (int 0-100)
    2. "improvement_points": [list of 5 actionable strings]
    """

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    # AI Analysis stored at index 1
    state.append(response.text)
    return state

def node_extract_search_query(state: list):
    """
    STEP 2: Scrub & Create Query
    Uses the resume and the improvement points to find the best search keywords.
    """
    resume_text = state[0]
    ai_analysis = json.loads(state[1])
    tips = ai_analysis.get("improvement_points", [])
    
    prompt = f"""
    Extract the ideal job title and top skills from this resume. 
    Also consider these improvement tips: {tips}
    
    CRITICAL: Remove all PII (Name, Email, Phone).
    Resume content: {resume_text[:500]}
    
    Return only a short search string: e.g., 'Senior Python Developer FastAPI'
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    
    # Clean query stored at index 2
    state.append(response.text.strip())
    return state

def node_search_jobs(state: list):
    """
    STEP 3: Search
    Uses the scrubbed query for real-time results.
    """
    clean_query = state[2]
    today = datetime.now().strftime("%Y-%m-%d")
    
    query = f"Software roles posted after {today} for: {clean_query}"
    
    # Raw Tavily results stored at index 3
    results = tavily_search.invoke({"query": query})
    state.append(results)
    return state

# --- Updated Graph Assembly ---
# State list order: [0: Raw Text, 1: AI JSON, 2: Clean Query, 3: Tavily Results]

builder = StateGraph(list)

builder.add_node("analyze", node_analyze_resume)
builder.add_node("cleaner", node_extract_search_query)
builder.add_node("search", node_search_jobs)

builder.set_entry_point("analyze")
builder.add_edge("analyze", "cleaner")
builder.add_edge("cleaner", "search")
builder.add_edge("search", END)

resume_agent = builder.compile()