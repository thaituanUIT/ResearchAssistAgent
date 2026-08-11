import os
from functools import lru_cache

import dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

MODEL_ENV_BY_ROLE = {
    "default": "OPENROUTER_DEFAULT_MODEL",
    "fast": "OPENROUTER_FAST_MODEL",
    "reasoning": "OPENROUTER_REASONING_MODEL",
    "structured": "OPENROUTER_STRUCTURED_MODEL",
}

DEFAULT_MODELS = {
    "default": "openai/gpt-4o-mini",
    "fast": "openai/gpt-4o-mini",
    "reasoning": "openai/gpt-4o",
    "structured": "openai/gpt-4o-mini",
}


def get_model_name(role: str = "default") -> str:
    env_name = MODEL_ENV_BY_ROLE.get(role, MODEL_ENV_BY_ROLE["default"])
    return os.environ.get(env_name) or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODELS.get(role, DEFAULT_MODELS["default"])


@lru_cache(maxsize=16)
def get_llm(role: str = "default", temperature: float = 0.1) -> ChatOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    default_headers = {
        "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost:5173"),
        "X-OpenRouter-Title": os.environ.get("OPENROUTER_APP_TITLE", "ResearchAssist"),
    }

    return ChatOpenAI(
        model=get_model_name(role),
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers=default_headers,
    )
