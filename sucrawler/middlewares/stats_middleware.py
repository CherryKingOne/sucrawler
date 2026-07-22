from __future__ import annotations

import time
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class StatsMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.total_requests: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.total_elapsed: float = 0.0
        self._status_codes: dict[int, int] = {}

    async def process_request(self, request: Request) -> Request:
        self.total_requests += 1
        request.meta["stats_start_time"] = time.monotonic()
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        start_time = request.meta.get("stats_start_time", time.monotonic())
        elapsed = time.monotonic() - start_time
        self.total_elapsed += elapsed

        if response.ok:
            self.success_count += 1
        else:
            self.failure_count += 1

        self._status_codes[response.status_code] = (
            self._status_codes.get(response.status_code, 0) + 1
        )

        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        self.failure_count += 1
        start_time = request.meta.get("stats_start_time", time.monotonic())
        elapsed = time.monotonic() - start_time
        self.total_elapsed += elapsed
        return None

    def get_stats(self) -> dict[str, Any]:
        avg_elapsed = self.total_elapsed / self.total_requests if self.total_requests > 0 else 0.0
        success_rate = (
            self.success_count / self.total_requests * 100
            if self.total_requests > 0
            else 0.0
        )
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(success_rate, 2),
            "avg_elapsed": round(avg_elapsed, 4),
            "total_elapsed": round(self.total_elapsed, 4),
            "status_codes": dict(self._status_codes),
        }

    def reset(self) -> None:
        self.total_requests = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_elapsed = 0.0
        self._status_codes.clear()
        logger.info("Stats middleware reset")

    def log_stats(self) -> None:
        stats = self.get_stats()
        logger.info(
            "Stats: total={total}, success={success}, failure={failure}, "
            "rate={rate}%, avg={avg:.4f}s",
            total=stats["total_requests"],
            success=stats["success_count"],
            failure=stats["failure_count"],
            rate=stats["success_rate"],
            avg=stats["avg_elapsed"],
        )
