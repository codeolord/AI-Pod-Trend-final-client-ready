from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


class AIError(RuntimeError):
    pass


@dataclass
class TrendAIOutput:
    score_0_100: int
    niche: str
    keywords: list[str]
    design_prompts: list[str]
    reasoning: str


class OpenAIResponsesClient:
    """Thin wrapper around the OpenAI Responses API.

    Uses the public HTTP API (no SDK) so deploys are predictable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: Optional[int] = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model or settings.openai_model
        self.timeout_s = timeout_s or settings.openai_timeout_s

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise AIError("OPENAI_API_KEY is not set")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def json_response(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Ask for a JSON object that matches `json_schema`.

        We use `text.format` = json_schema (Structured Outputs) on the Responses API.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "text": {"format": {"type": "json_schema", "json_schema": json_schema}},
        }

        # Reasoning config is optional; only honored by some models.
        if settings.openai_reasoning:
            payload["reasoning"] = {"effort": settings.openai_reasoning}

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(f"{self.base_url}/responses", headers=self._headers(), json=payload)
            if r.status_code >= 400:
                raise AIError(f"OpenAI error {r.status_code}: {r.text}")
            data = r.json()

        # The Responses API returns content items; `output_text` is easiest when present.
        # Fall back to scanning output.
        text = data.get("output_text")
        if not text:
            parts: list[str] = []
            for item in data.get("output", []) or []:
                for c in item.get("content", []) or []:
                    if c.get("type") in ("output_text", "text") and c.get("text"):
                        parts.append(c["text"])
            text = "\n".join(parts).strip()

        if not text:
            raise AIError("OpenAI returned no text output")

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise AIError(f"Failed to parse JSON from model output: {e}; output={text[:500]!r}")


TREND_SCHEMA: Dict[str, Any] = {
    "name": "trend_score",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score_0_100": {"type": "integer", "minimum": 0, "maximum": 100},
            "niche": {"type": "string", "minLength": 2},
            "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 12},
            "design_prompts": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
            "reasoning": {"type": "string", "minLength": 10},
        },
        "required": ["score_0_100", "niche", "keywords", "design_prompts", "reasoning"],
    },
}


async def score_trend_item_with_ai(
    *,
    title: str,
    summary: str,
    source: str,
    url: str,
    client: Optional[OpenAIResponsesClient] = None,
) -> TrendAIOutput:
    c = client or OpenAIResponsesClient()
    system = (
        "You are a product strategist for a print-on-demand (POD) business. "
        "Given a trend/news item, score its POD potential and propose design prompts. "
        "Be concrete, avoid vague advice, and focus on sellable niches." 
    )
    user = (
        f"SOURCE: {source}\nTITLE: {title}\nURL: {url}\nSUMMARY: {summary}\n\n"
        "Return JSON for: score_0_100 (0-100), niche (short), keywords (3-12), "
        "design_prompts (2-6, each a strong stable-diffusion prompt for a POD graphic), reasoning (1-3 sentences)."
    )
    obj = await c.json_response(system=system, user=user, json_schema=TREND_SCHEMA)
    return TrendAIOutput(
        score_0_100=int(obj["score_0_100"]),
        niche=str(obj["niche"]),
        keywords=[str(x) for x in obj.get("keywords", [])],
        design_prompts=[str(x) for x in obj.get("design_prompts", [])],
        reasoning=str(obj["reasoning"]),
    )
