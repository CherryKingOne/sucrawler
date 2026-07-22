from __future__ import annotations

import time
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.logging.trace import generate_trace_id, get_trace_id, set_trace_id


class LogMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.log_level: str = self.config.get("log_level", "INFO")
        self.log_request_headers: bool = self.config.get("log_request_headers", False)
        self.log_response_headers: bool = self.config.get("log_response_headers", False)

    async def process_request(self, request: Request) -> Request:
        trace_id = request.meta.get("trace_id") or get_trace_id()
        if not request.meta.get("trace_id"):
            request.meta["trace_id"] = trace_id
        set_trace_id(trace_id)

        request.meta["start_time"] = time.monotonic()

        log_msg = f"Request: {request.method} {request.url}"
        if self.log_request_headers:
            log_msg += f" headers={request.headers}"

        logger.info(
            "[{trace_id}] {msg}",
            trace_id=trace_id,
            msg=log_msg,
        )
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        trace_id = request.meta.get("trace_id", generate_trace_id())
        start_time = request.meta.get("start_time", time.monotonic())
        elapsed = time.monotonic() - start_time

        log_msg = (
            f"Response: {request.method} {request.url} "
            f"status={response.status_code} elapsed={elapsed:.3f}s"
        )
        if self.log_response_headers:
            log_msg += f" headers={response.headers}"

        logger.info(
            "[{trace_id}] {msg}",
            trace_id=trace_id,
            msg=log_msg,
        )
        return response

    async def process_exception(self, request: Request, exception: Exception) -> None:
        trace_id = request.meta.get("trace_id", generate_trace_id())
        start_time = request.meta.get("start_time", time.monotonic())
        elapsed = time.monotonic() - start_time

        logger.error(
            "[{trace_id}] Error: {method} {url} {exc_type}: {exc_msg} elapsed={elapsed:.3f}s",
            trace_id=trace_id,
            method=request.method,
            url=request.url,
            exc_type=type(exception).__name__,
            exc_msg=str(exception),
            elapsed=elapsed,
        )
        return None
