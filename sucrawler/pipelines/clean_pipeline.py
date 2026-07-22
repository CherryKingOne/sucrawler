from __future__ import annotations

import re
import unicodedata
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger

from sucrawler.core.base.base_pipeline import BasePipelineImpl
from sucrawler.core.item import Item


class CleanPipeline(BasePipelineImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.strip_whitespace: bool = self.config.get("strip_whitespace", True)
        self.clean_html: bool = self.config.get("clean_html", True)
        self.filter_special_chars: bool = self.config.get("filter_special_chars", False)
        self.format_fields: dict[str, str] = self.config.get("format_fields", {})
        self.fields: list[str] | None = self.config.get("fields")
        self.special_char_pattern: re.Pattern[str] = re.compile(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
        )

    async def process_item(self, item: Item) -> Item:
        logger.debug(f"Cleaning item: {item.id}")
        raw_data = item.raw_data or {}

        if self.fields:
            for field in self.fields:
                if field in raw_data:
                    raw_data[field] = self._clean_value(raw_data[field])
        else:
            for key, value in raw_data.items():
                raw_data[key] = self._clean_value(value)

        for field, fmt in self.format_fields.items():
            if field in raw_data:
                raw_data[field] = self._format_field(raw_data[field], fmt)

        item.raw_data = raw_data
        return item

    def _clean_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            return [self._clean_value(v) for v in value]
        if not isinstance(value, str):
            return value

        result = value

        if self.clean_html:
            result = self._strip_html(result)

        if self.strip_whitespace:
            result = self._strip_whitespace(result)

        if self.filter_special_chars:
            result = self._filter_special_chars(result)

        return result

    def _strip_html(self, text: str) -> str:
        try:
            soup = BeautifulSoup(text, "lxml")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return text

    def _strip_whitespace(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = unicodedata.normalize("NFKC", text)
        return text.strip()

    def _filter_special_chars(self, text: str) -> str:
        return self.special_char_pattern.sub("", text)

    def _format_field(self, value: Any, fmt: str) -> Any:
        if fmt == "int":
            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return value
        if fmt == "float":
            try:
                return float(str(value).strip())
            except (ValueError, TypeError):
                return value
        if fmt == "bool":
            return str(value).strip().lower() in ("true", "1", "yes", "是")
        if fmt == "lower":
            return str(value).lower()
        if fmt == "upper":
            return str(value).upper()
        if fmt == "title":
            return str(value).title()
        return value
