from abc import ABC, abstractmethod
from typing import Any

from sucrawler.core.response import Response


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, response: Response) -> dict[str, Any]: ...
