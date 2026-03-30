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

# Use mixtral for its larger 32k context window on Groq
llm = ChatGroq(model="mixtral-8x7b-32768")

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

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("reader", reader_node)
workflow.add_node("comparator", comparator_node)
workflow.add_node("evaluator", evaluator_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.add_edge(START, "planner")
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

app_graph = workflow.compile()
