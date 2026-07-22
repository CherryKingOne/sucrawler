from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger

from .base import AbstractCache


class ExpiringLocalCache(AbstractCache):
    """带过期时间的本地内存缓存。

    使用字典存储，每个值附带过期时间戳。
    支持定时清理过期键和获取时的惰性检查。
    """

    def __init__(self, cron_interval: int = 10) -> None:
        """初始化本地缓存。

        Args:
            cron_interval: 定时清理的间隔时间（秒），默认 10 秒
        """
        self._cron_interval = cron_interval
        self._cache: dict[str, tuple[Any, float]] = {}
        self._cron_task: asyncio.Task | None = None
        self._schedule_clear()

    def __del__(self) -> None:
        if self._cron_task is not None and not self._cron_task.done():
            self._cron_task.cancel()
            self._cron_task = None

    def get(self, key: str) -> Any | None:
        value, expire_time = self._cache.get(key, (None, 0.0))
        if value is None:
            return None

        if expire_time < time.time():
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, expire_time: int) -> None:
        self._cache[key] = (value, time.time() + expire_time)

    def keys(self, pattern: str) -> list[str]:
        if pattern == "*":
            return list(self._cache.keys())

        if "*" in pattern:
            parts = pattern.split("*")
            return [
                key
                for key in self._cache.keys()
                if all(part in key for part in parts if part)
            ]

        return [key for key in self._cache.keys() if pattern in key]

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    def _schedule_clear(self) -> None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._cron_task = loop.create_task(self._clear_cron())

    def _clear_expired(self) -> None:
        now = time.time()
        expired_keys = [key for key, (_, expire_time) in self._cache.items() if expire_time < now]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"[LocalCache] Cleared {len(expired_keys)} expired keys")

    async def _clear_cron(self) -> None:
        logger.debug(f"[LocalCache] Started cleanup cron (interval: {self._cron_interval}s)")
        while True:
            try:
                self._clear_expired()
                await asyncio.sleep(self._cron_interval)
            except asyncio.CancelledError:
                logger.debug("[LocalCache] Cleanup cron cancelled")
                break
            except Exception as e:
                logger.error(f"[LocalCache] Cleanup cron error: {e}")
                await asyncio.sleep(self._cron_interval)
