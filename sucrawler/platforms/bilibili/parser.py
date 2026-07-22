from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseParserImpl
from sucrawler.core.response import Response


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}


class BiliParser(BaseParserImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        logger.debug(f"Parsing response from {response.request.url}")
        try:
            json_data = response.json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return {"raw": response.text}

        if not isinstance(json_data, dict):
            return {"data": json_data}

        return json_data

    def parse_user(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing user data")
        user_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(user_data, dict):
            result["mid"] = str(
                user_data.get("mid", user_data.get("id", "")),
            )
            result["name"] = str(
                user_data.get("name", user_data.get("uname", "")),
            )
            face = user_data.get("face", user_data.get("avatar", ""))
            result["avatar"] = str(face) if face else ""
            result["sign"] = str(
                user_data.get("sign", user_data.get("description", "")),
            )
            result["sex"] = str(user_data.get("sex", ""))
            result["level"] = _safe_int(user_data.get("level"), 0)

            fans_info = user_data.get("fans", 0)
            if isinstance(fans_info, dict):
                result["fans"] = _safe_int(fans_info.get("total"), 0)
            else:
                result["fans"] = _safe_int(fans_info, 0)

            following = user_data.get("following", 0)
            if isinstance(following, dict):
                result["following"] = _safe_int(following.get("total"), 0)
            else:
                result["following"] = _safe_int(following, 0)

            result["video_count"] = _safe_int(
                user_data.get("video", user_data.get("archive_count", 0)),
                0,
            )
            result["likes"] = _safe_int(user_data.get("likes", 0), 0)
            result["archive_count"] = _safe_int(
                user_data.get("archive_count", 0),
                0,
            )

        result["raw_data"] = data
        return result

    def parse_video(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing video data")
        video_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(video_data, dict):
            result["bvid"] = str(video_data.get("bvid", ""))
            result["aid"] = _safe_int(video_data.get("aid"), 0)
            result["title"] = str(video_data.get("title", ""))
            result["description"] = str(
                video_data.get("description", video_data.get("desc", "")),
            )
            result["pic"] = str(video_data.get("pic", ""))
            stat = _safe_dict(video_data.get("stat", {}))
            result["play"] = _safe_int(stat.get("view"), 0)
            result["danmaku"] = _safe_int(stat.get("danmaku"), 0)
            result["comment"] = _safe_int(stat.get("reply"), 0)
            result["like"] = _safe_int(stat.get("like"), 0)
            result["coin"] = _safe_int(stat.get("coin"), 0)
            result["collect"] = _safe_int(stat.get("favorite"), 0)
            result["share"] = _safe_int(stat.get("share"), 0)
            result["duration"] = _safe_int(video_data.get("duration"), 0)
            result["pubdate"] = _safe_int(video_data.get("pubdate"), 0)

            owner = _safe_dict(video_data.get("owner", {}))
            result["mid"] = str(owner.get("mid", ""))
            result["author"] = str(owner.get("name", ""))

            tname = video_data.get("tname", "")
            result["tname"] = str(tname) if tname else ""

            tag_list = _safe_list(video_data.get("tags", []))
            result["tags"] = [
                str(tag.get("tag_name", tag)) if isinstance(tag, dict) else str(tag)
                for tag in tag_list
            ]

        result["raw_data"] = data
        return result

    def parse_comment(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing comment data")
        result: dict[str, Any] = {}

        if isinstance(data, dict):
            result["rpid"] = str(data.get("rpid", data.get("id", "")))
            result["oid"] = str(data.get("oid", ""))
            result["type"] = _safe_int(data.get("type"), 1)
            result["message"] = str(
                data.get("content", {}).get("message", "")
                if isinstance(data.get("content"), dict)
                else data.get("content", ""),
            )
            member = _safe_dict(data.get("member", {}))
            result["mid"] = str(member.get("mid", ""))
            result["name"] = str(member.get("uname", ""))
            result["avatar"] = str(member.get("avatar", ""))
            result["like"] = _safe_int(data.get("like"), 0)
            result["rcount"] = _safe_int(data.get("rcount"), 0)
            result["ctime"] = _safe_int(data.get("ctime"), 0)

            if result["ctime"]:
                result["created_at"] = datetime.fromtimestamp(result["ctime"])
            else:
                result["created_at"] = datetime.now()

        result["raw_data"] = data
        return result
