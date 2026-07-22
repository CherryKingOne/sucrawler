from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from loguru import logger

from sucrawler.browser.manager.browser_manager import BrowserManager


class BrowserSession:
    def __init__(self, browser_manager: BrowserManager) -> None:
        self._manager = browser_manager
        self._session_id: str = str(uuid.uuid4())
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None
        self._active: bool = False

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def page(self) -> Optional[Any]:
        return self._page

    @property
    def context(self) -> Optional[Any]:
        return self._context

    @property
    def is_active(self) -> bool:
        return self._active

    async def open(self, initial_url: str = "about:blank") -> None:
        if self._active:
            logger.warning(f"[BrowserSession] Session {self._session_id} already active")
            return

        logger.info(f"[BrowserSession] Opening session {self._session_id}")

        if not self._manager.is_started:
            await self._manager.start()

        self._page = await self._manager.new_page(initial_url)
        self._active = True
        logger.info(f"[BrowserSession] Session {self._session_id} opened")

    async def close(self) -> None:
        if not self._active:
            return

        logger.info(f"[BrowserSession] Closing session {self._session_id}")

        if self._page:
            try:
                await self._page.close()
                logger.debug(f"[BrowserSession] Page closed for session {self._session_id}")
            except Exception as e:
                logger.warning(f"[BrowserSession] Failed to close page: {e}")
            finally:
                self._page = None

        self._active = False
        logger.info(f"[BrowserSession] Session {self._session_id} closed")

    async def navigate(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> Any:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")

        logger.debug(f"[BrowserSession] Navigating to: {url}")
        response = await self._page.goto(url, wait_until=wait_until, timeout=timeout)
        return response

    async def evaluate(self, script: str, *args: Any) -> Any:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")
        return await self._page.evaluate(script, *args)

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> bytes:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")

        kwargs: dict[str, Any] = {"full_page": full_page}
        if path:
            kwargs["path"] = path

        return await self._page.screenshot(**kwargs)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 10000,
        state: str = "visible",
    ) -> Any:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")
        return await self._page.wait_for_selector(selector, timeout=timeout, state=state)

    async def content(self) -> str:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")
        return await self._page.content()

    async def url(self) -> str:
        if not self._page:
            raise RuntimeError("Session not active. Call open() first.")
        return self._page.url

    async def __aenter__(self) -> "BrowserSession":
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
