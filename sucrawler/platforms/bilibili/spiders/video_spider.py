from __future__ import annotations

from loguru import logger

from sucrawler.platforms.bilibili.api.video_api import BiliVideoApi
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.downloader import BiliDownloader
from sucrawler.platforms.bilibili.extractor import BiliExtractor
from sucrawler.platforms.bilibili.models.video import BiliVideoItem
from sucrawler.platforms.bilibili.parser import BiliParser


class BiliVideoSpider:
    def __init__(self, config: BiliConfig) -> None:
        self.config = config
        self.downloader = BiliDownloader(config)
        self.parser = BiliParser()
        self.extractor = BiliExtractor()
        self.video_api = BiliVideoApi(config, self.downloader)

    async def crawl_video_info(self, bvid: str) -> BiliVideoItem | None:
        logger.info(f"Crawling video info: {bvid}")
        try:
            data = await self.video_api.get_video_info(bvid)
            if not data:
                logger.warning(f"No data returned for video: {bvid}")
                return None

            tags = await self.video_api.get_video_tags(bvid)
            if tags:
                data["tags"] = tags

            videos = self.extractor.extract_videos({"data": [data]})
            if videos:
                return videos[0]
            return None
        except Exception as e:
            logger.error(f"Error crawling video {bvid}: {e}")
            return None

    async def search_videos(
        self,
        keyword: str,
        max_count: int = 0,
    ) -> list[BiliVideoItem]:
        fetch_all = max_count <= 0
        log_msg = f"Searching videos: {keyword}"
        log_msg += ", fetch all" if fetch_all else f", max_count: {max_count}"
        logger.info(log_msg)

        all_videos: list[BiliVideoItem] = []
        page = 1
        page_size = 30

        while True:
            try:
                result = await self.video_api.search_videos(keyword, page, page_size)
                if not result:
                    break

                results = result.get("result", [])
                if not results:
                    logger.info("No more search results")
                    break

                videos = self.extractor.extract_videos({"vlist": results})
                all_videos.extend(videos)
                logger.info(
                    f"Page {page}: got {len(videos)} videos (total: {len(all_videos)})",
                )

                if not fetch_all and len(all_videos) >= max_count:
                    logger.info(f"Reached max_count: {max_count}")
                    break

                num_results = int(result.get("numResults", 0))
                num_pages = int(result.get("numPages", 0))
                if num_pages > 0 and page >= num_pages:
                    logger.info("All pages crawled")
                    break

                if len(results) < page_size:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error searching videos page {page}: {e}")
                break

        if max_count > 0:
            return all_videos[:max_count]
        return all_videos

    async def close(self) -> None:
        await self.downloader.close()
