from typing import Any, Dict, List, TypedDict


class ResearchState(TypedDict, total=False):
    user_prompt: str
    chat_history: List[Dict[str, str]]
    user_id: str
    session_id: str

    intent: str
    active_agents: List[str]

    retrieved_context: str
    search_results: str
    search_evaluation: str
    agent_draft: str
    critique: str
    chat_response: str

    paper_metadata: List[dict]
    errors: List[str]
    debug: Dict[str, Any]
