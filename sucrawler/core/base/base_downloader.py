from __future__ import annotations

import asyncio
from typing import Any

from sucrawler.common.constants import DEFAULT_TIMEOUT
from sucrawler.common.exceptions import DownloadException
from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class BaseDownloaderImpl(BaseDownloader):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.max_retries: int = self.config.get("max_retries", 3)
        self.retry_delay: float = self.config.get("retry_delay", 1.0)
        self.timeout: float = self.config.get("timeout", DEFAULT_TIMEOUT)

    async def fetch(self, request: Request) -> Response:
        last_exception: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return await self._do_fetch(request)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
        msg = f"Failed to fetch {request.url} after {self.max_retries} retries"
        raise DownloadException(msg) from last_exception

    async def fetch_batch(self, requests: list[Request]) -> list[Response]:
        tasks = [self.fetch(request) for request in requests]
        return await asyncio.gather(*tasks)

    async def _do_fetch(self, request: Request) -> Response:
        msg = "_do_fetch must be implemented by subclass"
        raise NotImplementedError(msg)
