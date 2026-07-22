
from loguru import logger

from sucrawler.core.engine import CrawlerEngine, CrawlResult
from sucrawler.core.spider import Task


class CrawlerService:
    def __init__(self, engine: CrawlerEngine) -> None:
        self._engine = engine
        logger.info("CrawlerService initialized")

    async def crawl(self, task: Task) -> CrawlResult:
        logger.info(f"Starting crawl for task: {task.task_id}")
        result = await self._engine.run(task)
        if result.success:
            logger.info(f"Crawl completed: {task.task_id}, items: {result.items_count}")
        else:
            logger.error(f"Crawl failed: {task.task_id}, error: {result.error}")
        return result

    async def crawl_batch(self, tasks: list[Task]) -> list[CrawlResult]:
        logger.info(f"Starting batch crawl with {len(tasks)} tasks")
        results = await self._engine.run_batch(tasks)
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch crawl completed: {success_count}/{len(results)} succeeded")
        return results

    async def pause(self) -> None:
        logger.info("Pausing crawler")
        await self._engine.pause()

    async def resume(self) -> None:
        logger.info("Resuming crawler")
        await self._engine.resume()

    async def stop(self) -> None:
        logger.info("Stopping crawler")
        await self._engine.stop()
