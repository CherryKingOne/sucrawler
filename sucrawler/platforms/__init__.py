from sucrawler.platforms import bilibili  # noqa: F401
from sucrawler.platforms import xiaohongshu  # noqa: F401
from sucrawler.platforms.registry import PlatformRegistry, register_platform

__all__ = [
    "PlatformRegistry",
    "register_platform",
]
