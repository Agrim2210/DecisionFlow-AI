from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

import structlog

from app.shared.events.event_types import DomainEvent

logger = structlog.get_logger(__name__)

Handler = Callable[[DomainEvent], Awaitable[None]]


class EventConsumer:

    def __init__(self, redis_url: str, group: str, consumer: str) -> None:
        self._redis_url = redis_url
        self._group = group
        self._consumer = consumer
        self._client = None
        self._handlers: dict[str, list[Handler]] = {}
        self._running = False

    async def connect(self) -> None:
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(self._redis_url, decode_responses=True)

    async def disconnect(self) -> None:
        self._running = False
        if self._client:
            await self._client.aclose()

    def register(self, event_type: str, handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def ensure_groups(self, streams: list[str]) -> None:
        for stream in streams:
            try:
                await self._client.xgroup_create(stream, self._group, id="0", mkstream=True)
            except Exception:
                pass

    async def start(self, streams: list[str], poll_ms: int = 1000) -> None:
        if not self._client:
            await self.connect()
        await self.ensure_groups(streams)
        self._running = True
        stream_keys = {s: ">" for s in streams}

        while self._running:
            try:
                results = await self._client.xreadgroup(
                    groupname=self._group,
                    consumername=self._consumer,
                    streams=stream_keys,
                    count=10,
                    block=poll_ms,
                )
                if not results:
                    continue

                for stream, messages in results:
                    for msg_id, data in messages:
                        await self._dispatch(stream, msg_id, data)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("consumer_poll_failed", error=str(exc))
                await asyncio.sleep(2)

    async def _dispatch(self, stream: str, msg_id: str, data: dict[str, Any]) -> None:
        try:
            event = DomainEvent.from_dict(data)
        except Exception as exc:
            logger.warning("event_parse_failed", msg_id=msg_id, error=str(exc))
            await self._ack(stream, msg_id)
            return

        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            await self._ack(stream, msg_id)
            return

        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                logger.error(
                    "handler_failed",
                    event_type=event.event_type,
                    handler=handler.__name__,
                    error=str(exc),
                )

        await self._ack(stream, msg_id)

    async def _ack(self, stream: str, msg_id: str) -> None:
        try:
            await self._client.xack(stream, self._group, msg_id)
        except Exception as exc:
            logger.warning("ack_failed", msg_id=msg_id, error=str(exc))
