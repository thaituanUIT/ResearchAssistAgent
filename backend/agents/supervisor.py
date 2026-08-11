from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from backend.graph.state import ResearchState
from backend.core.llm import get_llm


class RouteDecision(BaseModel):
    intent: str = Field(
        description=(
            "One of: document_rag, scholar_search, paper_comparison, "
            "flowchart, summary."
        )
    )


def supervisor_agent(state: ResearchState) -> dict:
    user_prompt = state.get("user_prompt", "")
    llm = get_llm("structured", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are the supervisor for a multi-agent research assistant. "
            "Route the user request to exactly one intent:\n"
            "- document_rag: questions about uploaded documents or general research chat\n"
            "- scholar_search: finding new external academic papers\n"
            "- paper_comparison: compare uploaded papers, methods, claims, results, or limitations\n"
            "- flowchart: diagram, Mermaid, process map, architecture map, concept map\n"
            "- summary: summarize uploaded papers or previous context\n"
            "Return only structured output.",
        ),
        ("human", "{user_prompt}"),
    ])

    try:
        decision = (prompt | llm.with_structured_output(RouteDecision)).invoke({"user_prompt": user_prompt})
        intent = decision.intent.strip().lower()
    except Exception:
        text = user_prompt.lower()
        if any(word in text for word in ["google scholar", "find papers", "search papers", "recent papers", "new papers"]):
            intent = "scholar_search"
        elif any(word in text for word in ["flowchart", "diagram", "mermaid", "visual map", "concept map"]):
            intent = "flowchart"
        elif any(word in text for word in ["compare", "versus", "vs.", "differences", "similarities"]):
            intent = "paper_comparison"
        elif any(word in text for word in ["summarize", "summary", "tl;dr"]):
            intent = "summary"
        else:
            intent = "document_rag"

    if intent not in {"document_rag", "scholar_search", "paper_comparison", "flowchart", "summary"}:
        intent = "document_rag"

    return {
        "intent": intent,
        "active_agents": ["supervisor"],
    }
