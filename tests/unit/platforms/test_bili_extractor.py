from __future__ import annotations

import pytest

from sucrawler.platforms.bilibili.extractor import BiliExtractor
from sucrawler.platforms.bilibili.models.user import BiliUserItem
from sucrawler.platforms.bilibili.models.video import BiliVideoItem


class TestBiliExtractor:
    def test_extract_videos_from_vlist(self):
        extractor = BiliExtractor()
        data = {
            "vlist": [
                {
                    "bvid": "BV1test1",
                    "aid": 1,
                    "title": "Test Video 1",
                    "description": "desc 1",
                    "pic": "pic1.jpg",
                    "play": 1000,
                    "video_review": 100,
                    "comment": 50,
                    "like": 200,
                    "coin": 100,
                    "favorite": 80,
                    "share": 30,
                    "length": "10:00",
                    "created": 1700000000,
                    "mid": "123",
                    "author": "TestUser",
                    "typeid": 1,
                    "tname": "科技",
                },
                {
                    "bvid": "BV1test2",
                    "aid": 2,
                    "title": "Test Video 2",
                    "description": "desc 2",
                    "pic": "pic2.jpg",
                    "play": 2000,
                    "video_review": 200,
                    "comment": 100,
                    "like": 400,
                    "coin": 200,
                    "favorite": 160,
                    "share": 60,
                    "length": "20:00",
                    "created": 1700001000,
                    "mid": "123",
                    "author": "TestUser",
                    "typeid": 1,
                    "tname": "科技",
                },
            ],
        }
        videos = extractor.extract_videos(data)
        assert len(videos) == 2
        assert isinstance(videos[0], BiliVideoItem)
        assert videos[0].bvid == "BV1test1"
        assert videos[0].title == "Test Video 1"

    def test_extract_users(self):
        extractor = BiliExtractor()
        data = {
            "data": [
                {
                    "mid": "123456",
                    "name": "TestUser",
                    "face": "avatar.jpg",
                    "sign": "test sign",
                    "sex": "男",
                    "level": 6,
                    "fans": {"total": 1000},
                    "following": {"total": 500},
                },
            ],
        }
        users = extractor.extract_users(data)
        assert len(users) == 1
        assert isinstance(users[0], BiliUserItem)
        assert users[0].mid == "123456"
        assert users[0].name == "TestUser"

    def test_extract_empty(self):
        extractor = BiliExtractor()
        videos = extractor.extract_videos({})
        assert videos == []
        users = extractor.extract_users({})
        assert users == []
