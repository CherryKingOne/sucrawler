from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request


class BiliCookieMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.cookie_pool: list[str] = list(self.config.get("cookie_pool", []))
        self._current_index = 0

    async def before_request(self, request: Request) -> Request:
        if self.cookie_pool:
            cookie = self.cookie_pool[self._current_index % len(self.cookie_pool)]
            if cookie:
                request.headers["Cookie"] = cookie
                logger.debug(f"Using cookie #{self._current_index}")
        return request

    async def after_request(self, request: Request, response: Any) -> Any:
        return response
