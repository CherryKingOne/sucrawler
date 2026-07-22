from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from sucrawler.common.types import TaskId
from sucrawler.core.item import Item
from sucrawler.core.request import Request
from sucrawler.core.response import Response
from sucrawler.core.spider import Task
from sucrawler.models.base import BaseModel

if TYPE_CHECKING:
    from sucrawler.core.interfaces.downloader import BaseDownloader
    from sucrawler.core.interfaces.extractor import BaseExtractor
    from sucrawler.core.interfaces.middleware import BaseMiddleware
    from sucrawler.core.interfaces.parser import BaseParser
    from sucrawler.core.interfaces.pipeline import BasePipeline
    from sucrawler.core.interfaces.platform import BasePlatform
    from sucrawler.core.interfaces.scheduler import BaseScheduler
    from sucrawler.core.interfaces.storage import BaseStorage


@runtime_checkable
class PlatformRegistry(Protocol):
    def get(self, name: str) -> Any: ...


class CrawlResult(BaseModel):
    task_id: TaskId
    success: bool
    items_count: int = 0
    error: str | None = None
    duration: float = 0.0


class CrawlerEngine:
    def __init__(
        self,
        scheduler: BaseScheduler,
        platform_registry: PlatformRegistry,
        event_bus: Any,
        storage: BaseStorage,
        config: Any,
    ) -> None:
        self._scheduler = scheduler
        self._platform_registry = platform_registry
        self._event_bus = event_bus
        self._storage = storage
        self._config = config
        self._paused: bool = False
        self._stopped: bool = False
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()

    async def run(self, task: Task) -> CrawlResult:
        start_time = time.perf_counter()

        try:
            await self._wait_if_paused()
            if self._stopped:
                return CrawlResult(
                    task_id=task.task_id,
                    success=False,
                    error="Engine stopped",
                    duration=time.perf_counter() - start_time,
                )

            platform = self._get_platform(task)
            items = await self._crawl_task(platform, task)

            if items:
                await self._storage.save_batch(items)

            await self._scheduler.mark_done(task)

            return CrawlResult(
                task_id=task.task_id,
                success=True,
                items_count=len(items),
                duration=time.perf_counter() - start_time,
            )
        except Exception as e:
            error_msg = str(e)
            await self._scheduler.mark_failed(task, error_msg)
            return CrawlResult(
                task_id=task.task_id,
                success=False,
                error=error_msg,
                duration=time.perf_counter() - start_time,
            )

    async def run_batch(self, tasks: list[Task]) -> list[CrawlResult]:
        await self._scheduler.add_tasks(tasks)
        results: list[CrawlResult] = []

        while await self._scheduler.has_more():
            if self._stopped:
                break
            await self._wait_if_paused()

            task = await self._scheduler.get_next_task()
            if task is None:
                break

            result = await self.run(task)
            results.append(result)

        return results

    async def pause(self) -> None:
        self._paused = True
        self._pause_event.clear()

    async def resume(self) -> None:
        self._paused = False
        self._pause_event.set()

    async def stop(self) -> None:
        self._stopped = True
        self._pause_event.set()

    def _get_platform(self, task: Task) -> BasePlatform:
        platform_name = task.meta.get("platform") if task.meta else None
        if not platform_name:
            raise ValueError("Task meta must contain 'platform' key")
        platform: BasePlatform = self._platform_registry.get(platform_name)
        return platform

    async def _crawl_task(self, platform: BasePlatform, task: Task) -> list[Item]:
        downloader: BaseDownloader = platform.create_downloader()
        parser: BaseParser = platform.create_parser()
        extractor: BaseExtractor = platform.create_extractor()
        middlewares: list[BaseMiddleware] = platform.get_middlewares()
        pipelines: list[BasePipeline] = platform.get_pipelines()

        request = await self._apply_request_middlewares(task.request, middlewares)

        try:
            response = await downloader.fetch(request)
        except Exception as e:
            await self._apply_exception_middlewares(request, e, middlewares)
            raise

        response = await self._apply_response_middlewares(request, response, middlewares)

        data = await parser.parse(response)
        items = await extractor.extract(data)
        items = await self._apply_pipelines(items, pipelines)

        return items

    async def _apply_request_middlewares(
        self,
        request: Request,
        middlewares: list[BaseMiddleware],
    ) -> Request:
        current = request
        for middleware in middlewares:
            current = await middleware.process_request(current)
        return current

    async def _apply_response_middlewares(
        self,
        request: Request,
        response: Response,
        middlewares: list[BaseMiddleware],
    ) -> Response:
        current = response
        for middleware in reversed(middlewares):
            current = await middleware.process_response(request, current)
        return current

    async def _apply_exception_middlewares(
        self,
        request: Request,
        exception: Exception,
        middlewares: list[BaseMiddleware],
    ) -> None:
        for middleware in middlewares:
            await middleware.process_exception(request, exception)

    async def _apply_pipelines(
        self,
        items: list[Item],
        pipelines: list[BasePipeline],
    ) -> list[Item]:
        result: list[Item] = []
        for item in items:
            current = item
            for pipeline in pipelines:
                current = await pipeline.process_item(current)
            result.append(current)
        return result

    async def _wait_if_paused(self) -> None:
        await self._pause_event.wait()
