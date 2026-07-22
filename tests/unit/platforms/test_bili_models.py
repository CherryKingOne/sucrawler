from __future__ import annotations

import pytest

from sucrawler.platforms.bilibili.models.comment import BiliCommentItem
from sucrawler.platforms.bilibili.models.user import BiliUserItem
from sucrawler.platforms.bilibili.models.video import BiliVideoItem


class TestBiliUserItem:
    def test_create_user(self):
        user = BiliUserItem(
            mid="123456",
            name="TestUser",
            avatar="https://example.com/avatar.jpg",
            sign="test sign",
            sex="男",
            level=6,
            fans=1000,
            following=500,
            video_count=100,
            likes=5000,
            archive_count=200,
        )
        assert user.mid == "123456"
        assert user.name == "TestUser"
        assert user.platform == "bilibili"
        assert user.fans == 1000
        assert user.level == 6

    def test_user_default_values(self):
        user = BiliUserItem(mid="123", name="test")
        assert user.mid == "123"
        assert user.name == "test"
        assert user.avatar == ""
        assert user.sign == ""
        assert user.fans == 0
        assert user.platform == "bilibili"


class TestBiliVideoItem:
    def test_create_video(self):
        video = BiliVideoItem(
            bvid="BV1xx411c7mD",
            aid=123456,
            title="Test Video",
            description="test desc",
            pic="https://example.com/pic.jpg",
            play=10000,
            danmaku=500,
            comment=200,
            like=1000,
            coin=500,
            collect=300,
            share=100,
            duration=120,
            pubdate=1700000000,
            mid="123456",
            author="TestUser",
            tags=["tag1", "tag2"],
            tname="科技",
        )
        assert video.bvid == "BV1xx411c7mD"
        assert video.title == "Test Video"
        assert video.platform == "bilibili"
        assert video.play == 10000
        assert len(video.tags) == 2

    def test_video_default_values(self):
        video = BiliVideoItem(bvid="BV1test", title="test")
        assert video.bvid == "BV1test"
        assert video.title == "test"
        assert video.play == 0
        assert video.tags == []
        assert video.platform == "bilibili"


class TestBiliCommentItem:
    def test_create_comment(self):
        comment = BiliCommentItem(
            rpid="123456",
            oid="789012",
            type=1,
            message="test comment",
            mid="123456",
            name="TestUser",
            avatar="https://example.com/avatar.jpg",
            like=10,
            rcount=5,
            ctime=1700000000,
        )
        assert comment.rpid == "123456"
        assert comment.message == "test comment"
        assert comment.platform == "bilibili"
        assert comment.like == 10

    def test_comment_default_values(self):
        comment = BiliCommentItem(rpid="123", oid="456")
        assert comment.rpid == "123"
        assert comment.oid == "456"
        assert comment.message == ""
        assert comment.like == 0
        assert comment.platform == "bilibili"
