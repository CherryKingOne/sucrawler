from __future__ import annotations

import json
import os
from typing import Any, Optional

from loguru import logger


class CookieManager:
    def __init__(self, browser_context: Any) -> None:
        self._context = browser_context

    async def get_all(self) -> list[dict[str, Any]]:
        try:
            cookies = await self._context.cookies()
            logger.debug(f"[CookieManager] Got {len(cookies)} cookies")
            return cookies
        except Exception as e:
            logger.warning(f"[CookieManager] Failed to get cookies: {e}")
            return []

    async def set_cookies(self, cookies: list[dict[str, Any]]) -> None:
        try:
            await self._context.add_cookies(cookies)
            logger.info(f"[CookieManager] Set {len(cookies)} cookies")
        except Exception as e:
            logger.warning(f"[CookieManager] Failed to set cookies: {e}")

    async def clear(self) -> None:
        try:
            await self._context.clear_cookies()
            logger.info("[CookieManager] Cleared all cookies")
        except Exception as e:
            logger.warning(f"[CookieManager] Failed to clear cookies: {e}")

    async def get_by_domain(self, domain: str) -> list[dict[str, Any]]:
        cookies = await self.get_all()
        return [c for c in cookies if domain in c.get("domain", "")]

    async def get_by_name(self, name: str, domain: Optional[str] = None) -> Optional[dict[str, Any]]:
        cookies = await self.get_all()
        for cookie in cookies:
            if cookie.get("name") == name:
                if domain and domain not in cookie.get("domain", ""):
                    continue
                return cookie
        return None

    async def save_to_file(self, file_path: str) -> None:
        cookies = await self.get_all()
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"[CookieManager] Saved {len(cookies)} cookies to {file_path}")
        except Exception as e:
            logger.warning(f"[CookieManager] Failed to save cookies: {e}")

    async def load_from_file(self, file_path: str) -> int:
        if not os.path.isfile(file_path):
            logger.warning(f"[CookieManager] Cookie file not found: {file_path}")
            return 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            if cookies:
                await self.set_cookies(cookies)
            logger.info(f"[CookieManager] Loaded {len(cookies)} cookies from {file_path}")
            return len(cookies)
        except Exception as e:
            logger.warning(f"[CookieManager] Failed to load cookies: {e}")
            return 0

    async def export_for_requests(self, domain: Optional[str] = None) -> dict[str, str]:
        cookies = await self.get_all()
        result: dict[str, str] = {}
        for cookie in cookies:
            if domain and domain not in cookie.get("domain", ""):
                continue
            result[cookie["name"]] = cookie["value"]
        return result

    async def export_cookie_header(self, domain: Optional[str] = None) -> str:
        cookies = await self.export_for_requests(domain)
        return "; ".join(f"{k}={v}" for k, v in cookies.items())
