from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger

from sucrawler.common.exceptions import PlatformNotFoundException
from sucrawler.core.interfaces.platform import BasePlatform

T = TypeVar("T", bound=type[BasePlatform])


class PlatformRegistry:
    _platforms: dict[str, type[BasePlatform]] = {}

    @classmethod
    def register(cls, name: str, platform_cls: type[BasePlatform]) -> None:
        if name in cls._platforms:
            logger.warning(f"Platform '{name}' already registered, overwriting")
        cls._platforms[name] = platform_cls
        logger.debug(f"Platform '{name}' registered successfully")

    @classmethod
    def get(cls, name: str, config: Any = None) -> BasePlatform:
        if name not in cls._platforms:
            msg = f"Platform '{name}' not found. Available: {cls.list_platforms()}"
            raise PlatformNotFoundException(msg)
        platform_cls = cls._platforms[name]
        return platform_cls(config)

    @classmethod
    def list_platforms(cls) -> list[str]:
        return sorted(cls._platforms.keys())


def register_platform(name: str) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        PlatformRegistry.register(name, cls)
        return cls

    return decorator
