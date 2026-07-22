from __future__ import annotations

import pytest

from sucrawler.platforms.bilibili.config import BiliConfig


class TestBiliConfig:
    def test_default_config(self):
        config = BiliConfig()
        assert config.base_url == "https://www.bilibili.com"
        assert config.api_url == "https://api.bilibili.com"
        assert config.rate_limit == 1.0
        assert config.cookie == ""
        assert config.sessdata == ""
        assert config.bili_jct == ""
        assert "Mozilla" in config.user_agent

    def test_custom_config(self):
        config = BiliConfig(
            cookie="test_cookie",
            sessdata="test_sessdata",
            bili_jct="test_bili_jct",
            rate_limit=2.0,
        )
        assert config.cookie == "test_cookie"
        assert config.sessdata == "test_sessdata"
        assert config.bili_jct == "test_bili_jct"
        assert config.rate_limit == 2.0
