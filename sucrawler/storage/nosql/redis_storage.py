from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("redis")
class RedisStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.host: str = self.config.get("host", "localhost")
        self.port: int = self.config.get("port", 6379)
        self.db: int = self.config.get("db", 0)
        self.password: str = self.config.get("password", "")
        self.key_prefix: str = self.config.get("key_prefix", "crawler:item:")
        logger.info("Redis storage initialized (async implementation using redis-py async)")

    async def save(self, item: Item) -> bool:
        logger.warning("RedisStorage.save not implemented yet")
        msg = "Redis storage save method not implemented"
        raise StorageException(msg)

    async def save_batch(self, items: list[Item]) -> int:
        logger.warning("RedisStorage.save_batch not implemented yet")
        msg = "Redis storage save_batch method not implemented"
        raise StorageException(msg)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("RedisStorage.query not implemented yet")
        msg = "Redis storage query method not implemented"
        raise StorageException(msg)

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("RedisStorage.update not implemented yet")
        msg = "Redis storage update method not implemented"
        raise StorageException(msg)

    async def delete(self, item_id: str) -> bool:
        logger.warning("RedisStorage.delete not implemented yet")
        msg = "Redis storage delete method not implemented"
        raise StorageException(msg)
