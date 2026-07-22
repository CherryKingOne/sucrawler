from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractCache(ABC):
    """缓存抽象基类。"""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """获取缓存值。

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或已过期返回 None
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, expire_time: int) -> None:
        """设置缓存。

        Args:
            key: 缓存键
            value: 缓存值
            expire_time: 过期时间（秒）
        """
        raise NotImplementedError

    @abstractmethod
    def keys(self, pattern: str) -> list[str]:
        """获取匹配模式的所有键。

        Args:
            pattern: 匹配模式，支持 * 通配符

        Returns:
            匹配的键列表
        """
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """删除缓存键。

        Args:
            key: 缓存键
        """
        raise NotImplementedError

    def clear(self) -> None:
        """清空所有缓存。"""
        raise NotImplementedError
