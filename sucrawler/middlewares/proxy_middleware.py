from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.downloaders.proxy.proxy_pool import ProxyPool
from sucrawler.downloaders.proxy.proxy_rotator import ProxyRotator


class ProxyMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.proxy_pool_url: str | None = self.config.get("proxy_pool_url")
        self.proxy_list: list[str] = self.config.get("proxy_list", [])
        self.rotate_on_failure: bool = self.config.get("rotate_on_failure", True)

        self.proxy_pool: ProxyPool = ProxyPool()
        self.proxy_rotator: ProxyRotator = ProxyRotator(self.proxy_pool)

        if self.proxy_list:
            for proxy in self.proxy_list:
                self.proxy_pool.add_proxy(proxy)

    async def process_request(self, request: Request) -> Request:
        if request.proxy:
            return request

        proxy = self.proxy_rotator.next()
        if proxy:
            request.proxy = proxy
            logger.debug("Set proxy: {proxy} for {url}", proxy=proxy, url=request.url)
        else:
            logger.warning("No proxy available for {url}", url=request.url)

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if response.status_code >= 400 and request.proxy and self.rotate_on_failure:
            self.proxy_pool.mark_failed(request.proxy)
            logger.info(
                "Marked proxy {proxy} as failed due to status {status_code}",
                proxy=request.proxy,
                status_code=response.status_code,
            )
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        if request.proxy and self.rotate_on_failure:
            self.proxy_pool.mark_failed(request.proxy)
            logger.info(
                "Marked proxy {proxy} as failed due to {exc_type}: {exc_msg}",
                proxy=request.proxy,
                exc_type=type(exception).__name__,
                exc_msg=str(exception),
            )
        return None
