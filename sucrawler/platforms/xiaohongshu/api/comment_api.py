from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.downloader import XHSDownloader


class XHSCommentApi:
    def __init__(self, config: XHSConfig, downloader: XHSDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def get_comments(
        self,
        note_id: str,
        cursor: str = "",
    ) -> list[dict[str, Any]]:
        logger.info(f"Getting comments for note: {note_id}, cursor: {cursor}")
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

    async def get_sub_comments(
        self,
        comment_id: str,
        cursor: str = "",
    ) -> list[dict[str, Any]]:
        logger.info(f"Getting sub comments for: {comment_id}, cursor: {cursor}")
        url = f"{self.config.api_url}/comment/sub/page"
        params = {
            "comment_id": comment_id,
            "cursor": cursor,
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

        sub_comments = inner_data.get("sub_comments", [])
        return cast(
            list[dict[str, Any]],
            sub_comments if isinstance(sub_comments, list) else [],
        )
