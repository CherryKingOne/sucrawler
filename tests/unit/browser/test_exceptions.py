from __future__ import annotations

import pytest

from sucrawler.browser.exceptions import (
    BrowserConnectionError,
    BrowserError,
    BrowserLaunchError,
    BrowserNotFoundError,
    BrowserTimeoutError,
    PortNotAvailableError,
)
from sucrawler.common.exceptions import CrawlerException


class TestBrowserExceptions:
    def test_browser_error_inherits_base(self):
        assert issubclass(BrowserError, CrawlerException)

    def test_browser_launch_error(self):
        assert issubclass(BrowserLaunchError, BrowserError)

    def test_browser_connection_error(self):
        assert issubclass(BrowserConnectionError, BrowserError)

    def test_browser_timeout_error(self):
        assert issubclass(BrowserTimeoutError, BrowserError)

    def test_browser_not_found_error(self):
        assert issubclass(BrowserNotFoundError, BrowserError)

    def test_port_not_available_error(self):
        assert issubclass(PortNotAvailableError, BrowserError)

    def test_error_with_message(self):
        err = BrowserError("test error")
        assert str(err) == "test error"
