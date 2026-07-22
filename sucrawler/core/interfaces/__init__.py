from sucrawler.core.interfaces.downloader import BaseDownloader
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.interfaces.middleware import BaseMiddleware
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.interfaces.pipeline import BasePipeline
from sucrawler.core.interfaces.platform import BasePlatform
from sucrawler.core.interfaces.scheduler import BaseScheduler
from sucrawler.core.interfaces.storage import BaseStorage

__all__ = [
    "BaseDownloader",
    "BaseParser",
    "BaseExtractor",
    "BaseStorage",
    "BaseMiddleware",
    "BasePipeline",
    "BaseScheduler",
    "BasePlatform",
]
