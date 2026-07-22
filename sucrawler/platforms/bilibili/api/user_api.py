from __future__ import annotations

from typing import Any, cast

from loguru import logger

from sucrawler.common.constants import GET
from sucrawler.core.request import Request
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.downloader import BiliDownloader


class BiliUserApi:
    def __init__(self, config: BiliConfig, downloader: BiliDownloader) -> None:
        self.config = config
        self.downloader = downloader

    async def get_user_info(self, mid: str) -> dict[str, Any]:
        logger.info(f"Getting user info: {mid}")
        url = f"{self.config.api_url}/x/space/wbi/acc/info"
        params = {"mid": mid}

        request = Request(url=url, method=GET, params=params)
        response = await self.downloader.fetch(request)

        if not response.ok:
            return {}

        data = response.json()
        if not isinstance(data, dict):
            return {}

        data_dict = cast(dict[str, Any], data)
        if data_dict.get("code") != 0:
            logger.warning(f"Get user info failed: {data_dict.get('message')}")
            return {}

        user_data = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            user_data if isinstance(user_data, dict) else {},
        )

    async def get_user_stat(self, mid: str) -> dict[str, Any]:
        logger.info(f"Getting user stat: {mid}")
        url = f"{self.config.api_url}/x/relation/stat"
        params = {"vmid": mid}

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

        stat_data = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            stat_data if isinstance(stat_data, dict) else {},
        )

    async def get_user_videos(
        self,
        mid: str,
        pn: int = 1,
        ps: int = 30,
    ) -> dict[str, Any]:
        logger.info(f"Getting user videos: {mid}, page: {pn}")
        url = f"{self.config.api_url}/x/space/wbi/arc/search"
        params = {
            "mid": mid,
            "pn": pn,
            "ps": ps,
            "order": "pubdate",
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
            logger.warning(f"Get user videos failed: {data_dict.get('message')}")
            return {}

        result = data_dict.get("data", {})
        return cast(
            dict[str, Any],
            result if isinstance(result, dict) else {},
        )
