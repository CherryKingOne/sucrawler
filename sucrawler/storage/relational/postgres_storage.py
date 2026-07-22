from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("postgres")
class PostgreSQLStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.host: str = self.config.get("host", "localhost")
        self.port: int = self.config.get("port", 5432)
        self.user: str = self.config.get("user", "postgres")
        self.password: str = self.config.get("password", "")
        self.database: str = self.config.get("database", "crawler")
        logger.info("PostgreSQL storage initialized (async implementation using asyncpg)")

    async def save(self, item: Item) -> bool:
        logger.warning("PostgreSQLStorage.save not implemented yet")
        msg = "PostgreSQL storage save method not implemented"
        raise StorageException(msg)

    async def save_batch(self, items: list[Item]) -> int:
        logger.warning("PostgreSQLStorage.save_batch not implemented yet")
        msg = "PostgreSQL storage save_batch method not implemented"
        raise StorageException(msg)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("PostgreSQLStorage.query not implemented yet")
        msg = "PostgreSQL storage query method not implemented"
        raise StorageException(msg)

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("PostgreSQLStorage.update not implemented yet")
        msg = "PostgreSQL storage update method not implemented"
        raise StorageException(msg)

    async def delete(self, item_id: str) -> bool:
        logger.warning("PostgreSQLStorage.delete not implemented yet")
        msg = "PostgreSQL storage delete method not implemented"
        raise StorageException(msg)
