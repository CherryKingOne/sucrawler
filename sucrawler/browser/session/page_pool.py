from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger

from sucrawler.browser.manager.browser_manager import BrowserManager


class PagePool:
    def __init__(
        self,
        browser_manager: BrowserManager,
        min_size: int = 1,
        max_size: int = 5,
    ) -> None:
        self._manager = browser_manager
        self._min_size = min_size
        self._max_size = max_size
        self._pool: list[Any] = []
        self._lock: asyncio.Lock = asyncio.Lock()
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_size)
        self._initialized: bool = False

    @property
    def size(self) -> int:
        return len(self._pool)

    @property
    def available(self) -> int:
        return self._semaphore._value

    async def initialize(self) -> None:
        if self._initialized:
            return

        logger.info(f"[PagePool] Initializing pool with min_size={self._min_size}")

        if not self._manager.is_started:
            await self._manager.start()

        for _ in range(self._min_size):
            page = await self._manager.new_page()
            self._pool.append(page)

        self._initialized = True
        logger.info(f"[PagePool] Initialized with {self._min_size} pages")

    async def acquire(self) -> Any:
        if not self._initialized:
            await self.initialize()

        await self._semaphore.acquire()

        async with self._lock:
            if self._pool:
                page = self._pool.pop()
                logger.debug(f"[PagePool] Acquired page from pool, remaining: {len(self._pool)}")
                return page

            page = await self._manager.new_page()
            logger.debug(f"[PagePool] Created new page, pool size: {len(self._pool)}")
            return page

    async def release(self, page: Any) -> None:
        async with self._lock:
            if len(self._pool) < self._max_size:
                try:
                    await page.goto("about:blank")
                except Exception as e:
                    logger.debug(f"[PagePool] Error resetting page: {e}")

                self._pool.append(page)
                logger.debug(f"[PagePool] Released page to pool, pool size: {len(self._pool)}")
            else:
                try:
                    await page.close()
                    logger.debug("[PagePool] Pool full, closed excess page")
                except Exception as e:
                    logger.debug(f"[PagePool] Error closing excess page: {e}")

        self._semaphore.release()

    async def close_all(self) -> None:
        async with self._lock:
            count = 0
            for page in self._pool:
                try:
                    await page.close()
                    count += 1
                except Exception as e:
                    logger.debug(f"[PagePool] Error closing page: {e}")
            self._pool.clear()
            logger.info(f"[PagePool] Closed all {count} pages")

        self._initialized = False

    async def __aenter__(self) -> "PagePool":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close_all()
