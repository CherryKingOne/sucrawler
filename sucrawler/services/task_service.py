from typing import Any

from loguru import logger

from sucrawler.common.types import TaskId
from sucrawler.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, task_repository: TaskRepository) -> None:
        self._repo = task_repository
        logger.info("TaskService initialized")

    async def create_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"Creating task: {task_data.get('name', 'unnamed')}")
        task = await self._repo.create(task_data)
        logger.info(f"Task created: {task.get('id')}")
        return task

    async def get_task(self, task_id: TaskId) -> dict[str, Any] | None:
        logger.debug(f"Getting task: {task_id}")
        return await self._repo.get_by_id(task_id)

    async def list_tasks(self, condition: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        logger.debug(f"Listing tasks with condition: {condition}")
        return await self._repo.list(condition or {})

    async def update_task(self, task_id: TaskId, data: dict[str, Any]) -> bool:
        logger.info(f"Updating task: {task_id}")
        result = await self._repo.update(task_id, data)
        if result:
            logger.info(f"Task updated: {task_id}")
        else:
            logger.warning(f"Task not found: {task_id}")
        return result

    async def delete_task(self, task_id: TaskId) -> bool:
        logger.info(f"Deleting task: {task_id}")
        result = await self._repo.delete(task_id)
        if result:
            logger.info(f"Task deleted: {task_id}")
        else:
            logger.warning(f"Task not found: {task_id}")
        return result
