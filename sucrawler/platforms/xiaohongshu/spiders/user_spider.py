from __future__ import annotations

from loguru import logger

from sucrawler.platforms.xiaohongshu.api.user_api import XHSUserApi
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader
from sucrawler.platforms.xiaohongshu.extractor import XHSExtractor
from sucrawler.platforms.xiaohongshu.models.note import XHSNoteItem
from sucrawler.platforms.xiaohongshu.models.user import XHSUserItem
from sucrawler.platforms.xiaohongshu.parser import XHSParser


class XHSUserSpider:
    def __init__(self, config: XHSConfig) -> None:
        self.config = config
        self.downloader = XHSDownloader(config)
        self.parser = XHSParser()
        self.extractor = XHSExtractor()
        self.user_api = XHSUserApi(config, self.downloader)

    async def crawl_user_info(self, user_id: str) -> XHSUserItem | None:
        logger.info(f"Crawling user info: {user_id}")
        try:
            data = await self.user_api.get_user_info(user_id)
            if not data:
                logger.warning(f"No data returned for user: {user_id}")
                return None

            users = self.extractor.extract_users({"data": [data]})
            if users:
                return users[0]
            return None
        except Exception as e:
            logger.error(f"Error crawling user {user_id}: {e}")
            return None

    async def crawl_user_notes(
        self,
        user_id: str,
        max_count: int = 100,
    ) -> list[XHSNoteItem]:
        logger.info(f"Crawling user notes: {user_id}, max_count: {max_count}")
        all_notes: list[XHSNoteItem] = []
        cursor: str = ""

        while len(all_notes) < max_count:
            try:
                raw_notes = await self.user_api.get_user_notes(user_id, cursor)
                if not raw_notes:
                    logger.info("No more notes, stopping")
                    break

                notes = self.extractor.extract_notes({"notes": raw_notes})
                all_notes.extend(notes)
                logger.info(
                    f"Got {len(notes)} notes, total: {len(all_notes)}",
                )

                if len(raw_notes) < 20:
                    break

                cursor = str(len(all_notes))
            except Exception as e:
                logger.error(f"Error crawling user notes: {e}")
                break

        return all_notes[:max_count]

    async def close(self) -> None:
        await self.downloader.close()
