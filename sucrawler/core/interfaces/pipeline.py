from abc import ABC, abstractmethod
from typing import Any

from sucrawler.core.item import Item


class BasePipeline(ABC):
    @abstractmethod
    async def process_item(self, item: Item) -> Item: ...

    @abstractmethod
    async def open_spider(self, spider: Any) -> None: ...

    @abstractmethod
    async def close_spider(self, spider: Any) -> None: ...
