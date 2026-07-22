from __future__ import annotations

from sucrawler.common.exceptions import CrawlerException


class BrowserError(CrawlerException):
    pass


class BrowserLaunchError(BrowserError):
    pass


class BrowserConnectionError(BrowserError):
    pass


class BrowserTimeoutError(BrowserError):
    pass


class BrowserNotFoundError(BrowserError):
    pass


class PortNotAvailableError(BrowserError):
    pass
