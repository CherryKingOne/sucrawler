from __future__ import annotations

import pytest

from sucrawler.browser.types import (
    BrowserConfig,
    BrowserInfo,
    BrowserMode,
    BrowserType,
    LaunchOptions,
)


class TestBrowserConfig:
    def test_default_values(self):
        config = BrowserConfig()
        assert config.enabled is False
        assert config.mode == "standard"
        assert config.browser_type == "chrome"
        assert config.cdp_connect_existing is False
        assert config.debug_port == 9222
        assert config.custom_browser_path == ""
        assert config.headless is False
        assert config.user_data_dir == ""
        assert config.save_login_state is True
        assert config.launch_timeout == 60
        assert config.auto_close is True
        assert config.stealth_script_path == ""
        assert config.user_agent == ""
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.proxy == ""

    def test_custom_values(self):
        config = BrowserConfig(
            enabled=True,
            mode="cdp",
            browser_type="edge",
            debug_port=9333,
            headless=True,
        )
        assert config.enabled is True
        assert config.mode == "cdp"
        assert config.browser_type == "edge"
        assert config.debug_port == 9333
        assert config.headless is True

    def test_frozen(self):
        config = BrowserConfig()
        with pytest.raises(Exception):
            config.enabled = True


class TestBrowserInfo:
    def test_creation(self):
        info = BrowserInfo(
            name="Google Chrome",
            version="120.0.0.0",
            path="/usr/bin/chrome",
            type="chrome",
        )
        assert info.name == "Google Chrome"
        assert info.version == "120.0.0.0"
        assert info.path == "/usr/bin/chrome"
        assert info.type == "chrome"


class TestLaunchOptions:
    def test_default_values(self):
        options = LaunchOptions(browser_path="/usr/bin/chrome", debug_port=9222)
        assert options.browser_path == "/usr/bin/chrome"
        assert options.debug_port == 9222
        assert options.headless is False
        assert options.user_data_dir is None
        assert options.user_agent is None
        assert options.proxy is None
        assert options.args == []

    def test_custom_values(self):
        options = LaunchOptions(
            browser_path="/usr/bin/chrome",
            debug_port=9222,
            headless=True,
            user_data_dir="/tmp/data",
            user_agent="TestAgent",
            proxy="http://proxy:8080",
            args=["--disable-gpu"],
        )
        assert options.headless is True
        assert options.user_data_dir == "/tmp/data"
        assert options.user_agent == "TestAgent"
        assert options.proxy == "http://proxy:8080"
        assert options.args == ["--disable-gpu"]
