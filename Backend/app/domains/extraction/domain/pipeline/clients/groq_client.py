from __future__ import annotations

import json
import time
from typing import Any

from groq import AsyncGroq

from app.domains.extraction.domain.pipeline.clients.base_client import AIResponse, BaseAIClient, EmbeddingResponse
from app.shared.config import settings


class GroqClient(BaseAIClient):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
    ) -> None:
        self._client = AsyncGroq(api_key=api_key or settings.GROQ_API_KEY)
        self._model = model or settings.AI_EXTRACTION_MODEL
        self._max_retries = max_retries

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = True,
    ) -> AIResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                t0 = time.perf_counter()
                response = await self._client.chat.completions.create(**kwargs)
                latency_ms = (time.perf_counter() - t0) * 1000
                choice = response.choices[0]
                content = choice.message.content or ""
                if json_mode:
                    content = self._ensure_json(content)
                usage = response.usage
                return AIResponse(
                    content=content,
                    model=response.model or self._model,
                    input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    latency_ms=latency_ms,
                    raw={"id": response.id, "finish_reason": choice.finish_reason},
                )
            except Exception as e:
                last_err = e
                if attempt == self._max_retries - 1:
                    break
                await self._backoff(attempt)
        raise RuntimeError(f"Groq complete failed after {self._max_retries} retries: {last_err}") from last_err

    @staticmethod
    def parse_json(content: str) -> dict[str, Any]:
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError:
                                                                      
            trimmed = content.strip()
            if trimmed.startswith("```") and trimmed.endswith("```"):
                trimmed = "\n".join(trimmed.split("\n")[1:-1]).strip()
            return json.loads(trimmed)

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        if not texts:
            return EmbeddingResponse(embeddings=[], input_tokens=0, model=self._model)
        raise NotImplementedError(
            "GroqClient.embed is not implemented; use GeminiEmbedClient for embeddings."
        )

    @staticmethod
    def _ensure_json(content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:] if lines else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        json.loads(content)
        return content

    @staticmethod
    async def _backoff(attempt: int) -> None:
        import asyncio
        await asyncio.sleep(0.5 * (2 ** attempt))