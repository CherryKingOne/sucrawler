from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader


class XHSSearchApi:
    def __init__(self, config: XHSConfig, downloader: XHSDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def search(
        self,
        keyword: str,
        search_type: str = "normal",
        page: int = 1,
    ) -> list[dict[str, Any]]:
        logger.info(
            f"Searching: {keyword}, type: {search_type}, page: {page}",
        )
        url = f"{self.config.api_url}/search/notes"
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": 20,
            "search_type": search_type,
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
