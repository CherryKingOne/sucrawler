from abc import ABC, abstractmethod

from sucrawler.core.request import Request
from sucrawler.core.response import Response


class BaseDownloader(ABC):
    @abstractmethod
    async def fetch(self, request: Request) -> Response: ...

    @abstractmethod
    async def fetch_batch(self, requests: list[Request]) -> list[Response]: ...
