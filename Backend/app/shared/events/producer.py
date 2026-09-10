from __future__ import annotations

import json
import uuid
from typing import Any

import structlog

from app.shared.events.event_types import DomainEvent, Stream

logger = structlog.get_logger(__name__)


class EventProducer:

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client = None

    async def connect(self) -> None:
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(self._redis_url, decode_responses=True)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    async def publish(self, stream: str, event: DomainEvent) -> str | None:
        if not self._client:
            logger.warning("producer_not_connected", event_type=event.event_type)
            return None
        try:
            msg_id = await self._client.xadd(stream, event.to_dict())
            logger.debug("event_published", stream=stream, event_type=event.event_type, msg_id=msg_id)
            return msg_id
        except Exception as exc:
            logger.error("event_publish_failed", stream=stream, event_type=event.event_type, error=str(exc))
            return None

    async def publish_raw(
        self,
        stream: str,
        event_type: str,
        org_id: uuid.UUID,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> str | None:
        event = DomainEvent.create(
            event_type=event_type,
            org_id=org_id,
            payload=payload,
            correlation_id=correlation_id,
        )
        return await self.publish(stream, event)


_producer: EventProducer | None = None


def get_producer() -> EventProducer:
    global _producer
    if _producer is None:
        from app.shared.config import settings
        _producer = EventProducer(settings.REDIS_URL)
    return _producer
