from langchain_core.prompts import ChatPromptTemplate

from backend.graph.flowchart_workflow import flowchart_graph
from backend.graph.state import ResearchState
from backend.core.llm import get_llm


def flowchart_agent(state: ResearchState) -> dict:
    context = state.get("retrieved_context", "")
    user_prompt = state.get("user_prompt", "")

    if not context:
        return {
            "agent_draft": "I need uploaded or retrieved paper context before I can generate a useful flowchart.",
            "active_agents": state.get("active_agents", []) + ["flowchart"],
        }

    mermaid = flowchart_graph.invoke({"instruction": user_prompt, "context": context}).get("mermaid_graph", "")
    return {
        "agent_draft": mermaid,
        "active_agents": state.get("active_agents", []) + ["flowchart"],
    }


def summary_agent(state: ResearchState) -> dict:
    llm = get_llm("default", temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Summary Agent. Summarize the retrieved paper "
            "context into a concise research-useful summary with methods, findings, "
            "limitations, and notable terms when available.\n\nContext:\n{context}",
        ),
        ("human", "{user_prompt}"),
    ])
    response = (prompt | llm).invoke({
        "context": state.get("retrieved_context", ""),
        "user_prompt": state.get("user_prompt", ""),
    })
    return {
        "agent_draft": response.content,
        "active_agents": state.get("active_agents", []) + ["summary"],
    }
