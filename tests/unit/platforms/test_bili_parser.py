from __future__ import annotations

import pytest

from sucrawler.platforms.bilibili.parser import BiliParser, _safe_int, _safe_list, _safe_dict


class TestParserUtils:
    def test_safe_int(self):
        assert _safe_int(123) == 123
        assert _safe_int("456") == 456
        assert _safe_int(None) == 0
        assert _safe_int("abc") == 0
        assert _safe_int(None, 10) == 10

    def test_safe_list(self):
        assert _safe_list([1, 2, 3]) == [1, 2, 3]
        assert _safe_list(None) == []
        assert _safe_list("not a list") == []

    def test_safe_dict(self):
        assert _safe_dict({"a": 1}) == {"a": 1}
        assert _safe_dict(None) == {}
        assert _safe_list("not a dict") == []


class TestBiliParser:
    def test_parse_user(self):
        parser = BiliParser()
        data = {
            "data": {
                "mid": "123456",
                "name": "TestUser",
                "face": "https://example.com/avatar.jpg",
                "sign": "test sign",
                "sex": "男",
                "level": 6,
                "fans": {"total": 1000},
                "following": {"total": 500},
                "video": 100,
                "likes": 5000,
            },
        }
        result = parser.parse_user(data)
        assert result["mid"] == "123456"
        assert result["name"] == "TestUser"
        assert result["avatar"] == "https://example.com/avatar.jpg"
        assert result["fans"] == 1000
        assert result["level"] == 6

    def test_parse_video(self):
        parser = BiliParser()
        data = {
            "data": {
                "bvid": "BV1xx411c7mD",
                "aid": 123456,
                "title": "Test Video",
                "description": "test desc",
                "pic": "https://example.com/pic.jpg",
                "duration": 120,
                "pubdate": 1700000000,
                "stat": {
                    "view": 10000,
                    "danmaku": 500,
                    "reply": 200,
                    "like": 1000,
                    "coin": 500,
                    "favorite": 300,
                    "share": 100,
                },
                "owner": {
                    "mid": "123456",
                    "name": "TestUser",
                },
                "tname": "科技",
            },
        }
        result = parser.parse_video(data)
        assert result["bvid"] == "BV1xx411c7mD"
        assert result["title"] == "Test Video"
        assert result["play"] == 10000
        assert result["comment"] == 200
        assert result["mid"] == "123456"
        assert result["author"] == "TestUser"
        assert result["tname"] == "科技"

    def test_parse_comment(self):
        parser = BiliParser()
        data = {
            "rpid": 123456,
            "oid": 789012,
            "type": 1,
            "content": {"message": "test comment"},
            "member": {
                "mid": "123456",
                "uname": "TestUser",
                "avatar": "https://example.com/avatar.jpg",
            },
            "like": 10,
            "rcount": 5,
            "ctime": 1700000000,
        }
        result = parser.parse_comment(data)
        assert result["rpid"] == "123456"
        assert result["message"] == "test comment"
        assert result["mid"] == "123456"
        assert result["name"] == "TestUser"
        assert result["like"] == 10
        assert result["rcount"] == 5
