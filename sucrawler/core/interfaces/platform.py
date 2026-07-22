from abc import ABC, abstractmethod
from typing import Any

from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.interfaces.pipeline import BasePipeline


class BasePlatform(ABC):
    name: str
    config: Any

    def __init__(self, config: Any = None) -> None:
        self.config = config or {}

    @abstractmethod
    def create_downloader(self) -> BaseDownloader: ...

    @abstractmethod
    def create_parser(self) -> BaseParser: ...

    @abstractmethod
    def create_extractor(self) -> BaseExtractor: ...

    @abstractmethod
    def get_middlewares(self) -> list[BaseMiddleware]: ...

    @abstractmethod
    def get_pipelines(self) -> list[BasePipeline]: ...
