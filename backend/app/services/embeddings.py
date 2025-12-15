import json
import math
from typing import Iterable, List, Sequence

import httpx

from app.core.config import settings


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str | None = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/embeddings"

    async def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        payload = {"input": list(texts), "model": self.model}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            r = await client.post(self.base_url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            data = r.json()
        return [d["embedding"] for d in data["data"]]


def simple_cluster(embeddings: List[List[float]], similarity_threshold: float = 0.85) -> List[int]:
    if not embeddings:
        return []

    centroids: List[List[float]] = []
    labels: List[int] = []

    for vec in embeddings:
        if not centroids:
            centroids.append(vec)
            labels.append(0)
            continue

        best_idx = -1
        best_sim = -1.0
        for idx, c in enumerate(centroids):
            sim = _cosine_similarity(vec, c)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        if best_sim >= similarity_threshold:
            labels.append(best_idx)
        else:
            centroids.append(vec)
            labels.append(len(centroids) - 1)

    return labels


def embedding_to_json(vec: Sequence[float]) -> str:
    return json.dumps(list(vec))


def embedding_from_json(s: str) -> List[float]:
    return [float(x) for x in json.loads(s)]
