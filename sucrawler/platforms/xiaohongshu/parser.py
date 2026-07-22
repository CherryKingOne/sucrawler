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


class XHSParser(BaseParserImpl):
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

    def parse_note(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing note data")
        note_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(note_data, dict):
            result["note_id"] = str(
                note_data.get("id", note_data.get("note_id", "")),
            )
            result["title"] = str(note_data.get("title", ""))
            result["desc"] = str(
                note_data.get("desc", note_data.get("description", "")),
            )
            result["type"] = str(note_data.get("type", "normal"))
            cover = _safe_dict(note_data.get("cover", {}))
            result["cover_url"] = str(
                cover.get("url", note_data.get("cover_url", "")),
            )
            result["liked_count"] = _safe_int(
                note_data.get("liked_count"),
                0,
            )
            result["collected_count"] = _safe_int(
                note_data.get("collected_count"),
                0,
            )
            result["comment_count"] = _safe_int(
                note_data.get("comment_count", note_data.get("comments_count")),
                0,
            )
            result["share_count"] = _safe_int(
                note_data.get("share_count"),
                0,
            )

            user = _safe_dict(note_data.get("user", {}))
            result["user_id"] = str(user.get("user_id", user.get("id", "")))
            result["nickname"] = str(user.get("nickname", ""))

            tag_list = _safe_list(
                note_data.get("tag_list", note_data.get("tags")),
            )
            result["tags"] = [
                str(tag.get("name", ""))
                for tag in tag_list
                if isinstance(tag, dict)
            ]

            image_list = _safe_list(
                note_data.get("image_list", note_data.get("images")),
            )
            result["images"] = [
                str(img.get("url", ""))
                for img in image_list
                if isinstance(img, dict)
            ]

            video = _safe_dict(note_data.get("video", {}))
            if video:
                result["video_url"] = str(video.get("url", ""))
            else:
                result["video_url"] = None

        result["raw_data"] = data
        return result

    def parse_user(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing user data")
        user_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(user_data, dict):
            result["user_id"] = str(
                user_data.get("user_id", user_data.get("id", "")),
            )
            result["nickname"] = str(user_data.get("nickname", ""))
            result["avatar"] = str(
                user_data.get("avatar", user_data.get("avatar_url", "")),
            )
            result["desc"] = str(
                user_data.get("desc", user_data.get("description", "")),
            )
            result["gender"] = str(user_data.get("gender", ""))
            result["fans_count"] = _safe_int(
                user_data.get("fans", user_data.get("fans_count")),
                0,
            )
            result["follows_count"] = _safe_int(
                user_data.get("follows", user_data.get("follows_count")),
                0,
            )
            result["liked_count"] = _safe_int(
                user_data.get("liked", user_data.get("liked_count")),
                0,
            )
            result["notes_count"] = _safe_int(
                user_data.get("notes", user_data.get("notes_count")),
                0,
            )

        result["raw_data"] = data
        return result

    def parse_comment(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing comment data")
        result: dict[str, Any] = {}

        if isinstance(data, dict):
            result["comment_id"] = str(
                data.get("id", data.get("comment_id", "")),
            )
            result["note_id"] = str(data.get("note_id", ""))
            user = _safe_dict(data.get("user_info", data.get("user", {})))
            result["user_id"] = str(user.get("user_id", user.get("id", "")))
            result["nickname"] = str(user.get("nickname", ""))
            result["content"] = str(data.get("content", ""))
            result["like_count"] = _safe_int(
                data.get("like_count", data.get("likes")),
                0,
            )
            result["reply_count"] = _safe_int(
                data.get("reply_count", data.get("sub_comment_count")),
                0,
            )
            result["parent_comment_id"] = data.get(
                "parent_comment_id",
                data.get("parent_id"),
            )

            created_at = data.get("create_time", data.get("created_at", 0))
            if isinstance(created_at, (int, float)):
                if created_at > 1e12:
                    created_at = created_at / 1000
                result["created_at"] = datetime.fromtimestamp(created_at)
            else:
                result["created_at"] = datetime.now()

        result["raw_data"] = data
        return result
