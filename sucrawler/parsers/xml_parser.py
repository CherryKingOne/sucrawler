from __future__ import annotations

from typing import Any

from loguru import logger
from lxml import etree

from sucrawler.core.base.base_parser import BaseParserImpl
from sucrawler.core.response import Response


class XmlParser(BaseParserImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._tree: etree._ElementTree | None = None
        self._root: etree._Element | None = None

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        logger.debug(f"Parsing XML response from {response.request.url}")
        self._root = etree.fromstring(response.content)
        self._tree = etree.ElementTree(self._root)
        return {
            "root": self._root,
            "tree": self._tree,
            "tag": self._root.tag,
        }

    def xpath(self, expression: str) -> list[str]:
        if self._root is None:
            msg = "XML tree not initialized. Call parse() first."
            raise RuntimeError(msg)
        results = self._root.xpath(expression)
        if isinstance(results, list):
            return [str(r) for r in results]
        return [str(results)]

    def xpath_one(self, expression: str) -> str | None:
        results = self.xpath(expression)
        return results[0] if results else None

    def get_elements(self, expression: str) -> list[etree._Element]:
        if self._root is None:
            msg = "XML tree not initialized. Call parse() first."
            raise RuntimeError(msg)
        results = self._root.xpath(expression)
        if isinstance(results, list):
            return [r for r in results if etree.iselement(r)]
        return []

    def get_element(self, expression: str) -> etree._Element | None:
        elements = self.get_elements(expression)
        return elements[0] if elements else None
