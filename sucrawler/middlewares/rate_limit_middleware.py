from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class RateLimitMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.requests_per_second: float = self.config.get("requests_per_second", 10.0)
        self.burst: int = self.config.get("burst", 20)
        self._tokens: float = float(self.burst)
        self._last_refill_time: float = time.monotonic()
        self._lock: asyncio.Lock | None = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def process_request(self, request: Request) -> Request:
        await self._acquire()
        logger.debug("Rate limit passed for {url}", url=request.url)
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        return None

    async def _acquire(self) -> None:
        async with self.lock:
            self._refill_tokens()
            while self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self.requests_per_second
                logger.debug(
                    "Rate limit reached, waiting {wait_time:.4f}s",
                    wait_time=wait_time,
                )
                await asyncio.sleep(wait_time)
                self._refill_tokens()
            self._tokens -= 1.0

    def _refill_tokens(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill_time
        if elapsed > 0:
            new_tokens = elapsed * self.requests_per_second
            self._tokens = min(self.burst, self._tokens + new_tokens)
            self._last_refill_time = now
