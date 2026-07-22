from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from sucrawler.common.constants import DEFAULT_TIMEOUT
from sucrawler.common.exceptions import DownloadException
from sucrawler.core.base import BaseDownloaderImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.platforms.bilibili.config import BiliConfig


class BiliDownloader(BaseDownloaderImpl):
    def __init__(self, config: BiliConfig) -> None:
        super().__init__(config.model_dump())
        self.bili_config = config
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            msg = "Client not initialized. Use async context manager or call open() first."
            raise RuntimeError(msg)
        return self._client

    async def open(self) -> None:
        if self._client is None:
            cookie = self.bili_config.cookie
            if self.bili_config.sessdata and "SESSDATA" not in cookie:
                cookie = f"SESSDATA={self.bili_config.sessdata}; {cookie}".strip()
            if self.bili_config.bili_jct and "bili_jct" not in cookie:
                cookie = f"bili_jct={self.bili_config.bili_jct}; {cookie}".strip()

            headers = {
                "User-Agent": self.bili_config.user_agent,
                "Referer": self.bili_config.base_url + "/",
                "Origin": self.bili_config.base_url,
            }
            if cookie:
                headers["Cookie"] = cookie

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(DEFAULT_TIMEOUT),
                follow_redirects=True,
            )
            logger.info("Bilibili downloader opened")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Bilibili downloader closed")

    async def __aenter__(self) -> BiliDownloader:
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _do_fetch(self, request: Request) -> Response:
        if self._client is None:
            await self.open()

        try:
            is_bytes_or_str = isinstance(request.data, (bytes, str))
            json_data = (
                None
                if is_bytes_or_str or request.data is None
                else request.data
            )
            httpx_response = await self.client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                content=request.data if is_bytes_or_str else None,
                json=json_data,
            )
        except httpx.HTTPError as e:
            msg = f"HTTP error fetching {request.url}: {e!s}"
            raise DownloadException(msg) from e

        from datetime import timedelta

        elapsed = timedelta(seconds=httpx_response.elapsed.total_seconds())

        return Response(
            request=request,
            status_code=httpx_response.status_code,
            text=httpx_response.text,
            content=httpx_response.content,
            headers=dict(httpx_response.headers),
            elapsed=elapsed,
        )
