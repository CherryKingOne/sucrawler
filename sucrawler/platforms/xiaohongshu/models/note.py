from __future__ import annotations

from sucrawler.core.item import Item


class XHSNoteItem(Item):
    note_id: str
    title: str
    desc: str
    type: str
    cover_url: str
    liked_count: int
    collected_count: int
    comment_count: int
    share_count: int
    user_id: str
    nickname: str
    tags: list[str]
    images: list[str]
    video_url: str | None = None
    platform: str = "xiaohongshu"
