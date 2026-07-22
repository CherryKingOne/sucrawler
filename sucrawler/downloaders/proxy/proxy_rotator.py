from __future__ import annotations

import random
from typing import Any

from loguru import logger

from sucrawler.downloaders.proxy.proxy_pool import ProxyPool


class ProxyRotator:
    def __init__(
        self,
        proxy_pool: ProxyPool,
        strategy: str = "round_robin",
        config: dict[str, Any] | None = None,
    ) -> None:
        self.proxy_pool = proxy_pool
        self.strategy = strategy
        self.config = config or {}
        self._round_robin_index: int = 0

    def next(self) -> str | None:
        if self.strategy == "round_robin":
            return self._round_robin()
        if self.strategy == "random":
            return self._random()
        logger.warning(
            "Unknown proxy strategy: {strategy}, using round_robin",
            strategy=self.strategy,
        )
        return self._round_robin()

    def _round_robin(self) -> str | None:
        proxy = self.proxy_pool.get_proxy()
        if proxy:
            self._round_robin_index += 1
        return proxy

    def _random(self) -> str | None:
        available = self.proxy_pool.get_available_proxies()
        if not available:
            return None
        proxy = random.choice(available)
        self.proxy_pool.update_last_used(proxy)
        return proxy

    def set_strategy(self, strategy: str) -> None:
        if strategy not in {"round_robin", "random"}:
            msg = f"Invalid strategy: {strategy}. Must be 'round_robin' or 'random'"
            raise ValueError(msg)
        self.strategy = strategy
        logger.info("Proxy rotator strategy set to: {strategy}", strategy=strategy)

    def reset(self) -> None:
        self._round_robin_index = 0
