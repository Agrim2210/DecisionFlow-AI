from __future__ import annotations

import asyncio
import structlog
from app.shared.config import settings

logger = structlog.get_logger(__name__)

_BATCH_SIZE = 100
_MAX_RETRIES = 3
_RETRY_DELAYS = [2, 5, 10]


class OpenAIEmbedAdapter:

    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self._model = settings.AI_EMBEDDING_MODEL
        except ImportError:
            raise RuntimeError("openai package not installed")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i: i + _BATCH_SIZE]
            embeddings = await self._embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        from openai import RateLimitError, APIStatusError

        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=texts,
                    encoding_format="float",
                )
                logger.debug(
                    "embeddings_generated",
                    count=len(texts),
                    tokens=response.usage.total_tokens if response.usage else 0,
                )
                return [item.embedding for item in response.data]

            except RateLimitError:
                if attempt == _MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(_RETRY_DELAYS[attempt])

            except APIStatusError as exc:
                if exc.status_code >= 500 and attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                else:
                    raise

        raise RuntimeError("OpenAI embed: max retries exceeded")
