from abc import ABC, abstractmethod
from typing import Any

from sucrawler.core.item import Item


class BaseStorage(ABC):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def save(self, item: Item) -> bool: ...

    @abstractmethod
    async def save_batch(self, items: list[Item]) -> int: ...

    @abstractmethod
    async def query(self, condition: dict[str, Any]) -> list[Item]: ...

    @abstractmethod
    async def update(self, item_id: str, data: dict[str, Any]) -> bool: ...

    @abstractmethod
    async def delete(self, item_id: str) -> bool: ...
