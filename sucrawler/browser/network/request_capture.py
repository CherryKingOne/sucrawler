from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger


class RequestCapture:
    def __init__(self, page: Any, url_pattern: str = "") -> None:
        self._page = page
        self._url_pattern = url_pattern
        self._captured_requests: list[dict[str, Any]] = []
        self._captured_responses: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._active: bool = False

    @property
    def captured_requests(self) -> list[dict[str, Any]]:
        return self._captured_requests.copy()

    @property
    def captured_responses(self) -> list[dict[str, Any]]:
        return self._captured_responses.copy()

    async def start(self) -> None:
        if self._active:
            return

        self._page.on("request", self._on_request)
        self._page.on("response", self._on_response)
        self._active = True
        logger.info(f"[RequestCapture] Started, pattern: {self._url_pattern}")

    async def stop(self) -> None:
        if not self._active:
            return

        try:
            self._page.remove_listener("request", self._on_request)
            self._page.remove_listener("response", self._on_response)
        except Exception:
            pass

        self._active = False
        logger.info(f"[RequestCapture] Stopped, captured: {len(self._captured_requests)} requests")

    def clear(self) -> None:
        self._captured_requests.clear()
        self._captured_responses.clear()

    async def wait_for_request(
        self,
        url_pattern: str,
        timeout: float = 30.0,
    ) -> Optional[dict[str, Any]]:
        import re

        pattern = re.compile(url_pattern)
        start = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start < timeout:
            async with self._lock:
                for req in self._captured_requests:
                    if pattern.search(req.get("url", "")):
                        return req

            await asyncio.sleep(0.1)

        logger.warning(f"[RequestCapture] Request matching '{url_pattern}' not found within {timeout}s")
        return None

    async def wait_for_response(
        self,
        url_pattern: str,
        timeout: float = 30.0,
    ) -> Optional[dict[str, Any]]:
        import re

        pattern = re.compile(url_pattern)
        start = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start < timeout:
            async with self._lock:
                for resp in self._captured_responses:
                    if pattern.search(resp.get("url", "")):
                        return resp

            await asyncio.sleep(0.1)

        logger.warning(f"[RequestCapture] Response matching '{url_pattern}' not found within {timeout}s")
        return None

    async def _on_request(self, request: Any) -> None:
        import re

        url = request.url
        if self._url_pattern and not re.search(self._url_pattern, url):
            return

        async with self._lock:
            try:
                data = {
                    "url": url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "resource_type": request.resource_type,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                self._captured_requests.append(data)
                logger.debug(f"[RequestCapture] Request: {request.method} {url}")
            except Exception as e:
                logger.debug(f"[RequestCapture] Error capturing request: {e}")

    async def _on_response(self, response: Any) -> None:
        import re

        url = response.url
        if self._url_pattern and not re.search(self._url_pattern, url):
            return

        async with self._lock:
            try:
                data = {
                    "url": url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "timestamp": asyncio.get_event_loop().time(),
                }
                self._captured_responses.append(data)
                logger.debug(f"[RequestCapture] Response: {response.status} {url}")
            except Exception as e:
                logger.debug(f"[RequestCapture] Error capturing response: {e}")

    async def __aenter__(self) -> "RequestCapture":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()
