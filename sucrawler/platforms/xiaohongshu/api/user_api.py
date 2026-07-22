from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader


class XHSUserApi:
    def __init__(self, config: XHSConfig, downloader: XHSDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        logger.info(f"Getting user info: {user_id}")
        url = f"{self.config.api_url}/user/profile"
        params = {"user_id": user_id}

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return {}

        data = response.json()
        if not isinstance(data, dict):
            return {}

        data_dict = cast(dict[str, Any], data)
        user_data = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            user_data if isinstance(user_data, dict) else {},
        )

    async def get_user_notes(
        self,
        user_id: str,
        cursor: str = "",
    ) -> list[dict[str, Any]]:
        logger.info(f"Getting user notes: {user_id}, cursor: {cursor}")
        url = f"{self.config.api_url}/user/profile/notes"
        params = {
            "user_id": user_id,
            "cursor": cursor,
            "page_size": 20,
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
