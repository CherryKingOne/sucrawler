from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("mysql")
class MySQLStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.host: str = self.config.get("host", "localhost")
        self.port: int = self.config.get("port", 3306)
        self.user: str = self.config.get("user", "root")
        self.password: str = self.config.get("password", "")
        self.database: str = self.config.get("database", "crawler")
        logger.info("MySQL storage initialized (async implementation using asyncmy)")

    async def save(self, item: Item) -> bool:
        logger.warning("MySQLStorage.save not implemented yet")
        msg = "MySQL storage save method not implemented"
        raise StorageException(msg)

    async def save_batch(self, items: list[Item]) -> int:
        logger.warning("MySQLStorage.save_batch not implemented yet")
        msg = "MySQL storage save_batch method not implemented"
        raise StorageException(msg)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("MySQLStorage.query not implemented yet")
        msg = "MySQL storage query method not implemented"
        raise StorageException(msg)

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("MySQLStorage.update not implemented yet")
        msg = "MySQL storage update method not implemented"
        raise StorageException(msg)

    async def delete(self, item_id: str) -> bool:
        logger.warning("MySQLStorage.delete not implemented yet")
        msg = "MySQL storage delete method not implemented"
        raise StorageException(msg)
