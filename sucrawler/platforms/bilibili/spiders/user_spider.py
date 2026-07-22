from __future__ import annotations

import asyncio

from loguru import logger

from sucrawler.platforms.bilibili.api.user_api import BiliUserApi
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.downloader import BiliDownloader
from sucrawler.platforms.bilibili.extractor import BiliExtractor
from sucrawler.platforms.bilibili.models.user import BiliUserItem
from sucrawler.platforms.bilibili.models.video import BiliVideoItem
from sucrawler.platforms.bilibili.parser import BiliParser


class BiliUserSpider:
    def __init__(self, config: BiliConfig) -> None:
        self.config = config
        self.downloader = BiliDownloader(config)
        self.parser = BiliParser()
        self.extractor = BiliExtractor()
        self.user_api = BiliUserApi(config, self.downloader)

    async def crawl_user_info(self, mid: str) -> BiliUserItem | None:
        logger.info(f"Crawling user info: {mid}")
        try:
            data = await self.user_api.get_user_info(mid)
            if not data:
                logger.warning(f"No data returned for user: {mid}")
                return None

            users = self.extractor.extract_users({"data": [data]})
            if users:
                user = users[0]

                stat = await self.user_api.get_user_stat(mid)
                if stat:
                    user.fans = int(stat.get("follower", user.fans))
                    user.following = int(stat.get("following", user.following))

                return user
            return None
        except Exception as e:
            logger.error(f"Error crawling user {mid}: {e}")
            return None

    async def crawl_user_videos(
        self,
        mid: str,
        max_count: int = 0,
    ) -> list[BiliVideoItem]:
        fetch_all = max_count <= 0
        log_msg = f"Crawling user videos: {mid}"
        log_msg += ", fetch all" if fetch_all else f", max_count: {max_count}"
        logger.info(log_msg)

        all_videos: list[BiliVideoItem] = []
        page = 1
        page_size = 30
        consecutive_empty = 0

        while True:
            try:
                result = await self.user_api.get_user_videos(mid, page, page_size)
                if not result:
                    logger.warning(f"No data returned for page {page}")
                    break

                vlist = result.get("list", {}).get("vlist", [])
                if not vlist:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        logger.info("No more videos, stopping")
                        break
                    page += 1
                    continue

                consecutive_empty = 0
                videos = self.extractor.extract_videos({"vlist": vlist})
                all_videos.extend(videos)
                logger.info(
                    f"Page {page}: got {len(videos)} videos (total: {len(all_videos)})",
                )

                if not fetch_all and len(all_videos) >= max_count:
                    logger.info(f"Reached max_count: {max_count}")
                    break

                page_info = result.get("page", {})
                count = int(page_info.get("count", 0))
                if count > 0 and len(all_videos) >= count:
                    logger.info(f"All {count} videos crawled")
                    break

                if len(vlist) < page_size:
                    logger.info("Last page reached")
                    break

                page += 1
                await asyncio.sleep(self.config.rate_limit)

            except Exception as e:
                logger.error(f"Error crawling user videos page {page}: {e}")
                break

        if max_count > 0:
            return all_videos[:max_count]
        return all_videos

    async def close(self) -> None:
        await self.downloader.close()
