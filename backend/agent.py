import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import dotenv
from backend.flowchart_agent import flowchart_graph
from backend.vector_store import retrieve_relevant_context
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.tools import search_scholar_api

dotenv.load_dotenv()

class AgentState(TypedDict, total=False):
    paper_metadata: List[dict]
    user_prompt: str
    chat_history: List[dict]
    search_results: str
    chat_response: str
    user_id: str
    session_id: str

# Use mixtral for its larger 32k context window on Groq
llm = ChatGroq(model="mixtral-8x7b-32768")

@tool
def request_flowchart(instruction: str, text_to_analyze: str) -> str:
    """Builds a customized flowchart using a dedicated multi-agent pipeline based on the provided instruction and text context. Use this tool ONLY when the user asks for a flowchart, visual map, or diagram."""
    res = flowchart_graph.invoke({"instruction": instruction, "context": text_to_analyze})
    return res.get("mermaid_graph", "")

def input_router(state: AgentState):
    """Routes to searcher or prompt_analyzer."""
    user_prompt = state.get("user_prompt", "")
    sys_msg = "You are a routing assistant. Analyze the user prompt. If the user is asking to search for NEW external academic papers (e.g. 'search google scholar', 'find me papers on', 'retrieve recent papers'), output 'searcher'. Otherwise, if they are asking questions about existing documents or general chat, output 'prompt_analyzer'. Only output the exact string."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "{user_prompt}")
    ])
    
    try:
        response = (prompt | llm).invoke({"user_prompt": user_prompt})
        route = response.content.strip().replace("'", "").lower()
        if "searcher" in route:
            return "searcher"
    except:
        pass
        
    return "prompt_analyzer"

def prompt_analyzer(state: AgentState):
    """Analyzes the user prompt using vector context and chat history."""
    user_prompt = state.get("user_prompt", "")
    chat_history = state.get("chat_history", [])
    user_id = state.get("user_id", "")
    
    # Secure vector filtering to only look at user's personal context and papers
    filter_dict = {"user_id": {"$eq": user_id}} if user_id else None
    
    # Vector DB Search context based on user prompt!
    search_context = retrieve_relevant_context(user_prompt, k=8, filter_dict=filter_dict)
    
    # Format chat history
    history_text = ""
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"
    
    sys_msg = "You are a helpful research assistant named ResearchAssist. Answer the user's question based on the retrieved vector search context and previous chat history.\nIf the user asks for a flowchart or visual map, use your request_flowchart tool.\n\nRetrieved Vector Database Context:\n{search_context}\n\nChat History:\n{history_text}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "{user_prompt}")
    ])
    chain = prompt | llm.bind_tools([request_flowchart])
    response = chain.invoke({
        "search_context": search_context,
        "history_text": history_text,
        "user_prompt": user_prompt
    })
    
    content = response.content or ""
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "request_flowchart":
                content += "\n\n" + request_flowchart.invoke(tc["args"])
                
    return {"chat_response": content}

class SearchCriteria(BaseModel):
    query: str = Field(description="The exact search string to query Google Scholar based on the user's prompt.")
    scisbd: str = Field(description="Sort algorithm. Output '1' if the user requested the most recent/up to date papers. Output '0' otherwise.")
    num_results: int = Field(description="The number of papers the user wants to retrieve. Default to 5 if not explicitly stated.")

def searcher_node(state: AgentState):
    """Parses criteria from chat and calls SerpAPI Google Scholar."""
    user_prompt = state.get("user_prompt", "")
    sys_msg = "You are an expert Search Criteria Extractor. Analyze the user prompt to determine the exact query string, the sorting algorithm, and the number of results needed for a Google Scholar search."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "{user_prompt}")
    ])
    
    chain = prompt | llm.with_structured_output(SearchCriteria)
    try:
        criteria = chain.invoke({"user_prompt": user_prompt})
        results_markdown = search_scholar_api(criteria.query, criteria.scisbd, criteria.num_results)
        return {"search_results": results_markdown}
    except Exception as e:
        return {"search_results": f"**Error parsing search criteria or calling API:** {e}"}

def search_evaluator_node(state: AgentState):
    """Evaluates the retrieved Google Scholar results for clarity and reliability."""
    search_results = state.get("search_results", "")
    if not search_results or "**Error" in search_results:
        return {"chat_response": search_results or "No results generated."}
        
    sys_msg = "You are an expert Search Evaluator. Read the following retrieved Google Scholar snippets. Write a concise, 1-2 sentence paragraph evaluating the overall relevance, clarity, and reliability of these findings based on the user's query. Output only the evaluation paragraph."
    user_prompt = state.get("user_prompt", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "User Query: {user_prompt}\n\nRetrieved Search Results:\n{search_results}")
    ])
    try:
        eval_res = (prompt | llm).invoke({"user_prompt": user_prompt, "search_results": search_results})
        evaluation = f"### Search Analysis\n**{eval_res.content.strip()}**\n\n---\n\n{search_results}"
        return {"chat_response": evaluation}
    except Exception as e:
        return {"chat_response": search_results}

workflow = StateGraph(AgentState)
workflow.add_node("prompt_analyzer", prompt_analyzer)
workflow.add_node("searcher", searcher_node)
workflow.add_node("search_evaluator", search_evaluator_node)

workflow.add_conditional_edges(START, input_router, {
    "prompt_analyzer": "prompt_analyzer",
    "searcher": "searcher"
})
workflow.add_edge("searcher", "search_evaluator")
workflow.add_edge("search_evaluator", END)
workflow.add_edge("prompt_analyzer", END)

app_graph = workflow.compile()
