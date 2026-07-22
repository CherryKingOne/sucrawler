from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.interfaces.pipeline import BasePipeline
from sucrawler.core.interfaces.platform import BasePlatform
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.downloader import BiliDownloader
from sucrawler.platforms.bilibili.extractor import BiliExtractor
from sucrawler.platforms.bilibili.middlewares import (
    BiliCookieMiddleware,
    BiliWbiMiddleware,
)
from sucrawler.platforms.bilibili.parser import BiliParser
from sucrawler.platforms.registry import register_platform


@register_platform("bilibili")
class BilibiliPlatform(BasePlatform):
    name = "bilibili"

    def __init__(self, config: Any = None) -> None:
        if isinstance(config, BiliConfig):
            self.config = config
        elif isinstance(config, dict):
            self.config = BiliConfig(**config)
        else:
            self.config = BiliConfig()
        logger.info(f"Initialized {self.name} platform")

    def create_downloader(self) -> BaseDownloader:
        return BiliDownloader(self.config)

    def create_parser(self) -> BaseParser:
        return BiliParser()

    def create_extractor(self) -> BaseExtractor:
        return BiliExtractor()

    def get_middlewares(self) -> list[BaseMiddleware]:
        middlewares: list[BaseMiddleware] = []

        if self.config.cookie:
            cookie_middleware = BiliCookieMiddleware(
                {"cookie_pool": [self.config.cookie]},
            )
            middlewares.append(cookie_middleware)

        return middlewares

    def get_pipelines(self) -> list[BasePipeline]:
        return []
