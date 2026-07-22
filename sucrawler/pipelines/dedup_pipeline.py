from __future__ import annotations

import hashlib
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import PipelineException
from sucrawler.core.base.base_pipeline import BasePipelineImpl
from sucrawler.core.item import Item
from sucrawler.scheduler.bloom_filter import BloomFilter


class DedupPipeline(BasePipelineImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.use_bloom_filter: bool = self.config.get("use_bloom_filter", False)
        self.id_fields: list[str] = self.config.get("id_fields", [])
        self.bloom_capacity: int = self.config.get("bloom_capacity", 100000)
        self.bloom_error_rate: float = self.config.get("bloom_error_rate", 0.001)
        self.discard_duplicates: bool = self.config.get("discard_duplicates", True)

        self._seen_ids: set[str] = set()
        self._bloom_filter: BloomFilter | None = None
        self._duplicate_count: int = 0

    async def open_spider(self, spider: Any) -> None:
        logger.info("Opening DedupPipeline")
        self._seen_ids = set()
        self._duplicate_count = 0
        if self.use_bloom_filter:
            self._bloom_filter = BloomFilter(
                capacity=self.bloom_capacity,
                error_rate=self.bloom_error_rate,
            )
            logger.info(
                f"Bloom filter initialized with capacity={self.bloom_capacity}, "
                f"error_rate={self.bloom_error_rate}"
            )

    async def close_spider(self, spider: Any) -> None:
        logger.info(
            f"Closing DedupPipeline - seen {len(self._seen_ids)} unique, "
            f"{self._duplicate_count} duplicates"
        )

    async def process_item(self, item: Item) -> Item:
        item_id = self._get_item_id(item)

        if item_id is None:
            logger.debug("Item has no ID, skipping deduplication")
            return item

        if self._is_duplicate(item_id):
            self._duplicate_count += 1
            logger.debug(f"Duplicate item found: {item_id}")
            if self.discard_duplicates:
                msg = f"Duplicate item: {item_id}"
                raise DropItemException(msg)
            return item

        self._mark_seen(item_id)
        item.id = item_id
        return item

    def _get_item_id(self, item: Item) -> str | None:
        if item.id:
            return item.id

        if not self.id_fields or not item.raw_data:
            return None

        values: list[str] = []
        for field in self.id_fields:
            value = item.raw_data.get(field)
            if value is not None:
                values.append(str(value))

        if not values:
            return None

        raw_id = "|".join(values)
        return hashlib.md5(raw_id.encode()).hexdigest()

    def _is_duplicate(self, item_id: str) -> bool:
        if self.use_bloom_filter and self._bloom_filter:
            return self._bloom_filter.contains(item_id) and item_id in self._seen_ids
        return item_id in self._seen_ids

    def _mark_seen(self, item_id: str) -> None:
        self._seen_ids.add(item_id)
        if self.use_bloom_filter and self._bloom_filter:
            self._bloom_filter.add(item_id)


class DropItemException(PipelineException):  # noqa: N818
    pass
