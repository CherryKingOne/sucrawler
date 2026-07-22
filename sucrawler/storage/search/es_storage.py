from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("elasticsearch")
class ElasticsearchStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.hosts: list[str] = self.config.get("hosts", ["http://localhost:9200"])
        self.index: str = self.config.get("index", "crawler_items")
        logger.info("Elasticsearch storage initialized")

    async def save(self, item: Item) -> bool:
        logger.warning("ElasticsearchStorage.save not implemented yet")
        msg = "Elasticsearch storage save method not implemented"
        raise StorageException(msg)

    async def save_batch(self, items: list[Item]) -> int:
        logger.warning("ElasticsearchStorage.save_batch not implemented yet")
        msg = "Elasticsearch storage save_batch method not implemented"
        raise StorageException(msg)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("ElasticsearchStorage.query not implemented yet")
        msg = "Elasticsearch storage query method not implemented"
        raise StorageException(msg)

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("ElasticsearchStorage.update not implemented yet")
        msg = "Elasticsearch storage update method not implemented"
        raise StorageException(msg)

    async def delete(self, item_id: str) -> bool:
        logger.warning("ElasticsearchStorage.delete not implemented yet")
        msg = "Elasticsearch storage delete method not implemented"
        raise StorageException(msg)
