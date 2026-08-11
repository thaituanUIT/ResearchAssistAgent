from langchain_core.prompts import ChatPromptTemplate

from backend.graph.state import ResearchState
from backend.core.llm import get_llm
from backend.services.vector_store import retrieve_relevant_context


def _format_history(chat_history: list[dict]) -> str:
    lines = []
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        lines.append(f"{role.capitalize()}: {content}")
    return "\n".join(lines)


def retrieve_context_agent(state: ResearchState) -> dict:
    user_prompt = state.get("user_prompt", "")
    user_id = state.get("user_id", "")
    filter_dict = {"user_id": {"$eq": user_id}} if user_id else None
    context = retrieve_relevant_context(user_prompt, k=8, filter_dict=filter_dict)

    return {
        "retrieved_context": context,
        "active_agents": state.get("active_agents", []) + ["retriever"],
    }


def document_rag_agent(state: ResearchState) -> dict:
    llm = get_llm("default", temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Document RAG Agent. Answer using the retrieved "
            "document and memory context when it is relevant. If the context is weak, "
            "say what is missing instead of inventing details.\n\n"
            "Retrieved context:\n{retrieved_context}\n\n"
            "Chat history:\n{history_text}",
        ),
        ("human", "{user_prompt}"),
    ])

    response = (prompt | llm).invoke({
        "retrieved_context": state.get("retrieved_context", ""),
        "history_text": _format_history(state.get("chat_history", [])),
        "user_prompt": state.get("user_prompt", ""),
    })

    return {
        "agent_draft": response.content,
        "active_agents": state.get("active_agents", []) + ["document_rag"],
    }
