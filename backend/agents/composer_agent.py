from backend.graph.state import ResearchState


def response_composer_agent(state: ResearchState) -> dict:
    draft = state.get("agent_draft") or state.get("search_results") or ""
    critique = state.get("critique", "").strip()
    active_agents = state.get("active_agents", []) + ["composer"]

    if critique and not draft.startswith("### Search Analysis"):
        response = f"{draft}\n\n---\n\n**Agent Check:** {critique}"
    else:
        response = draft

    return {
        "chat_response": response,
        "active_agents": active_agents,
    }
