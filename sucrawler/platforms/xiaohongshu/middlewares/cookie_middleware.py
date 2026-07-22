from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.common.constants import HTTP_UNAUTHORIZED
from sucrawler.core.base import BaseMiddlewareImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response


class XHSCookieMiddleware(BaseMiddlewareImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.cookie_pool: list[str] = self.config.get("cookie_pool", [])
        self.current_cookie_index: int = 0
        self.failed_cookies: set[str] = set()
        self.rotate_threshold: int = self.config.get("rotate_threshold", 10)
        self.request_count: int = 0

    def _get_next_cookie(self) -> str | None:
        valid_cookies = [
            cookie
            for cookie in self.cookie_pool
            if cookie not in self.failed_cookies
        ]
        if not valid_cookies:
            return None

        if self.current_cookie_index >= len(valid_cookies):
            self.current_cookie_index = 0

        cookie = valid_cookies[self.current_cookie_index]
        self.current_cookie_index += 1
        return cookie

    def _is_cookie_invalid(self, response: Response) -> bool:
        if response.status_code == HTTP_UNAUTHORIZED:
            return True
        try:
            data = response.json()
            if isinstance(data, dict):
                code = data.get("code", data.get("status", 0))
                if code in [-100, 401, 403, 300015]:
                    return True
        except Exception:
            pass
        return False

    async def process_request(self, request: Request) -> Request:
        self.request_count += 1

        if self.cookie_pool:
            if self.request_count % self.rotate_threshold == 0:
                self.current_cookie_index = (
                    self.current_cookie_index + 1
                ) % len(self.cookie_pool)
                logger.debug(
                    "Rotating cookie, new index: {index}",
                    index=self.current_cookie_index,
                )

            cookie = self._get_next_cookie()
            if cookie:
                request.headers["Cookie"] = cookie
                logger.debug(f"Using cookie for {request.url}")

        return request

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Response:
        if self._is_cookie_invalid(response):
            current_cookie = request.headers.get("Cookie", "")
            if current_cookie and current_cookie in self.cookie_pool:
                self.failed_cookies.add(current_cookie)
                logger.warning(
                    f"Cookie marked as failed, remaining: "
                    f"{len(self.cookie_pool) - len(self.failed_cookies)}",
                )

        return response

    async def process_exception(
        self,
        request: Request,
        exception: Exception,
    ) -> None:
        logger.error(f"Cookie middleware exception for {request.url}: {exception}")

    def add_cookie(self, cookie: str) -> None:
        if cookie not in self.cookie_pool:
            self.cookie_pool.append(cookie)
            logger.info(f"Added new cookie to pool, total: {len(self.cookie_pool)}")

    def reset_failed_cookies(self) -> None:
        self.failed_cookies.clear()
        logger.info("Reset all failed cookies")
