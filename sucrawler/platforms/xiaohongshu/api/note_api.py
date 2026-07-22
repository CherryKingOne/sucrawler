from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader


class XHSNoteApi:
    def __init__(self, config: XHSConfig, downloader: XHSDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def get_note_detail(self, note_id: str) -> dict[str, Any]:
        logger.info(f"Getting note detail: {note_id}")
        url = f"{self.config.api_url}/feed/note_detail"
        params = {"note_id": note_id, "source": "explore_feed"}

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return {}

        data = response.json()
        return cast(dict[str, Any], data if isinstance(data, dict) else {})

    async def search_note(self, keyword: str, page: int = 1) -> list[dict[str, Any]]:
        logger.info(f"Searching notes: {keyword}, page: {page}")
        url = f"{self.config.api_url}/search/notes"
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": 20,
            "search_type": "normal",
        }

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return []

        data = response.json()
        if not isinstance(data, dict):
            return []

        data_dict = cast(dict[str, Any], data)
        inner_data = data_dict.get("data", {})
        if not isinstance(inner_data, dict):
            return []

        notes = inner_data.get("notes", [])
        return cast(list[dict[str, Any]], notes if isinstance(notes, list) else [])

    async def get_note_comments(
        self,
        note_id: str,
        cursor: str = "",
    ) -> list[dict[str, Any]]:
        logger.info(f"Getting note comments: {note_id}, cursor: {cursor}")
        url = f"{self.config.api_url}/comment/page"
        params = {
            "note_id": note_id,
            "cursor": cursor,
            "top_comment_id": "",
            "image_formats": "jpg,webp,avif",
        }

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return []

        data = response.json()
        if not isinstance(data, dict):
            return []

        data_dict = cast(dict[str, Any], data)
        inner_data = data_dict.get("data", {})
        if not isinstance(inner_data, dict):
            return []

        comments = inner_data.get("comments", [])
        return cast(
            list[dict[str, Any]],
            comments if isinstance(comments, list) else [],
        )
