from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from loguru import logger
from lxml import etree

from sucrawler.core.base.base_parser import BaseParserImpl
from sucrawler.core.response import Response


class HtmlParser(BaseParserImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._soup: BeautifulSoup | None = None
        self._lxml_tree: etree._Element | None = None

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        logger.debug(f"Parsing HTML response from {response.request.url}")
        self._soup = BeautifulSoup(response.text, "lxml")
        self._lxml_tree = etree.HTML(response.text)
        return {
            "soup": self._soup,
            "lxml_tree": self._lxml_tree,
            "title": self._soup.title.string if self._soup.title else None,
            "text": self._soup.get_text(),
        }

    def css(self, selector: str) -> list[str]:
        if self._soup is None:
            msg = "Soup not initialized. Call parse() first."
            raise RuntimeError(msg)
        return [str(el) for el in self._soup.select(selector)]

    def css_one(self, selector: str) -> str | None:
        if self._soup is None:
            msg = "Soup not initialized. Call parse() first."
            raise RuntimeError(msg)
        el = self._soup.select_one(selector)
        return str(el) if el else None

    def xpath(self, expression: str) -> list[str]:
        if self._lxml_tree is None:
            msg = "LXML tree not initialized. Call parse() first."
            raise RuntimeError(msg)
        results = self._lxml_tree.xpath(expression)
        if isinstance(results, list):
            return [str(r) for r in results]
        return [str(results)]

    def xpath_one(self, expression: str) -> str | None:
        results = self.xpath(expression)
        return results[0] if results else None
