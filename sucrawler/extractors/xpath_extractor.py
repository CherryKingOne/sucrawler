from __future__ import annotations

from typing import Any

from loguru import logger
from lxml import etree

from sucrawler.core.base.base_extractor import BaseExtractorImpl
from sucrawler.core.item import Item


class XpathExtractor(BaseExtractorImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.fields: dict[str, str] = self.config.get("fields", {})
        self.item_xpath: str = self.config.get("item_xpath", "")
        self.platform: str = self.config.get("platform", "unknown")
        self.tree_key: str = self.config.get("tree_key", "lxml_tree")

    async def _do_extract(self, data: dict[str, Any]) -> list[Item]:
        logger.debug("Extracting items with XPath")
        tree = data.get(self.tree_key)
        if tree is None:
            logger.warning(f"No lxml_tree found in data with key '{self.tree_key}'")
            return []

        if not isinstance(tree, (etree._Element, etree._ElementTree)):
            logger.warning("Invalid tree type, expected lxml element or tree")
            return []

        if self.item_xpath:
            return self._extract_multiple(tree)
        return self._extract_single(tree)

    def _extract_multiple(self, tree: etree._Element | etree._ElementTree) -> list[Item]:
        elements = tree.xpath(self.item_xpath)
        if not isinstance(elements, list):
            return []

        items: list[Item] = []
        for element in elements:
            if not etree.iselement(element):
                continue
            item_data = self._extract_fields(element)
            item = Item(platform=self.platform, raw_data=item_data)
            items.append(item)

        logger.debug(f"Extracted {len(items)} items with XPath")
        return items

    def _extract_single(self, tree: etree._Element | etree._ElementTree) -> list[Item]:
        item_data = self._extract_fields(tree)
        item = Item(platform=self.platform, raw_data=item_data)
        return [item]

    def _extract_fields(self, element: etree._Element | etree._ElementTree) -> dict[str, Any]:
        item_data: dict[str, Any] = {}
        for field_name, xpath_expr in self.fields.items():
            results = element.xpath(xpath_expr)
            if isinstance(results, list):
                if len(results) == 1:
                    item_data[field_name] = str(results[0]).strip()
                elif len(results) > 1:
                    item_data[field_name] = [str(r).strip() for r in results]
                else:
                    item_data[field_name] = None
            else:
                item_data[field_name] = str(results).strip() if results else None
        return item_data
