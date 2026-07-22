from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable
from typing import Any

REQUEST_SENT = "request_sent"
RESPONSE_RECEIVED = "response_received"
ITEM_SCRAPED = "item_scraped"
ERROR_OCCURRED = "error_occurred"
TASK_STARTED = "task_started"
TASK_FINISHED = "task_finished"
SPIDER_OPENED = "spider_opened"
SPIDER_CLOSED = "spider_closed"
ITEM_DROPPED = "item_dropped"


EventHandler = Callable[[dict[str, Any]], Any | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        self._handlers[event].append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        if event in self._handlers and handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        event_data = data or {}
        for handler in self._handlers.get(event, []):
            if asyncio.iscoroutinefunction(handler):
                msg = "Async handler cannot be used with sync emit, use emit_async instead"
                raise TypeError(msg)
            handler(event_data)

    async def emit_async(self, event: str, data: dict[str, Any] | None = None) -> None:
        event_data = data or {}
        for handler in self._handlers.get(event, []):
            result = handler(event_data)
            if asyncio.iscoroutine(result):
                await result
