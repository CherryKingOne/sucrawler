from abc import ABC, abstractmethod
from typing import Any

from sucrawler.core.item import Item


class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, data: dict[str, Any]) -> list[Item]: ...
