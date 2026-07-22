from __future__ import annotations

import time
from datetime import timedelta
from typing import Any

import aiohttp
from loguru import logger

from sucrawler.common.constants import DEFAULT_TIMEOUT
from sucrawler.common.exceptions import DownloadException
from sucrawler.core.base import BaseDownloaderImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class AiohttpDownloader(BaseDownloaderImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.max_connections: int = self.config.get("max_connections", 100)
        self.verify_ssl: bool = self.config.get("verify_ssl", True)
        self.follow_redirects: bool = self.config.get("follow_redirects", True)
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            msg = "Session not initialized. Use async context manager or call open() first."
            raise RuntimeError(msg)
        return self._session

    async def open(self) -> None:
        if self._session is None:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                ssl=self.verify_ssl,
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
            )
            logger.info("Aiohttp downloader opened")

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None
            logger.info("Aiohttp downloader closed")

    async def __aenter__(self) -> AiohttpDownloader:
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _do_fetch(self, request: Request) -> Response:
        if self._session is None:
            await self.open()

        proxy = request.proxy
        timeout = aiohttp.ClientTimeout(
            total=request.timeout if request.timeout else DEFAULT_TIMEOUT,
        )

        start_time = time.monotonic()
        try:
            is_bytes_str_or_dict = isinstance(request.data, (bytes, str, dict))
            json_data = None if is_bytes_str_or_dict or request.data is None else request.data
            async with self.session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                data=request.data if is_bytes_str_or_dict else None,
                json=json_data,
                proxy=proxy,
                timeout=timeout,
                allow_redirects=self.follow_redirects,
            ) as aiohttp_response:
                text = await aiohttp_response.text()
                content = await aiohttp_response.read()
                elapsed_seconds = time.monotonic() - start_time
                elapsed = timedelta(seconds=elapsed_seconds)

                return Response(
                    request=request,
                    status_code=aiohttp_response.status,
                    text=text,
                    content=content,
                    headers=dict(aiohttp_response.headers),
                    elapsed=elapsed,
                )
        except aiohttp.ClientError as e:
            msg = f"HTTP error fetching {request.url}: {e!s}"
            raise DownloadException(msg) from e
