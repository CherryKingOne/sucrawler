from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sucrawler.core.spider import Task


class BaseScheduler(ABC):
    @abstractmethod
    async def add_task(self, task: "Task") -> None: ...

    @abstractmethod
    async def add_tasks(self, tasks: list["Task"]) -> None: ...

    @abstractmethod
    async def get_next_task(self) -> "Task | None": ...

    @abstractmethod
    async def has_more(self) -> bool: ...

    @abstractmethod
    async def mark_done(self, task: "Task") -> None: ...

    @abstractmethod
    async def mark_failed(self, task: "Task", reason: str) -> None: ...

    @abstractmethod
    async def size(self) -> int: ...
