from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.platforms.xiaohongshu.utils.sign import xhs_sign


class XHSSignMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.sign_key: str = self.config.get("sign_key", "")
        self.sign_algorithm: str = self.config.get("sign_algorithm", "md5")

    async def process_request(self, request: Request) -> Request:
        if not self.sign_key:
            return request

        logger.debug(f"Signing request to {request.url}")

        params = dict(request.params) if request.params else {}
        sign = xhs_sign(params, self.sign_key)
        request.params["sign"] = sign

        return request

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Response:
        return response

    async def process_exception(
        self,
        request: Request,
        exception: Exception,
    ) -> None:
        logger.error(f"Sign middleware exception for {request.url}: {exception}")
