from __future__ import annotations

import re
from typing import Any

from loguru import logger

from sucrawler.core.base.base_extractor import BaseExtractorImpl
from sucrawler.core.item import Item


class RegexExtractor(BaseExtractorImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.patterns: dict[str, str] = self.config.get("patterns", {})
        self.compiled_patterns: dict[str, re.Pattern[str]] = {
            name: re.compile(pattern) for name, pattern in self.patterns.items()
        }
        self.platform: str = self.config.get("platform", "unknown")
        self.text_key: str = self.config.get("text_key", "text")
        self.find_all: bool = self.config.get("find_all", False)

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        text = str(data.get(self.text_key, ""))
        logger.debug(f"Extracting with regex from text of length {len(text)}")

        if not self.patterns:
            logger.warning("No regex patterns configured")
            return []

        extracted_data: dict[str, Any] = {}
        for name, pattern in self.compiled_patterns.items():
            if self.find_all:
                matches = pattern.findall(text)
                extracted_data[name] = matches
            else:
                match = pattern.search(text)
                if match and match.groupdict():
                    extracted_data[name] = match.groupdict()
                elif match:
                    extracted_data[name] = match.group(0)
                else:
                    extracted_data[name] = None

        items: list[Item] = []
        if self.find_all and self._has_list_values(extracted_data):
            max_len = max(len(v) for v in extracted_data.values() if isinstance(v, list))
            for i in range(max_len):
                item_data = self._build_item_data(extracted_data, i)
                item = Item(platform=self.platform, raw_data=item_data)
                items.append(item)
        else:
            item = Item(platform=self.platform, raw_data=extracted_data)
            items.append(item)

        logger.debug(f"Extracted {len(items)} items with regex")
        return items

    def _has_list_values(self, data: dict[str, Any]) -> bool:
        return any(isinstance(v, list) for v in data.values())

    def _build_item_data(self, extracted_data: dict[str, Any], index: int) -> dict[str, Any]:
        item_data: dict[str, Any] = {}
        for key, value in extracted_data.items():
            if isinstance(value, list):
                item_data[key] = value[index] if index < len(value) else None
            else:
                item_data[key] = value
        return item_data
