from __future__ import annotations

from typing import Any

from sucrawler.common.exceptions import ExtractException
from sucrawler.core.interfaces.extractor import BaseExtractor
from sucrawler.core.item import Item


class BaseExtractorImpl(BaseExtractor):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def extract(self, data: dict[str, Any]) -> list[Item]:
        try:
            return await self._do_extract(data)
        except Exception as e:
            msg = "Failed to extract items from data"
            raise ExtractException(msg) from e

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        msg = "_do_extract must be implemented by subclass"
        raise NotImplementedError(msg)
