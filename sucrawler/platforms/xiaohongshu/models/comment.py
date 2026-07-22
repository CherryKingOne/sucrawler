from __future__ import annotations

from datetime import datetime

from sucrawler.core.item import Item


class XHSCommentItem(Item):
    comment_id: str
    note_id: str
    user_id: str
    nickname: str
    content: str
    like_count: int
    reply_count: int
    parent_comment_id: str | None = None
    created_at: datetime
    platform: str = "xiaohongshu"
