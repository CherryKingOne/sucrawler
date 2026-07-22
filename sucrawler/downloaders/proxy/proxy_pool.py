from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger


class ProxyPool:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._proxies: dict[str, dict[str, Any]] = {}
        self._failed_proxies: dict[str, float] = {}
        self.failure_threshold: int = self.config.get("failure_threshold", 3)
        self.recovery_time: float = self.config.get("recovery_time", 300.0)
        self._lock: asyncio.Lock | None = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def add_proxy(self, proxy: str) -> None:
        if proxy not in self._proxies:
            self._proxies[proxy] = {
                "failure_count": 0,
                "last_used": 0.0,
                "success_count": 0,
            }
            logger.debug("Added proxy: {proxy}", proxy=proxy)

    def remove_proxy(self, proxy: str) -> None:
        self._proxies.pop(proxy, None)
        self._failed_proxies.pop(proxy, None)
        logger.debug("Removed proxy: {proxy}", proxy=proxy)

    def get_proxy(self) -> str | None:
        self._recover_proxies()
        available = [p for p in self._proxies if p not in self._failed_proxies]
        if not available:
            return None
        available.sort(key=lambda p: self._proxies[p]["last_used"])
        proxy = available[0]
        self._proxies[proxy]["last_used"] = time.monotonic()
        return proxy

    def mark_failed(self, proxy: str) -> None:
        if proxy not in self._proxies:
            return

        self._proxies[proxy]["failure_count"] += 1
        failure_count = self._proxies[proxy]["failure_count"]

        if failure_count >= self.failure_threshold:
            self._failed_proxies[proxy] = time.monotonic()
            logger.warning(
                "Proxy {proxy} marked as failed after {count} failures",
                proxy=proxy,
                count=failure_count,
            )

    def mark_success(self, proxy: str) -> None:
        if proxy not in self._proxies:
            return
        self._proxies[proxy]["success_count"] += 1
        if self._proxies[proxy]["failure_count"] > 0:
            self._proxies[proxy]["failure_count"] = max(
                0,
                self._proxies[proxy]["failure_count"] - 1,
            )

    def _recover_proxies(self) -> None:
        now = time.monotonic()
        recovered: list[str] = []
        for proxy, fail_time in self._failed_proxies.items():
            if now - fail_time >= self.recovery_time:
                recovered.append(proxy)
                if proxy in self._proxies:
                    self._proxies[proxy]["failure_count"] = 0

        for proxy in recovered:
            self._failed_proxies.pop(proxy, None)
            logger.info("Proxy {proxy} recovered", proxy=proxy)

    def get_available_proxies(self) -> list[str]:
        self._recover_proxies()
        return [p for p in self._proxies if p not in self._failed_proxies]

    def get_available_count(self) -> int:
        return len(self.get_available_proxies())

    def update_last_used(self, proxy: str) -> None:
        if proxy in self._proxies:
            self._proxies[proxy]["last_used"] = time.monotonic()

    def get_total_count(self) -> int:
        return len(self._proxies)

    def get_stats(self) -> dict[str, Any]:
        self._recover_proxies()
        return {
            "total": len(self._proxies),
            "available": self.get_available_count(),
            "failed": len(self._failed_proxies),
            "proxies": {
                proxy: {
                    "failure_count": info["failure_count"],
                    "success_count": info["success_count"],
                    "is_failed": proxy in self._failed_proxies,
                }
                for proxy, info in self._proxies.items()
            },
        }
