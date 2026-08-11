import os
from typing import List

import dotenv
import requests
from langchain_core.embeddings import Embeddings

dotenv.load_dotenv()


class OpenRouterEmbeddings(Embeddings):
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        self.model = os.environ.get("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small")
        self.dimensions = int(os.environ.get("OPENROUTER_EMBEDDING_DIMENSIONS", "384"))

        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        response = requests.post(
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost:5173"),
                "X-OpenRouter-Title": os.environ.get("OPENROUTER_APP_TITLE", "ResearchAssist"),
            },
            json={
                "model": self.model,
                "input": texts,
                "dimensions": self.dimensions,
                "encoding_format": "float",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload.get("data", [])]
