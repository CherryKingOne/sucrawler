from sucrawler.downloaders.aiohttp_downloader import AiohttpDownloader
from sucrawler.downloaders.cdp_downloader import CDPDownloader
from sucrawler.downloaders.httpx_downloader import HttpxDownloader
from sucrawler.downloaders.playwright_downloader import PlaywrightDownloader

__all__ = [
    "HttpxDownloader",
    "AiohttpDownloader",
    "PlaywrightDownloader",
    "CDPDownloader",
]
