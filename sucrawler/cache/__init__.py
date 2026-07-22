"""缓存系统。

通用的缓存抽象，支持本地内存缓存和 Redis 缓存（可选）。
"""
from .base import AbstractCache
from .factory import CacheFactory
from .local_cache import ExpiringLocalCache

__all__ = ["AbstractCache", "ExpiringLocalCache", "CacheFactory"]
