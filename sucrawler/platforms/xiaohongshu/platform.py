from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.interfaces.pipeline import BasePipeline
from sucrawler.core.interfaces.platform import BasePlatform
from sucrawler.platforms.registry import register_platform
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader
from sucrawler.platforms.xiaohongshu.extractor import XHSExtractor
from sucrawler.platforms.xiaohongshu.middlewares import (
    XHSCookieMiddleware,
    XHSSignMiddleware,
)
from sucrawler.platforms.xiaohongshu.parser import XHSParser


@register_platform("xiaohongshu")
class XiaohongshuPlatform(BasePlatform):
    name = "xiaohongshu"

    def __init__(self, config: Any = None) -> None:
        if isinstance(config, XHSConfig):
            self.config = config
        elif isinstance(config, dict):
            self.config = XHSConfig(**config)
        else:
            self.config = XHSConfig()
        logger.info(f"Initialized {self.name} platform")

    def create_downloader(self) -> BaseDownloader:
        return XHSDownloader(self.config)

    def create_parser(self) -> BaseParser:
        return XHSParser()

    def create_extractor(self) -> BaseExtractor:
        return XHSExtractor()

    def get_middlewares(self) -> list[BaseMiddleware]:
        middlewares: list[BaseMiddleware] = []

        if self.config.sign_key:
            sign_middleware = XHSSignMiddleware(
                {"sign_key": self.config.sign_key},
            )
            middlewares.append(sign_middleware)

        if self.config.cookie:
            cookie_middleware = XHSCookieMiddleware(
                {"cookie_pool": [self.config.cookie]},
            )
            middlewares.append(cookie_middleware)

        return middlewares

    def get_pipelines(self) -> list[BasePipeline]:
        return []
