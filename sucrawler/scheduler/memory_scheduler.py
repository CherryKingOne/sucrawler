import asyncio
from typing import Any

from sucrawler.core.interfaces.scheduler import BaseScheduler
from sucrawler.core.spider import Task, TaskStatus
from sucrawler.scheduler.bloom_filter import BloomFilter
from sucrawler.scheduler.priority_queue import PriorityQueue


class MemoryScheduler(BaseScheduler):
    def __init__(
        self,
        bloom_capacity: int = 100000,
        bloom_error_rate: float = 0.01,
    ) -> None:
        self._queue: PriorityQueue[Task] = PriorityQueue()
        self._seen: BloomFilter = BloomFilter(bloom_capacity, bloom_error_rate)
        self._all_urls: set[str] = set()
        self._pending_count: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def add_task(self, task: Task) -> None:
        async with self._lock:
            url = task.request.url
            if self._seen.contains(url):
                return
            self._seen.add(url)
            self._all_urls.add(url)
            priority = self._get_priority(task)
            await self._queue.push(task, priority)
            self._pending_count += 1

    async def add_tasks(self, tasks: list[Task]) -> None:
        for task in tasks:
            await self.add_task(task)

    async def get_next_task(self) -> Task | None:
        async with self._lock:
            if self._queue.empty():
                return None
            task = await self._queue.pop()
            self._pending_count -= 1
            task.status = TaskStatus.RUNNING
            return task

    async def has_more(self) -> bool:
        async with self._lock:
            return self._pending_count > 0

    async def mark_done(self, task: Task) -> None:
        async with self._lock:
            task.status = TaskStatus.DONE

    async def mark_failed(self, task: Task, reason: str) -> None:
        async with self._lock:
            task.status = TaskStatus.FAILED
            task.error = reason

    async def size(self) -> int:
        async with self._lock:
            return self._pending_count

    def _get_priority(self, task: Task) -> int:
        meta: dict[str, Any] = task.meta or {}
        priority = meta.get("priority", 0)
        return int(priority)
