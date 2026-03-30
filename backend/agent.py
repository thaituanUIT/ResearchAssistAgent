import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import dotenv

dotenv.load_dotenv()

class AgentState(TypedDict, total=False):
    pdf_texts: List[str]
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

def input_router(state: AgentState):
    """Routes to prompt_analyzer if user_prompt exists, else to planner."""
    if state.get("user_prompt"):
        return "prompt_analyzer"
    return "planner"

def planner_node(state: AgentState):
    """Determines whether the input is simple or complex."""
    pdf_texts = state.get("pdf_texts", [])
    route = "simple" if len(pdf_texts) == 1 else "complex"
    return {"route": route}

def route_analyzer(state: AgentState):
    """Routes to Reader or Comparator."""
    if state.get("route", "") == "complex":
        return "comparator"
    return "reader"

def reader_node(state: AgentState):
    """Summarizes a single PDF text."""
    pdf_texts = state.get("pdf_texts", [])
    text_content = pdf_texts[0][:80000] if pdf_texts else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic Reader. Summarize the following paper text concisely and highlight the main contributions, methodology, and results."),
        ("human", "Paper text:\n{pdf_text}")
    ])
    chain = prompt | llm
    response = chain.invoke({"pdf_text": text_content})
    return {"working_document": response.content}

def comparator_node(state: AgentState):
    """Compares multiple PDF texts."""
    pdf_texts = state.get("pdf_texts", [])
    combined_texts = ""
    for i, text in enumerate(pdf_texts):
        combined_texts += f"--- Document {i+1} ---\n{text[:20000]}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic Comparator. Compare the following papers, highlighting their commonalities, differences, methodologies, and overall impact."),
        ("human", "Papers:\n{pdf_texts}")
    ])
    chain = prompt | llm
    response = chain.invoke({"pdf_texts": combined_texts})
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
    pdf_texts = state.get("pdf_texts", [])
    combined_texts = ""
    for i, text in enumerate(pdf_texts):
        combined_texts += f"--- Document {i+1} ---\n{text[:20000]}\n\n"
        
    evaluation = state.get("evaluation", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Retriever. The previous evaluation flagged missing info or inconsistencies. Re-read the original texts and extract the missing methodologies or clear up the contradictions mentioned in the evaluation."),
        ("human", "Evaluation raising concerns:\n{evaluation}\n\nOriginal Papers:\n{pdf_texts}")
    ])
    chain = prompt | llm
    response = chain.invoke({"evaluation": evaluation, "pdf_texts": combined_texts})
    return {"retrieved_context": response.content}

def synthesizer_node(state: AgentState):
    """Compiles the final report."""
    working_document = state.get("working_document", "")
    evaluation = state.get("evaluation", "")
    retrieved_context = state.get("retrieved_context", "")
    
    context_instruction = f"\nExtra context from Retriever:\n{retrieved_context}" if retrieved_context else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Synthesizer. Combine the Reader/Comparator's working document, the Evaluator's analysis, and any extra retrieved context into a final, well-structured markdown report suitable for a UI dashboard. Use headings, bullet points, and bold text to make it easy to read. Do not output raw JSON, only markdown."),
        ("human", "Working Document:\n{working_document}\n\nEvaluation:\n{evaluation}{context_instruction}")
    ])
    chain = prompt | llm
    response = chain.invoke({
        "working_document": working_document, 
        "evaluation": evaluation, 
        "context_instruction": context_instruction
    })
    return {"synthesis": response.content}

def prompt_analyzer(state: AgentState):
    """Analyzes the user prompt using document context and chat history."""
    user_prompt = state.get("user_prompt", "")
    chat_history = state.get("chat_history", [])
    working_document = state.get("working_document", "")
    synthesis = state.get("synthesis", "")
    
    # Format chat history
    history_text = ""
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful research assistant named ResearchAssist. Answer the user's question based on the provided document context and the previous synthesis.\n\nContext:\n{working_document}\n\nSynthesis:\n{synthesis}\n\nChat History:\n{history_text}"),
        ("human", "{user_prompt}")
    ])
    chain = prompt | llm
    response = chain.invoke({
        "working_document": working_document,
        "synthesis": synthesis,
        "history_text": history_text,
        "user_prompt": user_prompt
    })
    return {"chat_response": response.content}

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
