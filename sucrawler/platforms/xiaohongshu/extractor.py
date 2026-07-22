from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseExtractorImpl
from sucrawler.core.item import Item
from sucrawler.platforms.xiaohongshu.models.comment import XHSCommentItem
from sucrawler.platforms.xiaohongshu.models.note import XHSNoteItem
from sucrawler.platforms.xiaohongshu.models.user import XHSUserItem
from sucrawler.platforms.xiaohongshu.parser import XHSParser


class XHSExtractor(BaseExtractorImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.parser = XHSParser(config)

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        logger.debug("Extracting items from data")
        items: list[Item] = []

        if "notes" in data:
            items.extend(self.extract_notes(data))
        elif "users" in data:
            items.extend(self.extract_users(data))
        elif "comments" in data:
            items.extend(self.extract_comments(data))

        return items

    def extract_notes(self, data: dict[str, Any]) -> list[XHSNoteItem]:
        logger.debug("Extracting notes")
        notes: list[XHSNoteItem] = []
        raw_notes = data.get("notes", data.get("data", []))

        if not isinstance(raw_notes, list):
            if isinstance(raw_notes, dict):
                raw_notes = [raw_notes]
            else:
                return notes

        for raw_note in raw_notes:
            if not isinstance(raw_note, dict):
                continue
            parsed = self.parser.parse_note({"data": raw_note})
            note = XHSNoteItem(
                note_id=parsed.get("note_id", ""),
                title=parsed.get("title", ""),
                desc=parsed.get("desc", ""),
                type=parsed.get("type", "normal"),
                cover_url=parsed.get("cover_url", ""),
                liked_count=parsed.get("liked_count", 0),
                collected_count=parsed.get("collected_count", 0),
                comment_count=parsed.get("comment_count", 0),
                share_count=parsed.get("share_count", 0),
                user_id=parsed.get("user_id", ""),
                nickname=parsed.get("nickname", ""),
                tags=parsed.get("tags", []),
                images=parsed.get("images", []),
                video_url=parsed.get("video_url"),
                raw_data=parsed.get("raw_data"),
            )
            notes.append(note)

        return notes

    def extract_users(self, data: dict[str, Any]) -> list[XHSUserItem]:
        logger.debug("Extracting users")
        users: list[XHSUserItem] = []
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
            user = XHSUserItem(
                user_id=parsed.get("user_id", ""),
                nickname=parsed.get("nickname", ""),
                avatar=parsed.get("avatar", ""),
                desc=parsed.get("desc", ""),
                gender=parsed.get("gender", ""),
                fans_count=parsed.get("fans_count", 0),
                follows_count=parsed.get("follows_count", 0),
                liked_count=parsed.get("liked_count", 0),
                notes_count=parsed.get("notes_count", 0),
                raw_data=parsed.get("raw_data"),
            )
            users.append(user)

        return users

    def extract_comments(self, data: dict[str, Any]) -> list[XHSCommentItem]:
        logger.debug("Extracting comments")
        comments: list[XHSCommentItem] = []
        raw_comments = data.get("comments", data.get("data", []))

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

            comment = XHSCommentItem(
                comment_id=str(parsed.get("comment_id", "")),
                note_id=str(parsed.get("note_id", "")),
                user_id=str(parsed.get("user_id", "")),
                nickname=str(parsed.get("nickname", "")),
                content=str(parsed.get("content", "")),
                like_count=int(parsed.get("like_count", 0)),
                reply_count=int(parsed.get("reply_count", 0)),
                parent_comment_id=parsed.get("parent_comment_id"),
                created_at=created_at,
                raw_data=parsed.get("raw_data"),
            )
            comments.append(comment)

        return comments
