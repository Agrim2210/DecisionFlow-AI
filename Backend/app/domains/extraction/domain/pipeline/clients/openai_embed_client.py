from __future__ import annotations

import time
from typing import Any

from openai import AsyncOpenAI
from openai import APIStatusError, RateLimitError

from app.domains.extraction.domain.pipeline.clients.base_client import (
    AIResponse,
    BaseAIClient,
    EmbeddingResponse,
)
from app.shared.config import settings


class OpenAIEmbedClient(BaseAIClient):
                                                  

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        max_retries: int = 3,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self._model = model or settings.AI_EMBEDDING_MODEL
        self._dimensions = dimensions or getattr(settings, "AI_EMBEDDING_DIMS", 1536)
        self._max_retries = max_retries
        self._timeout = timeout
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=self._api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = True,
    ) -> AIResponse:
        raise NotImplementedError("OpenAIEmbedClient only supports embeddings")

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        if not texts:
            return EmbeddingResponse(
                embeddings=[],
                model=self._model,
                dimensions=self._dimensions,
            )

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                t0 = time.perf_counter()
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=texts,
                    encoding_format="float",
                )
                latency_ms = (time.perf_counter() - t0) * 1000
                embeddings = [item.embedding for item in response.data]
                if any(len(embedding) != self._dimensions for embedding in embeddings):
                    raise ValueError(
                        f"OpenAI embeddings returned {len(embeddings[0]) if embeddings else 0} dimensions, "
                        f"expected {self._dimensions}"
                    )
                return EmbeddingResponse(
                    embeddings=embeddings,
                    model=self._model,
                    dimensions=len(embeddings[0]) if embeddings else self._dimensions,
                    latency_ms=latency_ms,
                )
            except RateLimitError as e:
                last_err = e
                if attempt == self._max_retries - 1:
                    break
                await self._backoff(attempt)
            except APIStatusError as e:
                last_err = e
                if e.status_code >= 500 and attempt < self._max_retries - 1:
                    await self._backoff(attempt)
                    continue
                break
            except Exception as e:
                last_err = e
                break

        raise RuntimeError(
            f"OpenAI embed failed after {self._max_retries} retries: {last_err}"
        ) from last_err

    @staticmethod
    async def _backoff(attempt: int) -> None:
        import asyncio

        await asyncio.sleep(0.5 * (2 ** attempt))
