import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import dotenv
from backend.flowchart_agent import flowchart_graph
from backend.vector_store import retrieve_relevant_context
from langchain_core.tools import tool

dotenv.load_dotenv()

class AgentState(TypedDict, total=False):
    paper_metadata: List[dict]
    route: str
    working_document: str
    evaluation: str
    confidence_level: str
    retrieved_context: str
    synthesis: str
    user_prompt: str
    chat_history: List[dict]
    chat_response: str

# Use mixtral for its larger 32k context window on Groq
llm = ChatGroq(model="mixtral-8x7b-32768")

@tool
def request_flowchart(instruction: str, text_to_analyze: str) -> str:
    """Builds a customized flowchart using a dedicated multi-agent pipeline based on the provided instruction and text context. Use this tool ONLY when the user asks for a flowchart, visual map, or diagram."""
    res = flowchart_graph.invoke({"instruction": instruction, "context": text_to_analyze})
    return res.get("mermaid_graph", "")

def input_router(state: AgentState):
    """Routes to planner if new pdfs are provided, else prompt_analyzer for chat."""
    if state.get("paper_metadata"):
        return "planner"
    return "prompt_analyzer"

def planner_node(state: AgentState):
    """Determines whether the input is simple or complex."""
    paper_metadata = state.get("paper_metadata", [])
    route = "simple" if len(paper_metadata) == 1 else "complex"
    return {"route": route}

def route_analyzer(state: AgentState):
    """Routes to Reader or Comparator."""
    if state.get("route", "") == "complex":
        return "comparator"
    return "reader"

def reader_node(state: AgentState):
    """Summarizes a single PDF text."""
    paper_metadata = state.get("paper_metadata", [])
    if paper_metadata:
        meta = paper_metadata[0]
        text_content = retrieve_relevant_context(
            "Abstract methodology contributions main results conclusion limitations", 
            k=10, 
            filter_dict={"paper_id": meta.get("paper_id")}
        )
    else:
        text_content = ""
    user_prompt = state.get("user_prompt", "")
    
    sys_msg = "You are an expert academic Reader. Summarize the following paper text concisely and highlight the main contributions, methodology, and results."
    if user_prompt:
        sys_msg += f"\nThe user also gave this specific instruction: {user_prompt}\nIf the instruction asks for a flowchart, use your request_flowchart tool."
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "Paper text:\n{pdf_text}")
    ])
    chain = prompt | llm.bind_tools([request_flowchart])
    response = chain.invoke({"pdf_text": text_content})
    
    content = response.content or ""
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "request_flowchart":
                content += "\n\n" + request_flowchart.invoke(tc["args"])
                
    return {"working_document": content}

def comparator_node(state: AgentState):
    """Compares multiple PDF texts."""
    paper_metadata = state.get("paper_metadata", [])
    text_content = retrieve_relevant_context(
        "abstract method approach dataset methodology findings conclusion comparison", 
        k=15
    )
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic Comparator. Compare the following papers, highlighting their commonalities, differences, methodologies, and overall impact."),
        ("human", "Papers Excerpts:\n{pdf_texts}")
    ])
    chain = prompt | llm
    response = chain.invoke({"pdf_texts": text_content})
    return {"working_document": response.content}

def evaluator_node(state: AgentState):
    """Evaluates reliability, strengths, and weaknesses."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Evaluator. Analyze the provided summary or comparison. Determine its reliability, strengths, and weaknesses.\nIf the text has major inconsistencies, missing key methodology, or is highly ambiguous, you MUST include the exact tag '[CONFIDENCE: LOW]' in your response.\nOtherwise, include '[CONFIDENCE: HIGH]'. Provide your analysis before the tag."),
        ("human", "Working Document:\n{working_document}")
    ])
    chain = prompt | llm
    response = chain.invoke({"working_document": state.get("working_document", "")})
    content = response.content
    
    confidence = "low" if "[CONFIDENCE: LOW]" in content else "high"
    return {"evaluation": content, "confidence_level": confidence}

def check_confidence(state: AgentState):
    """Routes based on confidence level."""
    if state.get("confidence_level", "") == "low":
        return "retriever"
    return "synthesizer"

def retriever_node(state: AgentState):
    """Runs a second pass to retrieve missing context."""
    evaluation = state.get("evaluation", "")
    text_content = retrieve_relevant_context(evaluation, k=10)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Retriever. The previous evaluation flagged missing info or inconsistencies. Extract the missing methodologies or clear up the contradictions mentioned in the evaluation."),
        ("human", "Evaluation raising concerns:\n{evaluation}\n\nSearch Vector Context:\n{pdf_texts}")
    ])
    chain = prompt | llm
    response = chain.invoke({"evaluation": evaluation, "pdf_texts": text_content})
    return {"retrieved_context": response.content}

def synthesizer_node(state: AgentState):
    """Compiles the final report."""
    working_document = state.get("working_document", "")
    evaluation = state.get("evaluation", "")
    retrieved_context = state.get("retrieved_context", "")
    user_prompt = state.get("user_prompt", "")
    
    context_instruction = f"\nExtra context from Retriever:\n{retrieved_context}" if retrieved_context else ""
    
    sys_msg = "You are a Synthesizer. Combine the Reader/Comparator's working document, the Evaluator's analysis, and any extra retrieved context into a final, well-structured markdown report suitable for a UI dashboard. Use headings, bullet points, and bold text to make it easy to read. Do not output raw JSON, only markdown."
    if user_prompt:
        sys_msg += f"\nThe user also gave this instruction: {user_prompt}\nIf resolving this requires a flowchart, use your request_flowchart tool."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "Working Document:\n{working_document}\n\nEvaluation:\n{evaluation}{context_instruction}")
    ])
    chain = prompt | llm.bind_tools([request_flowchart])
    response = chain.invoke({
        "working_document": working_document, 
        "evaluation": evaluation, 
        "context_instruction": context_instruction
    })
    
    content = response.content or ""
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "request_flowchart":
                content += "\n\n" + request_flowchart.invoke(tc["args"])
                
    return {"synthesis": content}

def prompt_analyzer(state: AgentState):
    """Analyzes the user prompt using document context and chat history."""
    user_prompt = state.get("user_prompt", "")
    chat_history = state.get("chat_history", [])
    working_document = state.get("working_document", "")
    synthesis = state.get("synthesis", "")
    
    # Vector DB Search context based on user prompt!
    search_context = retrieve_relevant_context(user_prompt, k=8)
    
    # Format chat history
    history_text = ""
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"
    
    sys_msg = "You are a helpful research assistant named ResearchAssist. Answer the user's question based on the provided document context, vector search results, and previous synthesis.\nIf the user asks for a flowchart or visual diagram, use your request_flowchart tool.\n\nOverarching Context:\n{working_document}\n\nTargeted Vector Search Context:\n{search_context}\n\nSynthesis:\n{synthesis}\n\nChat History:\n{history_text}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "{user_prompt}")
    ])
    chain = prompt | llm.bind_tools([request_flowchart])
    response = chain.invoke({
        "working_document": working_document,
        "search_context": search_context,
        "synthesis": synthesis,
        "history_text": history_text,
        "user_prompt": user_prompt
    })
    
    content = response.content or ""
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "request_flowchart":
                content += "\n\n" + request_flowchart.invoke(tc["args"])
                
    return {"chat_response": content}

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("reader", reader_node)
workflow.add_node("comparator", comparator_node)
workflow.add_node("evaluator", evaluator_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("prompt_analyzer", prompt_analyzer)

workflow.add_conditional_edges(START, input_router, {
    "planner": "planner",
    "prompt_analyzer": "prompt_analyzer"
})
workflow.add_conditional_edges("planner", route_analyzer, {
    "reader": "reader",
    "comparator": "comparator"
})
workflow.add_edge("reader", "evaluator")
workflow.add_edge("comparator", "evaluator")
workflow.add_conditional_edges("evaluator", check_confidence, {
    "retriever": "retriever",
    "synthesizer": "synthesizer"
})
workflow.add_edge("retriever", "synthesizer")
workflow.add_edge("synthesizer", END)
workflow.add_edge("prompt_analyzer", END)

app_graph = workflow.compile()
