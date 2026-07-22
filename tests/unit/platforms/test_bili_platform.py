from __future__ import annotations

import pytest

from sucrawler.platforms import PlatformRegistry


class TestBiliPlatform:
    def test_bilibili_registered(self):
        platforms = PlatformRegistry.list_platforms()
        assert "bilibili" in platforms
        assert "xiaohongshu" in platforms

    def test_get_bilibili_platform(self):
        platform = PlatformRegistry.get("bilibili")
        assert platform.name == "bilibili"

    def test_bilibili_has_downloader(self):
        platform = PlatformRegistry.get("bilibili")
        downloader = platform.create_downloader()
        assert downloader is not None

    def test_bilibili_has_parser(self):
        platform = PlatformRegistry.get("bilibili")
        parser = platform.create_parser()
        assert parser is not None

    def test_bilibili_has_extractor(self):
        platform = PlatformRegistry.get("bilibili")
        extractor = platform.create_extractor()
        assert extractor is not None
