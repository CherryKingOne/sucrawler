from __future__ import annotations

import pytest

from sucrawler.utils.url_parser import detect_platform_from_url, extract_user_id_from_url


class TestExtractUserIdFromUrl:
    def test_xiaohongshu_profile_url(self):
        url = "https://www.xiaohongshu.com/user/profile/abc123def456"
        assert extract_user_id_from_url(url) == "abc123def456"

    def test_xiaohongshu_user_url(self):
        url = "https://www.xiaohongshu.com/user/abc123def456"
        assert extract_user_id_from_url(url) == "abc123def456"

    def test_bilibili_space_url(self):
        url = "https://space.bilibili.com/12345678"
        assert extract_user_id_from_url(url) == "12345678"

    def test_bilibili_url(self):
        url = "https://www.bilibili.com/12345678"
        assert extract_user_id_from_url(url) == "12345678"

    def test_bilibili_upload_video_url(self):
        url = "https://space.bilibili.com/3546833894771340/upload/video"
        assert extract_user_id_from_url(url) == "3546833894771340"

    def test_url_with_quotes(self):
        url = '"https://www.xiaohongshu.com/user/profile/abc123"'
        assert extract_user_id_from_url(url) == "abc123"

    def test_invalid_url(self):
        url = "https://example.com/something"
        assert extract_user_id_from_url(url) is None


class TestDetectPlatformFromUrl:
    def test_xiaohongshu_url(self):
        url = "https://www.xiaohongshu.com/user/profile/abc123"
        assert detect_platform_from_url(url) == "xiaohongshu"

    def test_xhslink_url(self):
        url = "https://xhslink.com/abc123"
        assert detect_platform_from_url(url) == "xiaohongshu"

    def test_bilibili_space_url(self):
        url = "https://space.bilibili.com/123456"
        assert detect_platform_from_url(url) == "bilibili"

    def test_bilibili_main_url(self):
        url = "https://www.bilibili.com/video/BV1xx411c7mD"
        assert detect_platform_from_url(url) == "bilibili"

    def test_bilibili_upload_url(self):
        url = "https://space.bilibili.com/3546833894771340/upload/video"
        assert detect_platform_from_url(url) == "bilibili"

    def test_unknown_url(self):
        url = "https://example.com/something"
        assert detect_platform_from_url(url) is None

    def test_url_case_insensitive(self):
        url = "https://SPACE.BILIBILI.COM/123456"
        assert detect_platform_from_url(url) == "bilibili"
