from __future__ import annotations

from datetime import timedelta
from typing import Any

import httpx
from loguru import logger

from sucrawler.common.constants import DEFAULT_TIMEOUT
from sucrawler.common.exceptions import DownloadException
from sucrawler.core.base import BaseDownloaderImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class HttpxDownloader(BaseDownloaderImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.max_connections: int = self.config.get("max_connections", 100)
        self.max_keepalive_connections: int = self.config.get(
            "max_keepalive_connections",
            20,
        )
        self.http2: bool = self.config.get("http2", False)
        self.verify_ssl: bool = self.config.get("verify_ssl", True)
        self.follow_redirects: bool = self.config.get("follow_redirects", True)
        self._client: httpx.AsyncClient | None = None
        self._proxy_clients: dict[str, httpx.AsyncClient] = {}

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            msg = "Client not initialized. Use async context manager or call open() first."
            raise RuntimeError(msg)
        return self._client

    def _build_limits(self) -> httpx.Limits:
        return httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections,
        )

    def _build_timeout(self, timeout: float | None = None) -> httpx.Timeout:
        return httpx.Timeout(timeout if timeout else self.timeout)

    async def open(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                limits=self._build_limits(),
                timeout=self._build_timeout(),
                http2=self.http2,
                verify=self.verify_ssl,
                follow_redirects=self.follow_redirects,
            )
            logger.info("Httpx downloader opened")

    async def _get_proxy_client(self, proxy: str) -> httpx.AsyncClient:
        if proxy not in self._proxy_clients:
            self._proxy_clients[proxy] = httpx.AsyncClient(
                limits=self._build_limits(),
                timeout=self._build_timeout(),
                http2=self.http2,
                verify=self.verify_ssl,
                follow_redirects=self.follow_redirects,
                proxy=proxy,
            )
            logger.debug("Created httpx client for proxy: {proxy}", proxy=proxy)
        return self._proxy_clients[proxy]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

        for proxy, client in self._proxy_clients.items():
            await client.aclose()
            logger.debug("Closed httpx client for proxy: {proxy}", proxy=proxy)
        self._proxy_clients.clear()

        logger.info("Httpx downloader closed")

    async def __aenter__(self) -> HttpxDownloader:
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _do_fetch(self, request: Request) -> Response:
        if self._client is None:
            await self.open()

        timeout = self._build_timeout(
            request.timeout if request.timeout else DEFAULT_TIMEOUT,
        )

        client = self.client
        if request.proxy:
            client = await self._get_proxy_client(request.proxy)

        try:
            is_bytes_or_str = isinstance(request.data, (bytes, str))
            json_data = (
                None
                if is_bytes_or_str or request.data is None
                else request.data
            )
            httpx_response = await client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                content=request.data if is_bytes_or_str else None,
                json=json_data,
                timeout=timeout,
            )
        except httpx.HTTPError as e:
            msg = f"HTTP error fetching {request.url}: {e!s}"
            raise DownloadException(msg) from e

        elapsed = timedelta(seconds=httpx_response.elapsed.total_seconds())

        return Response(
            request=request,
            status_code=httpx_response.status_code,
            text=httpx_response.text,
            content=httpx_response.content,
            headers=dict(httpx_response.headers),
            elapsed=elapsed,
        )
