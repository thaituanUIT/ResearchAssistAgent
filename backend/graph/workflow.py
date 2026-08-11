from langgraph.graph import END, START, StateGraph

from backend.agents.comparison_agent import paper_comparison_agent
from backend.agents.composer_agent import response_composer_agent
from backend.agents.critic_agent import critic_agent, scholar_evaluator_agent
from backend.agents.flowchart_agent import flowchart_agent, summary_agent
from backend.agents.rag_agent import document_rag_agent, retrieve_context_agent
from backend.agents.scholar_agent import scholar_search_agent
from backend.agents.supervisor import supervisor_agent
from backend.graph.state import ResearchState


def route_from_supervisor(state: ResearchState) -> str:
    return state.get("intent", "document_rag")


workflow = StateGraph(ResearchState)

workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("retrieve_context", retrieve_context_agent)
workflow.add_node("document_rag", document_rag_agent)
workflow.add_node("scholar_search", scholar_search_agent)
workflow.add_node("scholar_evaluator", scholar_evaluator_agent)
workflow.add_node("paper_comparison", paper_comparison_agent)
workflow.add_node("flowchart", flowchart_agent)
workflow.add_node("summary", summary_agent)
workflow.add_node("critic", critic_agent)
workflow.add_node("composer", response_composer_agent)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "document_rag": "retrieve_context",
        "paper_comparison": "retrieve_context",
        "flowchart": "retrieve_context",
        "summary": "retrieve_context",
        "scholar_search": "scholar_search",
    },
)

workflow.add_conditional_edges(
    "retrieve_context",
    route_from_supervisor,
    {
        "document_rag": "document_rag",
        "paper_comparison": "paper_comparison",
        "flowchart": "flowchart",
        "summary": "summary",
        "scholar_search": "scholar_search",
    },
)

workflow.add_edge("scholar_search", "scholar_evaluator")
workflow.add_edge("scholar_evaluator", "composer")

workflow.add_edge("document_rag", "critic")
workflow.add_edge("paper_comparison", "critic")
workflow.add_edge("flowchart", "critic")
workflow.add_edge("summary", "critic")
workflow.add_edge("critic", "composer")
workflow.add_edge("composer", END)

app_graph = workflow.compile()
