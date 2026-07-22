from __future__ import annotations

from datetime import timedelta
from typing import Any

from loguru import logger

from sucrawler.common.constants import DEFAULT_TIMEOUT
from sucrawler.common.exceptions import DownloadException
from sucrawler.core.base import BaseDownloaderImpl
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.browser.manager.browser_manager import BrowserManager
from sucrawler.browser.types import BrowserConfig


class CDPDownloader(BaseDownloaderImpl):
    def __init__(
        self,
        config: dict[str, Any] | None = None,
        browser_config: BrowserConfig | None = None,
        browser_manager: BrowserManager | None = None,
    ) -> None:
        super().__init__(config)
        self._browser_config = browser_config or BrowserConfig(mode="cdp", enabled=True)
        self._browser_manager = browser_manager
        self._owns_manager = browser_manager is None
        self._page: Any = None
        self._wait_until: str = self.config.get("wait_until", "domcontentloaded")
        self._stealth_enabled: bool = self.config.get("stealth_enabled", True)

    @property
    def browser_manager(self) -> BrowserManager | None:
        return self._browser_manager

    @property
    def browser_config(self) -> BrowserConfig:
        return self._browser_config

    async def open(self) -> None:
        if self._browser_manager is None:
            from sucrawler.browser.manager.browser_manager import BrowserManager

            self._browser_manager = BrowserManager(self._browser_config)

        if not self._browser_manager.is_started:
            await self._browser_manager.start()

        if self._page is None:
            self._page = await self._browser_manager.new_page()
            logger.info("CDP downloader opened")

    async def close(self) -> None:
        if self._page:
            try:
                await self._page.close()
            except Exception as e:
                logger.warning(f"Error closing CDP page: {e}")
            finally:
                self._page = None

        if self._owns_manager and self._browser_manager:
            await self._browser_manager.stop()
            self._browser_manager = None

        logger.info("CDP downloader closed")

    async def __aenter__(self) -> "CDPDownloader":
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _do_fetch(self, request: Request) -> Response:
        if self._page is None:
            await self.open()

        if self._page is None or self._browser_manager is None:
            raise DownloadException("CDP downloader not initialized")

        timeout = request.timeout if request.timeout else self.timeout
        if timeout is None:
            timeout = DEFAULT_TIMEOUT

        try:
            import time

            start = time.perf_counter()

            extra_headers: dict[str, str] = {}
            if request.headers:
                extra_headers = dict(request.headers)

            if extra_headers:
                await self._page.set_extra_http_headers(extra_headers)

            response = await self._page.goto(
                request.url,
                wait_until=self._wait_until,
                timeout=timeout * 1000,
            )

            status_code = response.status if response else 200
            headers = dict(response.headers) if response else {}

            content = await self._page.content()
            body_bytes = content.encode("utf-8")

            elapsed = timedelta(seconds=time.perf_counter() - start)

            return Response(
                request=request,
                status_code=status_code,
                text=content,
                content=body_bytes,
                headers=headers,
                elapsed=elapsed,
            )

        except Exception as e:
            msg = f"CDP downloader error for {request.url}: {e!s}"
            raise DownloadException(msg) from e

    async def get_page(self) -> Any:
        if self._page is None:
            await self.open()
        return self._page

    async def evaluate(self, script: str, *args: Any) -> Any:
        if self._page is None:
            await self.open()
        return await self._page.evaluate(script, *args)

    async def screenshot(self, path: str | None = None, full_page: bool = False) -> bytes:
        if self._page is None:
            await self.open()
        kwargs: dict[str, Any] = {"full_page": full_page}
        if path:
            kwargs["path"] = path
        return await self._page.screenshot(**kwargs)

    async def get_cookies(self, url: str | None = None) -> list[dict[str, Any]]:
        if self._page is None:
            await self.open()
        if self._page and self._page.context:
            ctx = self._page.context
            if url:
                return await ctx.cookies(url)
            return await ctx.cookies()
        return []

    async def set_cookies(self, cookies: list[dict[str, Any]]) -> None:
        if self._page is None:
            await self.open()
        if self._page and self._page.context:
            await self._page.context.add_cookies(cookies)

    async def clear_cookies(self) -> None:
        if self._page is None:
            await self.open()
        if self._page and self._page.context:
            await self._page.context.clear_cookies()
