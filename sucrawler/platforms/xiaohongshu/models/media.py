from __future__ import annotations

from sucrawler.core.item import Item


class XHSMediaItem(Item):
    media_id: str
    note_id: str
    url: str
    media_type: str
    width: int
    height: int
    size: int
    platform: str = "xiaohongshu"
