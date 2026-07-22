from typing import Any

from loguru import logger

from sucrawler.common.types import ItemId
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item


class DataRepository:
    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage
        logger.info("DataRepository initialized")

    async def save(self, item: Item) -> bool:
        return await self._storage.save(item)

    async def save_batch(self, items: list[Item]) -> int:
        return await self._storage.save_batch(items)

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        return await self._storage.query(condition)

    async def update(self, item_id: ItemId, data: dict[str, Any]) -> bool:
        return await self._storage.update(item_id, data)

    async def delete(self, item_id: ItemId) -> bool:
        return await self._storage.delete(item_id)
