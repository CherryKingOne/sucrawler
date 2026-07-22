from __future__ import annotations

import asyncio
import socket
from typing import Any, Optional

import httpx
from loguru import logger

from sucrawler.browser.exceptions import (
    BrowserConnectionError,
    BrowserTimeoutError,
)


class CDPConnection:
    def __init__(self, debug_port: int, host: str = "localhost") -> None:
        self.debug_port = debug_port
        self.host = host
        self._ws_url: Optional[str] = None
        self._browser_info: Optional[dict[str, Any]] = None

    @property
    def ws_url(self) -> Optional[str]:
        return self._ws_url

    @property
    def browser_info(self) -> Optional[dict[str, Any]]:
        return self._browser_info

    async def test_connection(self, timeout: float = 5.0) -> bool:
        logger.debug(f"[CDPConnection] Testing connection to {self.host}:{self.debug_port}")
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.debug_port),
                timeout=timeout,
            )
            writer.close()
            await writer.wait_closed()
            logger.debug(f"[CDPConnection] Port {self.debug_port} is reachable")
            return True
        except (OSError, asyncio.TimeoutError):
            logger.debug(f"[CDPConnection] Port {self.debug_port} is not reachable")
            return False

    async def wait_until_ready(self, timeout: int = 30, interval: float = 1.0) -> bool:
        logger.info(f"[CDPConnection] Waiting for CDP on port {self.debug_port}...")
        elapsed = 0.0
        while elapsed < timeout:
            if await self.test_connection(timeout=2.0):
                try:
                    await self.fetch_browser_info()
                    logger.info(f"[CDPConnection] CDP ready on port {self.debug_port}")
                    return True
                except BrowserConnectionError:
                    pass
            await asyncio.sleep(interval)
            elapsed += interval

        logger.error(f"[CDPConnection] CDP not ready within {timeout}s")
        return False

    async def fetch_browser_info(self) -> dict[str, Any]:
        url = f"http://{self.host}:{self.debug_port}/json/version"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    raise BrowserConnectionError(
                        f"Failed to fetch browser info: HTTP {response.status_code}"
                    )
                data = response.json()
                self._browser_info = data
                self._ws_url = data.get("webSocketDebuggerUrl")
                logger.debug(f"[CDPConnection] Browser info: {data.get('Browser', 'unknown')}")
                return data
        except httpx.HTTPError as e:
            raise BrowserConnectionError(f"Failed to connect to CDP: {e}") from e

    async def get_websocket_url(self, connect_existing: bool = False) -> str:
        if self._ws_url:
            return self._ws_url

        if connect_existing:
            direct_url = f"ws://{self.host}:{self.debug_port}/devtools/browser"
            logger.info(f"[CDPConnection] Trying direct WebSocket URL: {direct_url}")
            self._ws_url = direct_url
            return direct_url

        await self.fetch_browser_info()
        if not self._ws_url:
            raise BrowserConnectionError("webSocketDebuggerUrl not found in browser info")
        return self._ws_url

    async def list_targets(self) -> list[dict[str, Any]]:
        url = f"http://{self.host}:{self.debug_port}/json/list"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    raise BrowserConnectionError(
                        f"Failed to list targets: HTTP {response.status_code}"
                    )
                targets = response.json()
                logger.debug(f"[CDPConnection] Found {len(targets)} targets")
                return targets
        except httpx.HTTPError as e:
            raise BrowserConnectionError(f"Failed to list targets: {e}") from e

    async def new_page(self, url: str = "about:blank") -> dict[str, Any]:
        api_url = f"http://{self.host}:{self.debug_port}/json/new?{url}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(api_url, timeout=10.0)
                if response.status_code != 200:
                    raise BrowserConnectionError(
                        f"Failed to create new page: HTTP {response.status_code}"
                    )
                target = response.json()
                logger.debug(f"[CDPConnection] Created new page: {target.get('id')}")
                return target
        except httpx.HTTPError as e:
            raise BrowserConnectionError(f"Failed to create new page: {e}") from e

    async def close_page(self, target_id: str) -> bool:
        url = f"http://{self.host}:{self.debug_port}/json/close/{target_id}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                success = response.status_code == 200
                logger.debug(f"[CDPConnection] Closed page {target_id}: {success}")
                return success
        except httpx.HTTPError as e:
            logger.warning(f"[CDPConnection] Failed to close page {target_id}: {e}")
            return False

    def _test_sync(self, timeout: float = 5.0) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex((self.host, self.debug_port)) == 0
        except OSError:
            return False
