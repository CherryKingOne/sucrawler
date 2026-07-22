from __future__ import annotations

from typing import Any

from .base import AbstractCache
from .local_cache import ExpiringLocalCache


class CacheFactory:
    """缓存工厂，创建不同类型的缓存实例。"""

    _instances: dict[str, AbstractCache] = {}

    @staticmethod
    def create_cache(
        cache_type: str = "local",
        **kwargs: Any,
    ) -> AbstractCache:
        """创建缓存实例。

        Args:
            cache_type: 缓存类型，支持 'local' / 'redis'
            **kwargs: 传递给缓存实现的额外参数

        Returns:
            缓存实例

        Raises:
            ValueError: 不支持的缓存类型
        """
        cache_key = f"{cache_type}:{sorted(kwargs.items())}"

        if cache_key in CacheFactory._instances:
            return CacheFactory._instances[cache_key]

        if cache_type == "local":
            cache = ExpiringLocalCache(**kwargs)
        elif cache_type == "redis":
            try:
                from .redis_cache import RedisCache

                cache = RedisCache(**kwargs)
            except ImportError as e:
                raise ValueError(
                    "Redis cache requires 'redis' package. "
                    "Install with: pip install redis",
                ) from e
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}")

        CacheFactory._instances[cache_key] = cache
        return cache

    @staticmethod
    def reset() -> None:
        """清空所有缓存实例（主要用于测试）。"""
        CacheFactory._instances.clear()
