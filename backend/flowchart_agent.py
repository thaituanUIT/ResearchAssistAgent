from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from backend.tools import generate_flowchart
import dotenv

dotenv.load_dotenv()

# We need a model with good function calling. Mixtral handles structured output decently on Groq.
llm = ChatGroq(model="mixtral-8x7b-32768")

class FlowchartState(TypedDict, total=False):
    instruction: str
    context: str
    nodes: List[str]
    edges: List[List[str]]
    mermaid_graph: str

class NodesOutput(BaseModel):
    nodes: List[str] = Field(description="Strict list of short, descriptive strings representing the extracted steps or core concepts.")

class EdgesOutput(BaseModel):
    edges: List[List[str]] = Field(description="Strict list of dependencies mapped as [source_node, target_node] arrays. Both strings must EXACTLY match strings from the nodes list.")

def step_extractor(state: FlowchartState):
    """Answers 'What are the steps/entities?'"""
    sys_msg = "You are an expert Step Extractor. Your job is to extract the key steps, concepts, or entities from the provided context to build a flowchart. Output ONLY the required JSON list of strings."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "Instruction: {instruction}\n\nContext block to analyze:\n{context}")
    ])
    
    chain = prompt | llm.with_structured_output(NodesOutput)
    response = chain.invoke({"instruction": state.get("instruction", ""), "context": state.get("context", "")[0:50000]})
    
    return {"nodes": response.nodes}

def dependencies_extractor(state: FlowchartState):
    """Answers 'How do these steps connect?'"""
    sys_msg = "You are an expert Dependencies Extractor. Given a list of exact nodes and the original context, determine the relationships and directional dependencies between them to form a flowchart. Output the required JSON list of string pairs representing edges."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", "Extracted Nodes: {nodes}\n\nContext block to analyze:\n{context}")
    ])
    
    chain = prompt | llm.with_structured_output(EdgesOutput)
    response = chain.invoke({"nodes": state.get("nodes", []), "context": state.get("context", "")[0:50000]})
    
    return {"edges": response.edges}

def graph_builder(state: FlowchartState):
    """Final node that utilizes the generate_flowchart tool."""
    nodes = state.get("nodes", [])
    edges = state.get("edges", [])
    
    try:
        mermaid_str = generate_flowchart.invoke({"nodes": nodes, "edges": edges})
    except Exception as e:
        mermaid_str = f"```mermaid\n%% Error parsing flowchart parameters: {e}\n```"
        
    return {"mermaid_graph": mermaid_str}

flowchart_workflow = StateGraph(FlowchartState)
flowchart_workflow.add_node("step_extractor", step_extractor)
flowchart_workflow.add_node("dependencies_extractor", dependencies_extractor)
flowchart_workflow.add_node("graph_builder", graph_builder)

flowchart_workflow.add_edge(START, "step_extractor")
flowchart_workflow.add_edge("step_extractor", "dependencies_extractor")
flowchart_workflow.add_edge("dependencies_extractor", "graph_builder")
flowchart_workflow.add_edge("graph_builder", END)

flowchart_graph = flowchart_workflow.compile()
