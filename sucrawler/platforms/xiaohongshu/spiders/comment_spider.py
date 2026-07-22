from __future__ import annotations

from loguru import logger

from sucrawler.platforms.xiaohongshu.api.comment_api import XHSCommentApi
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader
from sucrawler.platforms.xiaohongshu.extractor import XHSExtractor
from sucrawler.platforms.xiaohongshu.models.comment import XHSCommentItem
from sucrawler.platforms.xiaohongshu.parser import XHSParser


class XHSCommentSpider:
    def __init__(self, config: XHSConfig) -> None:
        self.config = config
        self.downloader = XHSDownloader(config)
        self.parser = XHSParser()
        self.extractor = XHSExtractor()
        self.comment_api = XHSCommentApi(config, self.downloader)

    async def crawl_note_comments(
        self,
        note_id: str,
        max_count: int = 200,
    ) -> list[XHSCommentItem]:
        logger.info(
            f"Crawling comments for note: {note_id}, max_count: {max_count}",
        )
        all_comments: list[XHSCommentItem] = []
        cursor: str = ""

        while len(all_comments) < max_count:
            try:
                raw_comments = await self.comment_api.get_comments(note_id, cursor)
                if not raw_comments:
                    logger.info("No more comments, stopping")
                    break

                for raw_comment in raw_comments:
                    if isinstance(raw_comment, dict):
                        raw_comment["note_id"] = note_id

                comments = self.extractor.extract_comments({"comments": raw_comments})
                all_comments.extend(comments)
                logger.info(
                    f"Got {len(comments)} comments, total: {len(all_comments)}",
                )

                if len(raw_comments) < 20:
                    break

                cursor = str(len(all_comments))
            except Exception as e:
                logger.error(f"Error crawling comments: {e}")
                break

        return all_comments[:max_count]

    async def crawl_sub_comments(
        self,
        comment_id: str,
        max_count: int = 50,
    ) -> list[XHSCommentItem]:
        logger.info(
            f"Crawling sub comments for: {comment_id}, max_count: {max_count}",
        )
        all_comments: list[XHSCommentItem] = []
        cursor: str = ""

        while len(all_comments) < max_count:
            try:
                raw_comments = await self.comment_api.get_sub_comments(
                    comment_id,
                    cursor,
                )
                if not raw_comments:
                    logger.info("No more sub comments, stopping")
                    break

                for raw_comment in raw_comments:
                    if isinstance(raw_comment, dict):
                        raw_comment["parent_comment_id"] = comment_id

                comments = self.extractor.extract_comments({"comments": raw_comments})
                all_comments.extend(comments)
                logger.info(
                    f"Got {len(comments)} sub comments, total: {len(all_comments)}",
                )

                if len(raw_comments) < 20:
                    break

                cursor = str(len(all_comments))
            except Exception as e:
                logger.error(f"Error crawling sub comments: {e}")
                break

        return all_comments[:max_count]

    async def close(self) -> None:
        await self.downloader.close()
