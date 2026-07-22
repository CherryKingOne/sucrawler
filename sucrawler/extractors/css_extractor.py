from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger

from sucrawler.core.base.base_extractor import BaseExtractorImpl
from sucrawler.core.item import Item


class CssExtractor(BaseExtractorImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.fields: dict[str, str] = self.config.get("fields", {})
        self.item_selector: str = self.config.get("item_selector", "")
        self.platform: str = self.config.get("platform", "unknown")
        self.soup_key: str = self.config.get("soup_key", "soup")
        self.attr_map: dict[str, str] = self.config.get("attr_map", {})

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        logger.debug("Extracting items with CSS selectors")
        soup = data.get(self.soup_key)
        if soup is None:
            logger.warning(f"No soup found in data with key '{self.soup_key}'")
            return []

        if not isinstance(soup, BeautifulSoup):
            logger.warning("Invalid soup type, expected BeautifulSoup")
            return []

        if self.item_selector:
            return self._extract_multiple(soup)
        return self._extract_single(soup)

    def _extract_multiple(self, soup: BeautifulSoup) -> list[Item]:
        elements = soup.select(self.item_selector)
        items: list[Item] = []

        for element in elements:
            item_data = self._extract_fields(element)
            item = Item(platform=self.platform, raw_data=item_data)
            items.append(item)

        logger.debug(f"Extracted {len(items)} items with CSS selectors")
        return items

    def _extract_single(self, soup: BeautifulSoup) -> list[Item]:
        item_data = self._extract_fields(soup)
        item = Item(platform=self.platform, raw_data=item_data)
        return [item]

    def _extract_fields(self, element: BeautifulSoup | Tag) -> dict[str, Any]:
        item_data: dict[str, Any] = {}
        for field_name, selector in self.fields.items():
            attr = self.attr_map.get(field_name)
            results = element.select(selector)

            if len(results) == 1:
                item_data[field_name] = self._get_value(results[0], attr)
            elif len(results) > 1:
                item_data[field_name] = [self._get_value(r, attr) for r in results]
            else:
                item_data[field_name] = None

        return item_data

    def _get_value(self, element: Any, attr: str | None) -> str | None:
        if attr:
            value = element.get(attr)
            return str(value).strip() if value else None
        text = element.get_text(strip=True)
        return text if text else None
