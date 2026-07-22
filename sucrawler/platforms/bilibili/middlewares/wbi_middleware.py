from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request


class BiliWbiMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._wbi_keys: tuple[str, str] | None = None

    async def before_request(self, request: Request) -> Request:
        logger.debug("WBI middleware - request passed through")
        return request

    async def after_request(self, request: Request, response: Any) -> Any:
        return response
