from __future__ import annotations

from sucrawler.core.item import Item


class BiliUserItem(Item):
    mid: str = ""
    name: str = ""
    avatar: str = ""
    sign: str = ""
    sex: str = ""
    level: int = 0
    fans: int = 0
    following: int = 0
    video_count: int = 0
    likes: int = 0
    archive_count: int = 0
    platform: str = "bilibili"

