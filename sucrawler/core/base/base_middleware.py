from __future__ import annotations

from typing import Any

from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class BaseMiddlewareImpl(BaseMiddleware):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def process_request(self, request: Request) -> Request:
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        return None
