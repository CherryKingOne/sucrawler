from __future__ import annotations

from loguru import logger

from sucrawler.platforms.xiaohongshu.api.note_api import XHSNoteApi
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader
from sucrawler.platforms.xiaohongshu.extractor import XHSExtractor
from sucrawler.platforms.xiaohongshu.models.note import XHSNoteItem
from sucrawler.platforms.xiaohongshu.parser import XHSParser


class XHSNoteSpider:
    def __init__(self, config: XHSConfig) -> None:
        self.config = config
        self.downloader = XHSDownloader(config)
        self.parser = XHSParser()
        self.extractor = XHSExtractor()
        self.note_api = XHSNoteApi(config, self.downloader)

    async def crawl_note_detail(self, note_id: str) -> XHSNoteItem | None:
        logger.info(f"Crawling note detail: {note_id}")
        try:
            data = await self.note_api.get_note_detail(note_id)
            if not data:
                logger.warning(f"No data returned for note: {note_id}")
                return None

            notes = self.extractor.extract_notes({"data": [data]})
            if notes:
                return notes[0]
            return None
        except Exception as e:
            logger.error(f"Error crawling note {note_id}: {e}")
            return None

    async def crawl_note_list(
        self,
        keyword: str,
        max_pages: int = 5,
    ) -> list[XHSNoteItem]:
        logger.info(f"Crawling note list for keyword: {keyword}, max_pages: {max_pages}")
        all_notes: list[XHSNoteItem] = []

        for page in range(1, max_pages + 1):
            try:
                raw_notes = await self.note_api.search_note(keyword, page)
                if not raw_notes:
                    logger.info(f"No more notes on page {page}, stopping")
                    break

                notes = self.extractor.extract_notes({"notes": raw_notes})
                all_notes.extend(notes)
                logger.info(
                    f"Page {page}: got {len(notes)} notes, total: {len(all_notes)}",
                )
            except Exception as e:
                logger.error(f"Error crawling page {page}: {e}")
                break

        return all_notes

    async def close(self) -> None:
        await self.downloader.close()
