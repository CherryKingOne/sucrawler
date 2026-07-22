from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("mongodb")
class MongoDBStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.host: str = self.config.get("host", "localhost")
        self.port: int = self.config.get("port", 27017)
        self.database: str = self.config.get("database", "crawler")
        self.collection: str = self.config.get("collection", "items")
        logger.info("MongoDB storage initialized (async implementation using motor)")

    async def save(self, item: Item) -> bool:
        logger.warning("MongoDBStorage.save not implemented yet")
        msg = "MongoDB storage save method not implemented"
        raise StorageException(msg)

    async def save_batch(self, items: list[Item]) -> int:
        logger.warning("MongoDBStorage.save_batch not implemented yet")
        msg = "MongoDB storage save_batch method not implemented"
        raise StorageException(msg)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("MongoDBStorage.query not implemented yet")
        msg = "MongoDB storage query method not implemented"
        raise StorageException(msg)

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("MongoDBStorage.update not implemented yet")
        msg = "MongoDB storage update method not implemented"
        raise StorageException(msg)

    async def delete(self, item_id: str) -> bool:
        logger.warning("MongoDBStorage.delete not implemented yet")
        msg = "MongoDB storage delete method not implemented"
        raise StorageException(msg)
