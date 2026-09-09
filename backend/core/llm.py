import os
from functools import lru_cache
from typing import Any

import dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter").strip().lower()

OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

LOCAL_LLM_BASE_URL = os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001/v1")

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

LOCAL_MODEL_ENV_BY_ROLE = {
    "default": "LOCAL_LLM_DEFAULT_MODEL",
    "fast": "LOCAL_LLM_FAST_MODEL",
    "reasoning": "LOCAL_LLM_REASONING_MODEL",
    "structured": "LOCAL_LLM_STRUCTURED_MODEL",
}

LOCAL_DEFAULT_MODELS = {
    "default": "researchassist-soup",
    "fast": "researchassist-soup",
    "reasoning": "researchassist-soup",
    "structured": "researchassist-soup",
}


def get_model_name(role: str = "default") -> str:
    if LLM_PROVIDER == "local":
        env_name = LOCAL_MODEL_ENV_BY_ROLE.get(role, LOCAL_MODEL_ENV_BY_ROLE["default"])
        return os.environ.get(env_name) or os.environ.get("LOCAL_LLM_MODEL") or LOCAL_DEFAULT_MODELS.get(role, LOCAL_DEFAULT_MODELS["default"])

    env_name = MODEL_ENV_BY_ROLE.get(role, MODEL_ENV_BY_ROLE["default"])
    return os.environ.get(env_name) or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODELS.get(role, DEFAULT_MODELS["default"])


@lru_cache(maxsize=16)
def get_llm(role: str = "default", temperature: float = 0.1) -> ChatOpenAI:
    if LLM_PROVIDER == "local":
        return ChatOpenAI(
            model=get_model_name(role),
            api_key=os.environ.get("LOCAL_LLM_API_KEY", "local-not-needed"),
            base_url=LOCAL_LLM_BASE_URL,
            temperature=temperature,
        )

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


def get_llm_runtime_config(role: str = "default") -> dict[str, Any]:
    """Return non-secret model settings for UI/status diagnostics."""
    if LLM_PROVIDER == "local":
        return {
            "provider": "local",
            "model": get_model_name(role),
            "base_url": LOCAL_LLM_BASE_URL,
            "openai_compatible": True,
        }

    return {
        "provider": "openrouter",
        "model": get_model_name(role),
        "base_url": OPENROUTER_BASE_URL,
        "openai_compatible": True,
    }
