from typing import Any

from loguru import logger

from sucrawler.common.types import ItemId
from sucrawler.core.item import Item
from sucrawler.repositories.data_repository import DataRepository


class DataService:
    def __init__(self, data_repository: DataRepository) -> None:
        self._repo = data_repository
        logger.info("DataService initialized")

    async def save_item(self, item: Item) -> bool:
        logger.debug(f"Saving item: {item.id}")
        return await self._repo.save(item)

    async def save_items(self, items: list[Item]) -> int:
        logger.info(f"Saving {len(items)} items")
        count = await self._repo.save_batch(items)
        logger.info(f"Saved {count} items")
        return count

    async def get_item(self, item_id: ItemId) -> Item | None:
        logger.debug(f"Getting item: {item_id}")
        items = await self._repo.query({"id": item_id})
        return items[0] if items else None

    async def query_items(self, condition: dict[str, Any]) -> list[Item]:
        logger.debug(f"Querying items with condition: {condition}")
        return await self._repo.query(condition)

    async def update_item(self, item_id: ItemId, data: dict[str, Any]) -> bool:
        logger.info(f"Updating item: {item_id}")
        return await self._repo.update(item_id, data)

    async def delete_item(self, item_id: ItemId) -> bool:
        logger.info(f"Deleting item: {item_id}")
        return await self._repo.delete(item_id)
