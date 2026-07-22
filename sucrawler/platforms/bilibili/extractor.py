from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseExtractorImpl
from sucrawler.core.item import Item
from sucrawler.platforms.bilibili.models.comment import BiliCommentItem
from sucrawler.platforms.bilibili.models.user import BiliUserItem
from sucrawler.platforms.bilibili.models.video import BiliVideoItem
from sucrawler.platforms.bilibili.parser import BiliParser


class BiliExtractor(BaseExtractorImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.parser = BiliParser(config)

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        logger.debug("Extracting items from data")
        items: list[Item] = []

        if "videos" in data or "vlist" in data:
            items.extend(self.extract_videos(data))
        elif "users" in data:
            items.extend(self.extract_users(data))
        elif "comments" in data:
            items.extend(self.extract_comments(data))

        return items

    def extract_videos(self, data: dict[str, Any]) -> list[BiliVideoItem]:
        logger.debug("Extracting videos")
        videos: list[BiliVideoItem] = []
        raw_videos = data.get("vlist", data.get("videos", data.get("data", [])))

        if isinstance(raw_videos, dict):
            raw_videos = raw_videos.get("vlist", raw_videos.get("list", []))

        if not isinstance(raw_videos, list):
            return videos

        for raw_video in raw_videos:
            if not isinstance(raw_video, dict):
                continue
            parsed = self.parser.parse_video({"data": raw_video})
            video = BiliVideoItem(
                bvid=parsed.get("bvid", ""),
                aid=parsed.get("aid", 0),
                title=parsed.get("title", ""),
                description=parsed.get("description", ""),
                pic=parsed.get("pic", ""),
                play=parsed.get("play", 0),
                danmaku=parsed.get("danmaku", 0),
                comment=parsed.get("comment", 0),
                like=parsed.get("like", 0),
                coin=parsed.get("coin", 0),
                collect=parsed.get("collect", 0),
                share=parsed.get("share", 0),
                duration=parsed.get("duration", 0),
                pubdate=parsed.get("pubdate", 0),
                mid=parsed.get("mid", ""),
                author=parsed.get("author", ""),
                tags=parsed.get("tags", []),
                tname=parsed.get("tname", ""),
                raw_data=parsed.get("raw_data"),
            )
            videos.append(video)

        return videos

    def extract_users(self, data: dict[str, Any]) -> list[BiliUserItem]:
        logger.debug("Extracting users")
        users: list[BiliUserItem] = []
        raw_users = data.get("users", data.get("data", []))

        if not isinstance(raw_users, list):
            if isinstance(raw_users, dict):
                raw_users = [raw_users]
            else:
                return users

        for raw_user in raw_users:
            if not isinstance(raw_user, dict):
                continue
            parsed = self.parser.parse_user({"data": raw_user})
            user = BiliUserItem(
                mid=parsed.get("mid", ""),
                name=parsed.get("name", ""),
                avatar=parsed.get("avatar", ""),
                sign=parsed.get("sign", ""),
                sex=parsed.get("sex", ""),
                level=parsed.get("level", 0),
                fans=parsed.get("fans", 0),
                following=parsed.get("following", 0),
                video_count=parsed.get("video_count", 0),
                likes=parsed.get("likes", 0),
                archive_count=parsed.get("archive_count", 0),
                raw_data=parsed.get("raw_data"),
            )
            users.append(user)

        return users

    def extract_comments(self, data: dict[str, Any]) -> list[BiliCommentItem]:
        logger.debug("Extracting comments")
        comments: list[BiliCommentItem] = []
        raw_comments = data.get("comments", data.get("replies", data.get("data", [])))

        if isinstance(raw_comments, dict):
            raw_comments = raw_comments.get("replies", raw_comments.get("comments", []))

        if not isinstance(raw_comments, list):
            if isinstance(raw_comments, dict):
                raw_comments = [raw_comments]
            else:
                return comments

        for raw_comment in raw_comments:
            if not isinstance(raw_comment, dict):
                continue
            parsed = self.parser.parse_comment(raw_comment)
            created_at = parsed.get("created_at")
            if not isinstance(created_at, datetime):
                created_at = datetime.now()

            comment = BiliCommentItem(
                rpid=str(parsed.get("rpid", "")),
                oid=str(parsed.get("oid", "")),
                type=int(parsed.get("type", 1)),
                message=str(parsed.get("message", "")),
                mid=str(parsed.get("mid", "")),
                name=str(parsed.get("name", "")),
                avatar=str(parsed.get("avatar", "")),
                like=int(parsed.get("like", 0)),
                rcount=int(parsed.get("rcount", 0)),
                ctime=int(parsed.get("ctime", 0)),
                raw_data=parsed.get("raw_data"),
            )
            comments.append(comment)

        return comments
