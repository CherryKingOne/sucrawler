from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timezone
from typing import Any

from loguru import logger

from sucrawler.core.base.base_pipeline import BasePipelineImpl
from sucrawler.core.item import Item


class EnrichPipeline(BasePipelineImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.add_metadata: bool = self.config.get("add_metadata", True)
        self.format_time: bool = self.config.get("format_time", True)
        self.time_format: str = self.config.get("time_format", "%Y-%m-%d %H:%M:%S")
        self.timezone: timezone = self.config.get("timezone", UTC)
        self.field_transforms: dict[str, str] = self.config.get("field_transforms", {})
        self.extra_fields: dict[str, Any] = self.config.get("extra_fields", {})
        self.generate_id: bool = self.config.get("generate_id", True)
        self.id_fields: list[str] = self.config.get("id_fields", [])

    async def process_item(self, item: Item) -> Item:
        logger.debug(f"Enriching item: {item.id}")
        raw_data = item.raw_data or {}

        if self.add_metadata:
            raw_data = self._add_metadata(raw_data, item)

        if self.format_time:
            raw_data = self._format_time_fields(raw_data)

        if self.field_transforms:
            raw_data = self._transform_fields(raw_data)

        if self.extra_fields:
            raw_data = self._add_extra_fields(raw_data)

        if self.generate_id and not item.id:
            item.id = self._generate_id(raw_data)

        item.raw_data = raw_data
        return item

    def _add_metadata(self, data: dict[str, Any], item: Item) -> dict[str, Any]:
        now = datetime.now(self.timezone)
        data.setdefault("_crawled_at", item.crawled_at.isoformat())
        data.setdefault("_platform", item.platform)
        data.setdefault("_processed_at", now.isoformat())
        data.setdefault("_enriched_at", now.isoformat())
        return data

    def _format_time_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[f"{key}_formatted"] = value.strftime(self.time_format)
                data[f"{key}_iso"] = value.isoformat()
            elif isinstance(value, str):
                parsed = self._try_parse_datetime(value)
                if parsed:
                    data[f"{key}_formatted"] = parsed.strftime(self.time_format)
                    data[f"{key}_iso"] = parsed.isoformat()
        return data

    def _try_parse_datetime(self, value: str) -> datetime | None:
        formats: list[str] = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=self.timezone)
            except ValueError:
                continue
        return None

    def _transform_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        for field, transform in self.field_transforms.items():
            if field not in data or data[field] is None:
                continue

            value = data[field]
            if transform == "lower":
                data[field] = str(value).lower()
            elif transform == "upper":
                data[field] = str(value).upper()
            elif transform == "title":
                data[field] = str(value).title()
            elif transform == "strip":
                data[field] = str(value).strip()
            elif transform == "int":
                try:
                    data[field] = int(str(value).strip())
                except (ValueError, TypeError):
                    pass
            elif transform == "float":
                try:
                    data[field] = float(str(value).strip())
                except (ValueError, TypeError):
                    pass
            elif transform == "len":
                if isinstance(value, (list, str, dict)):
                    data[f"{field}_len"] = len(value)
        return data

    def _add_extra_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        for key, value in self.extra_fields.items():
            data.setdefault(key, value)
        return data

    def _generate_id(self, data: dict[str, Any]) -> str:
        if self.id_fields:
            values: list[str] = []
            for field in self.id_fields:
                value = data.get(field)
                if value is not None:
                    values.append(str(value))
            if values:
                raw_id = "|".join(values)
                return hashlib.md5(raw_id.encode()).hexdigest()

        raw_id = str(data)
        return hashlib.md5(raw_id.encode()).hexdigest()
