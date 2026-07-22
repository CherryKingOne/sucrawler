from __future__ import annotations

import re
from typing import Any, Awaitable, Callable, Optional

from loguru import logger


class NetworkInterceptor:
    def __init__(self, page_or_context: Any) -> None:
        self._target = page_or_context
        self._handlers: list[Callable[[Any], Awaitable[None]]] = []
        self._request_handlers: list[Callable[[Any], Awaitable[Optional[bool]]]] = []
        self._response_handlers: list[Callable[[Any], Awaitable[None]]] = []
        self._url_patterns: list[re.Pattern] = []
        self._active: bool = False

    @property
    def active(self) -> bool:
        return self._active

    def add_url_filter(self, pattern: str) -> None:
        compiled = re.compile(pattern)
        self._url_patterns.append(compiled)
        logger.debug(f"[NetworkInterceptor] Added URL filter: {pattern}")

    def on_request(self, handler: Callable[[Any], Awaitable[Optional[bool]]]) -> None:
        self._request_handlers.append(handler)

    def on_response(self, handler: Callable[[Any], Awaitable[None]]) -> None:
        self._response_handlers.append(handler)

    async def start(self) -> None:
        if self._active:
            return

        self._target.on("request", self._on_request)
        self._target.on("response", self._on_response)
        self._active = True
        logger.info("[NetworkInterceptor] Started")

    async def stop(self) -> None:
        if not self._active:
            return

        try:
            self._target.remove_listener("request", self._on_request)
            self._target.remove_listener("response", self._on_response)
        except Exception:
            pass

        self._active = False
        logger.info("[NetworkInterceptor] Stopped")

    async def _on_request(self, request: Any) -> None:
        url = request.url
        if not self._matches_url(url):
            return

        for handler in self._request_handlers:
            try:
                result = await handler(request)
                if result is False:
                    await request.abort()
                    return
            except Exception as e:
                logger.warning(f"[NetworkInterceptor] Request handler error: {e}")

        try:
            await request.continue_()
        except Exception:
            pass

    async def _on_response(self, response: Any) -> None:
        url = response.url
        if not self._matches_url(url):
            return

        for handler in self._response_handlers:
            try:
                await handler(response)
            except Exception as e:
                logger.warning(f"[NetworkInterceptor] Response handler error: {e}")

    def _matches_url(self, url: str) -> bool:
        if not self._url_patterns:
            return True
        return any(pattern.search(url) for pattern in self._url_patterns)

    async def __aenter__(self) -> "NetworkInterceptor":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()
