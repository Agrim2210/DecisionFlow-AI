from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.domains.extraction.domain.pipeline.clients.base_client import (
    AIResponse,
    BaseAIClient,
    EmbeddingResponse,
)
from app.shared.config import settings


class GeminiEmbedClient(BaseAIClient):
                                                               

    BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        max_retries: int = 3,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "GOOGLE_API_KEY", "")
        self._model = model or getattr(settings, "AI_EMBEDDING_MODEL", "gemini-embedding-001")
        self._dimensions = dimensions or getattr(settings, "AI_EMBEDDING_DIMS", 1536)
        self._max_retries = max_retries
        self._timeout = timeout

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = True,
    ) -> AIResponse:
        raise NotImplementedError("GeminiEmbedClient only supports embeddings")

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        if not texts:
            return EmbeddingResponse(
                embeddings=[],
                model=self._model,
                dimensions=self._dimensions,
            )
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                t0 = time.perf_counter()
                embeddings = await self._batch_embed(texts)
                latency_ms = (time.perf_counter() - t0) * 1000
                if any(len(embedding) != self._dimensions for embedding in embeddings):
                    raise ValueError(
                        f"Gemini embeddings returned {len(embeddings[0]) if embeddings else 0} dimensions, "
                        f"expected {self._dimensions}"
                    )
                return EmbeddingResponse(
                    embeddings=embeddings,
                    model=self._model,
                    dimensions=len(embeddings[0]) if embeddings else self._dimensions,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                last_err = e
                if attempt == self._max_retries - 1:
                    break
                await asyncio.sleep(0.5 * (2**attempt))
        raise RuntimeError(
            f"Gemini embed failed after {self._max_retries} retries: {last_err}"
        ) from last_err

    async def _batch_embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.BASE}/models/{self._model}:batchEmbedContents"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }
        requests = []
        for text in texts:
            req: dict[str, Any] = {
                "model": f"models/{self._model}",
                "content": {"parts": [{"text": text}]},
                "taskType": "RETRIEVAL_DOCUMENT",
            }
            if self._dimensions and self._dimensions != 3072:
                req["outputDimensionality"] = self._dimensions
            requests.append(req)

        payload = {"requests": requests}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                                                    
                if r.status_code in (404, 400):
                    return await self._embed_one_by_one(texts)
                r.raise_for_status()
            data = r.json()

        embeddings: list[list[float]] = []
        for item in data.get("embeddings", []):
            values = item.get("values") or item.get("embedding", {}).get("values")
            if values is None:
                raise ValueError(f"Unexpected Gemini batch item: {item.keys()}")
            embeddings.append(self._maybe_normalize(values))
        if len(embeddings) != len(texts):
            raise ValueError(
                f"Gemini returned {len(embeddings)} embeddings for {len(texts)} texts"
            )
        return embeddings

    async def _embed_one_by_one(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.BASE}/models/{self._model}:embedContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }
        out: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for text in texts:
                body: dict[str, Any] = {
                    "content": {"parts": [{"text": text}]},
                    "taskType": "RETRIEVAL_DOCUMENT",
                }
                if self._dimensions and self._dimensions != 3072:
                    body["outputDimensionality"] = self._dimensions
                r = await client.post(url, headers=headers, json=body)
                r.raise_for_status()
                data = r.json()
                emb = data.get("embedding", {})
                values = emb.get("values") if isinstance(emb, dict) else None
                if values is None:
                    raise ValueError(f"Unexpected Gemini embed response: {list(data.keys())}")
                out.append(self._maybe_normalize(values))
        return out

    def _maybe_normalize(self, values: list[float]) -> list[float]:
                                                                                  
        if self._dimensions == 3072:
            return values
        norm = sum(v * v for v in values) ** 0.5
        if norm == 0:
            return values
        return [v / norm for v in values]
