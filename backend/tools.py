from langchain_core.tools import tool
from typing import List
import os
import requests

@tool
def generate_flowchart(nodes: List[str], edges: List[List[str]]) -> str:
    """
    Creates a mermaid flowchart from a list of nodes and a list of edges.
    Use this tool when the user asks to generate a flowchart, process flow, or concept map.
    Nodes should be short, descriptive strings representing steps or concepts.
    Edges should be exactly two strings representing a connection from the first to the second.
    """
    s = "```mermaid\ngraph TD\n"
    for i, n in enumerate(nodes):
        safe_n = str(n).replace('"', "'").replace('\n', ' ')
        s += f'{i}["{safe_n}"]\n'
    for a, b in edges:
        try:
            s += f"{nodes.index(a)} --> {nodes.index(b)}\n"
            pass
    s += "```"
    return s

def search_scholar_api(query: str, scisbd: str = "0", num: int = 5) -> str:
    """Takes a query and sort parameter (0 for relevance, 1 for date), and number of results and calls SerpAPI."""
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return "**Error:** SERPAPI_API_KEY is not configured in the `.env` file! Please add it to search Google Scholar."
        
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": num
    }
    if scisbd == "1":
        params["scisbd"] = "1"
        
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        response.raise_for_status()
        results = response.json()
        
        organic = results.get("organic_results", [])
        if not organic:
            return "No relevant papers found on Google Scholar for that query."
            
        top_n = organic[:num]
        
        out = f"Here are {len(top_n)} papers that are relevant:\n\n"
        for i, res in enumerate(top_n):
            title = res.get("title", "Unknown Title")
            link = res.get("link", "#")
            snippet = res.get("snippet", "")
            citations = res.get("inline_links", {}).get("cited_by", {}).get("total", 0)
            
            out += f"<details class='scholar-dropdown'>\n"
            out += f"  <summary><strong>{i+1}. {title}</strong></summary>\n"
            out += f"  <div style='margin-top: 10px; padding-left: 10px; border-left: 2px solid #6366f1; font-size: 0.9em; opacity: 0.9;'>\n"
            out += f"    <p><em>{snippet}</em></p>\n"
            out += f"    <p style='margin-top: 8px;'><strong>Citations:</strong> {citations} | <a href='{link}' target='_blank' rel='noopener noreferrer'>🔗 Read on Google Scholar</a></p>\n"
            out += f"  </div>\n"
            out += f"</details>\n\n"
            
        return out
        
    except Exception as e:
        return f"**Error executing Google Scholar search:** {str(e)}"
