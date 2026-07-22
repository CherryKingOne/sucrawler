from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sucrawler.config.loader import load_config
from sucrawler.core.engine import CrawlerEngine
from sucrawler.core.request import Request
from sucrawler.core.spider import Task
from sucrawler.platforms.registry import get_platform_registry
from sucrawler.scheduler.memory_scheduler import MemoryScheduler
from sucrawler.services.crawler_service import CrawlerService
from sucrawler.storage.registry import get_storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a spider task")
    parser.add_argument(
        "--platform",
        "-p",
        type=str,
        required=True,
        help="Platform name (e.g., xiaohongshu)",
    )
    parser.add_argument(
        "--spider-type",
        "-t",
        type=str,
        default="detail",
        help="Spider type (e.g., detail, search, list)",
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        help="URL to crawl",
    )
    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        help="Keyword to search",
    )
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="dev",
        help="Environment (dev, test, prod)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Config directory path",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if not args.url and not args.keyword:
        print("Error: Either --url or --keyword must be provided")
        sys.exit(1)

    config = load_config(config_path=args.config, env=args.env)

    scheduler = MemoryScheduler(config.scheduler)
    default_backend = config.storage.default_backend
    storage = get_storage(default_backend, config.storage.backends[default_backend])
    platform_registry = get_platform_registry()

    engine = CrawlerEngine(
        scheduler=scheduler,
        platform_registry=platform_registry,
        event_bus=None,
        storage=storage,
        config=config,
    )

    service = CrawlerService(engine)

    url = args.url or f"https://www.xiaohongshu.com/search_result?keyword={args.keyword}"
    request = Request(url=url, meta={"platform": args.platform, "spider_type": args.spider_type})
    task = Task(
        task_id=f"{args.platform}-{args.spider_type}-{id(request)}",
        request=request,
        meta={"platform": args.platform},
    )

    result = await service.crawl(task)

    print(f"Task completed: {result.task_id}")
    print(f"Success: {result.success}")
    print(f"Items count: {result.items_count}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"Duration: {result.duration:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
