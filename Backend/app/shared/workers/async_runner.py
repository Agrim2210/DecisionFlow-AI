                                                         
from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

ResultT = TypeVar("ResultT")
_loops = threading.local()


def run_async(coro: Coroutine[Any, Any, ResultT]) -> ResultT:
       
    loop: asyncio.AbstractEventLoop | None = getattr(_loops, "event_loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _loops.event_loop = loop
    return loop.run_until_complete(coro)
