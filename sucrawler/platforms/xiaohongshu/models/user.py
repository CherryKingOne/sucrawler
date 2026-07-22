from __future__ import annotations

from sucrawler.core.item import Item


class XHSUserItem(Item):
    user_id: str
    nickname: str
    avatar: str
    desc: str
    gender: str
    fans_count: int
    follows_count: int
    liked_count: int
    notes_count: int
    platform: str = "xiaohongshu"
