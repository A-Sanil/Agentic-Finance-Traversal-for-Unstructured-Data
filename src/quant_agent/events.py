from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Any

# Simple in-process pub/sub for streaming citations during traversal.
_queue: "asyncio.Queue[dict]" = asyncio.Queue()


async def publish(event: dict[str, Any]) -> None:
    """Publish an event (a citation or progress update).

    Events are small dicts that will be JSON-serialized by the HTTP streamer.
    """
    await _queue.put(event)


async def subscribe() -> AsyncIterator[dict[str, Any]]:
    """Async iterator yielding published events.

    This yields events as they arrive. Caller is expected to break when done.
    """
    while True:
        event = await _queue.get()
        yield event
