from langchain_core.prompts import ChatPromptTemplate

from backend.graph.state import ResearchState
from backend.core.llm import get_llm


def critic_agent(state: ResearchState) -> dict:
    draft = state.get("agent_draft") or state.get("search_results", "")
    if not draft or draft.startswith("**Error"):
        return {
            "critique": "",
            "active_agents": state.get("active_agents", []) + ["critic"],
        }

    llm = get_llm("fast", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Critic Agent. Review the draft for grounding, "
            "clarity, and overclaiming. Return 1-2 concise sentences. Do not rewrite "
            "the answer.",
        ),
        (
            "human",
            "User request:\n{user_prompt}\n\nRetrieved context:\n{context}\n\nDraft:\n{draft}",
        ),
    ])
    try:
        response = (prompt | llm).invoke({
            "user_prompt": state.get("user_prompt", ""),
            "context": state.get("retrieved_context", ""),
            "draft": draft,
        })
        critique = response.content.strip()
    except Exception:
        critique = ""

    return {
        "critique": critique,
        "active_agents": state.get("active_agents", []) + ["critic"],
    }


def scholar_evaluator_agent(state: ResearchState) -> dict:
    search_results = state.get("search_results", "")
    if not search_results or search_results.startswith("**Error"):
        return {
            "agent_draft": search_results or "No results generated.",
            "active_agents": state.get("active_agents", []) + ["scholar_evaluator"],
        }

    llm = get_llm("fast", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Search Evaluator. Assess the clarity, relevance, "
            "and reliability of the Google Scholar snippets in 1-2 sentences.",
        ),
        ("human", "User query: {user_prompt}\n\nSearch results:\n{search_results}"),
    ])
    try:
        response = (prompt | llm).invoke({
            "user_prompt": state.get("user_prompt", ""),
            "search_results": search_results,
        })
        evaluation = response.content.strip()
    except Exception:
        evaluation = "These results should be checked against the full papers before relying on them."

    return {
        "search_evaluation": evaluation,
        "agent_draft": f"### Search Analysis\n**{evaluation}**\n\n---\n\n{search_results}",
        "active_agents": state.get("active_agents", []) + ["scholar_evaluator"],
    }
