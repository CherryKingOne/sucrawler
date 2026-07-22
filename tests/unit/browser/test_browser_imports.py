from __future__ import annotations

from sucrawler.browser import (
    BrowserConfig,
    BrowserConnectionError,
    BrowserError,
    BrowserInfo,
    BrowserLaunchError,
    BrowserNotFoundError,
    BrowserTimeoutError,
    PortNotAvailableError,
)
from sucrawler.browser.launcher import ChromeLauncher, PathDetector


class TestBrowserModule:
    def test_imports_from_browser(self):
        assert BrowserConfig is not None
        assert BrowserInfo is not None
        assert BrowserError is not None
        assert BrowserLaunchError is not None
        assert BrowserConnectionError is not None
        assert BrowserTimeoutError is not None
        assert BrowserNotFoundError is not None
        assert PortNotAvailableError is not None

    def test_imports_from_launcher(self):
        assert ChromeLauncher is not None
        assert PathDetector is not None
