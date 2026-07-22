from __future__ import annotations

from sucrawler.core.item import Item


class BiliCommentItem(Item):
    rpid: str = ""
    oid: str = ""
    type: int = 1
    message: str = ""
    mid: str = ""
    name: str = ""
    avatar: str = ""
    like: int = 0
    rcount: int = 0
    ctime: int = 0
    platform: str = "bilibili"

