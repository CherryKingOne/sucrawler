from __future__ import annotations

import asyncio
import random
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import DownloadException
from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class RetryMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.max_attempts: int = int(self.config.get("max_attempts", 3))
        self.backoff_factor: float = float(self.config.get("backoff_factor", 1.0))
        self.jitter: float = float(self.config.get("jitter", 0.5))
        self.retry_on_status_codes: set[int] = set(
            self.config.get(
                "retry_on_status_codes",
                {429, 500, 502, 503, 504},
            ),
        )

    async def process_request(self, request: Request) -> Request:
        request.meta.setdefault("retry_count", 0)
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if response.status_code in self.retry_on_status_codes:
            retry_count = request.meta.get("retry_count", 0)
            if retry_count < self.max_attempts:
                delay = self._calculate_delay(retry_count)
                logger.warning(
                    "Retrying {url} (attempt {attempt}/{max_attempts}) "
                    "after status {status_code} in {delay:.2f}s",
                    url=request.url,
                    attempt=retry_count + 1,
                    max_attempts=self.max_attempts,
                    status_code=response.status_code,
                    delay=delay,
                )
                request.meta["retry_count"] = retry_count + 1
                await asyncio.sleep(delay)
                return await self._retry_request(request)
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        retry_count = request.meta.get("retry_count", 0)
        if retry_count < self.max_attempts and self._is_retryable(exception):
            delay = self._calculate_delay(retry_count)
            logger.warning(
                "Retrying {url} (attempt {attempt}/{max_attempts}) "
                "after {exc_type}: {exc_msg} in {delay:.2f}s",
                url=request.url,
                attempt=retry_count + 1,
                max_attempts=self.max_attempts,
                exc_type=type(exception).__name__,
                exc_msg=str(exception),
                delay=delay,
            )
            request.meta["retry_count"] = retry_count + 1
            await asyncio.sleep(delay)
        return None

    def _calculate_delay(self, attempt: int) -> float:
        base_delay = float(self.backoff_factor * (2**attempt))
        jitter = float(random.uniform(0, self.jitter))
        return base_delay + jitter

    def _is_retryable(self, exception: Exception) -> bool:
        if isinstance(exception, DownloadException):
            return True
        return isinstance(exception, (ConnectionError, TimeoutError, OSError))

    async def _retry_request(self, request: Request) -> Response:
        msg = "_retry_request should be handled by the downloader pipeline"
        raise NotImplementedError(msg)
