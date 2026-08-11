from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from backend.graph.state import ResearchState
from backend.core.llm import get_llm
from backend.services.tools import search_scholar_api


class SearchCriteria(BaseModel):
    query: str = Field(description="The exact Google Scholar search query.")
    scisbd: str = Field(description="Use '1' for most recent/date sort, otherwise '0'.")
    num_results: int = Field(description="Number of results to retrieve. Default 5.")


def scholar_search_agent(state: ResearchState) -> dict:
    user_prompt = state.get("user_prompt", "")
    llm = get_llm("structured", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are ResearchAssist's Scholar Search Agent. Extract precise Google "
            "Scholar search parameters from the user's request.",
        ),
        ("human", "{user_prompt}"),
    ])

    try:
        criteria = (prompt | llm.with_structured_output(SearchCriteria)).invoke({"user_prompt": user_prompt})
        results = search_scholar_api(criteria.query, criteria.scisbd, criteria.num_results or 5)
    except Exception as exc:
        results = f"**Error parsing search criteria or calling API:** {exc}"

    return {
        "search_results": results,
        "active_agents": state.get("active_agents", []) + ["scholar_search"],
    }
