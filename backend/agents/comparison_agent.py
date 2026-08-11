from langchain_core.prompts import ChatPromptTemplate

from backend.graph.state import ResearchState
from backend.core.llm import get_llm


def paper_comparison_agent(state: ResearchState) -> dict:
    llm = get_llm("reasoning", temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Paper Comparison Agent. Compare the retrieved "
            "papers or document sections across problem, method, data, evaluation, "
            "findings, limitations, and practical implications. If there is only one "
            "paper in context, explain that a real comparison needs another paper.\n\n"
            "Context:\n{context}",
        ),
        ("human", "{user_prompt}"),
    ])
    response = (prompt | llm).invoke({
        "context": state.get("retrieved_context", ""),
        "user_prompt": state.get("user_prompt", ""),
    })

    return {
        "agent_draft": response.content,
        "active_agents": state.get("active_agents", []) + ["paper_comparison"],
    }
