from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.downloader import BiliDownloader


class BiliVideoApi:
    def __init__(self, config: BiliConfig, downloader: BiliDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def get_video_info(self, bvid: str) -> dict[str, Any]:
        logger.info(f"Getting video info: {bvid}")
        url = f"{self.config.api_url}/x/web-interface/view"
        params = {"bvid": bvid}

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return {}

        data = response.json()
        if not isinstance(data, dict):
            return {}

        data_dict = cast(dict[str, Any], data)
        if data_dict.get("code") != 0:
            logger.warning(f"Get video info failed: {data_dict.get('message')}")
            return {}

        video_data = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            video_data if isinstance(video_data, dict) else {},
        )

    async def get_video_tags(self, bvid: str) -> list[dict[str, Any]]:
        logger.info(f"Getting video tags: {bvid}")
        url = f"{self.config.api_url}/x/tag/archive/tags"
        params = {"bvid": bvid}

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return []

        data = response.json()
        if not isinstance(data, dict):
            return []

        data_dict = cast(dict[str, Any], data)
        if data_dict.get("code") != 0:
            return []

        tags = data_dict.get("data", [])
        return cast(list[dict[str, Any]], tags if isinstance(tags, list) else [])

    async def search_videos(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 30,
    ) -> dict[str, Any]:
        logger.info(f"Searching videos: {keyword}, page: {page}")
        url = f"{self.config.api_url}/x/web-interface/search/type"
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
        }

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return {}

        data = response.json()
        if not isinstance(data, dict):
            return {}

        data_dict = cast(dict[str, Any], data)
        if data_dict.get("code") != 0:
            return {}

        result = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            result if isinstance(result, dict) else {},
        )
