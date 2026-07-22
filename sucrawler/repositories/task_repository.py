from datetime import datetime
from typing import Any
from uuid import uuid4

from loguru import logger

from sucrawler.common.types import TaskId
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item


class TaskRepository:
    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage
        logger.info("TaskRepository initialized")

    async def create(self, task_data: dict[str, Any]) -> dict[str, Any]:
        task_id = task_data.get("id") or str(uuid4())
        now = datetime.now()
        item = Item(
            id=task_id,
            platform="task",
            crawled_at=now,
            raw_data={
                **task_data,
                "id": task_id,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "status": task_data.get("status", "pending"),
            },
        )
        await self._storage.save(item)
        return item.raw_data or {}

    async def get_by_id(self, task_id: TaskId) -> dict[str, Any] | None:
        items = await self._storage.query({"id": task_id})
        if items:
            return items[0].raw_data
        return None

    async def list(self, condition: dict[str, Any]) -> list[dict[str, Any]]:
        items = await self._storage.query(condition)
        return [item.raw_data or {} for item in items]

    async def update(self, task_id: TaskId, data: dict[str, Any]) -> bool:
        existing = await self.get_by_id(task_id)
        if existing is None:
            return False
        updated_data = {**existing, **data, "updated_at": datetime.now().isoformat()}
        return await self._storage.update(task_id, {"raw_data": updated_data})

    async def delete(self, task_id: TaskId) -> bool:
        return await self._storage.delete(task_id)
