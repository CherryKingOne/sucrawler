from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from sucrawler.browser.cdp.connection import CDPConnection


class TargetManager:
    def __init__(self, connection: CDPConnection) -> None:
        self._connection = connection
        self._targets: list[dict[str, Any]] = []

    @property
    def targets(self) -> list[dict[str, Any]]:
        return self._targets.copy()

    async def refresh(self) -> list[dict[str, Any]]:
        logger.debug("[TargetManager] Refreshing targets")
        self._targets = await self._connection.list_targets()
        return self._targets

    async def get_pages(self) -> list[dict[str, Any]]:
        if not self._targets:
            await self.refresh()
        pages = [t for t in self._targets if t.get("type") == "page"]
        logger.debug(f"[TargetManager] Found {len(pages)} page targets")
        return pages

    async def get_first_page(self) -> Optional[dict[str, Any]]:
        pages = await self.get_pages()
        return pages[0] if pages else None

    async def find_page_by_url(self, url_pattern: str) -> Optional[dict[str, Any]]:
        import re

        pages = await self.get_pages()
        pattern = re.compile(url_pattern)
        for page in pages:
            if pattern.search(page.get("url", "")):
                return page
        return None

    async def new_page(self, url: str = "about:blank") -> dict[str, Any]:
        target = await self._connection.new_page(url)
        self._targets.append(target)
        logger.info(f"[TargetManager] Created new page: {target.get('id')}")
        return target

    async def close_page(self, target_id: str) -> bool:
        success = await self._connection.close_page(target_id)
        if success:
            self._targets = [t for t in self._targets if t.get("id") != target_id]
            logger.info(f"[TargetManager] Closed page: {target_id}")
        return success

    async def close_all_pages(self) -> int:
        pages = await self.get_pages()
        count = 0
        for page in pages:
            if await self.close_page(page["id"]):
                count += 1
        logger.info(f"[TargetManager] Closed {count} pages")
        return count
