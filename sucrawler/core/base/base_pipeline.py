from __future__ import annotations

from typing import Any

from sucrawler.core.interfaces.pipeline import BasePipeline
from sucrawler.core.item import Item


class BasePipelineImpl(BasePipeline):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def process_item(self, item: Item) -> Item:
        return item

    async def open_spider(self, spider: Any) -> None:
        return None

    async def close_spider(self, spider: Any) -> None:
        return None
