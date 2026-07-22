from __future__ import annotations

import random
from typing import Any

from loguru import logger

from sucrawler.common.constants import DEFAULT_USER_AGENTS
from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class UserAgentMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.user_agents: list[str] = self.config.get("user_agents", DEFAULT_USER_AGENTS)
        self.rotate: bool = self.config.get("rotate", True)
        self._default_ua: str = self.user_agents[0] if self.user_agents else ""

    async def process_request(self, request: Request) -> Request:
        if "User-Agent" in request.headers and not self.rotate:
            return request

        if self.rotate and self.user_agents:
            ua = random.choice(self.user_agents)
        else:
            ua = self._default_ua

        request.headers["User-Agent"] = ua
        logger.debug("Set User-Agent: {ua} for {url}", ua=ua, url=request.url)
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        return None
