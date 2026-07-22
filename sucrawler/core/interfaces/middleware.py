from abc import ABC, abstractmethod

from sucrawler.core.request import Request
from sucrawler.core.response import Response


class BaseMiddleware(ABC):
    @abstractmethod
    async def process_request(self, request: Request) -> Request: ...

    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response: ...

    @abstractmethod
    async def process_exception(self, request: Request, exception: Exception) -> None: ...
