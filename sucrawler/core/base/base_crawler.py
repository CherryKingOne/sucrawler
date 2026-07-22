from __future__ import annotations

from typing import Any

from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.interfaces.pipeline import BasePipeline
from sucrawler.core.item import Item
from sucrawler.core.request import Request


class BaseCrawler:
    def __init__(
        self,
        downloader: BaseDownloader,
        parser: BaseParser,
        extractor: BaseExtractor,
        middlewares: list[BaseMiddleware] | None = None,
        pipelines: list[BasePipeline] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.downloader = downloader
        self.parser = parser
        self.extractor = extractor
        self.middlewares = middlewares or []
        self.pipelines = pipelines or []
        self.config = config or {}

    async def crawl(self, request: Request) -> list[Item]:
        current_request = request

        for middleware in self.middlewares:
            current_request = await middleware.process_request(current_request)

        try:
            response = await self.downloader.fetch(current_request)
        except Exception as e:
            for middleware in self.middlewares:
                await middleware.process_exception(current_request, e)
            raise

        for middleware in self.middlewares:
            response = await middleware.process_response(current_request, response)

        data = await self.parser.parse(response)
        items = await self.extractor.extract(data)

        processed_items: list[Item] = []
        for item in items:
            current_item = item
            for pipeline in self.pipelines:
                current_item = await pipeline.process_item(current_item)
            processed_items.append(current_item)

        return processed_items
