from __future__ import annotations

from sucrawler.core.item import Item


class BiliVideoItem(Item):
    bvid: str = ""
    aid: int = 0
    title: str = ""
    description: str = ""
    pic: str = ""
    play: int = 0
    danmaku: int = 0
    comment: int = 0
    like: int = 0
    coin: int = 0
    collect: int = 0
    share: int = 0
    duration: int = 0
    pubdate: int = 0
    mid: str = ""
    author: str = ""
    tags: list[str] = []
    tname: str = ""
    # 视频详情页补充字段
    cid: int = 0
    video_urls: list[str] = []
    audio_urls: list[str] = []
    accept_quality: list[int] = []
    accept_description: list[str] = []
    platform: str = "bilibili"
