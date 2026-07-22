from __future__ import annotations

from typing import Any

from loguru import logger
from pydantic import BaseModel, ValidationError

from sucrawler.common.exceptions import PipelineException
from sucrawler.core.base.base_pipeline import BasePipelineImpl
from sucrawler.core.item import Item


class ValidatePipeline(BasePipelineImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.model_class: type[BaseModel] | None = self.config.get("model_class")
        self.validate_raw: bool = self.config.get("validate_raw", True)
        self.drop_invalid: bool = self.config.get("drop_invalid", True)
        self.required_fields: list[str] = self.config.get("required_fields", [])
        self.field_types: dict[str, type] = self.config.get("field_types", {})
        self._invalid_count: int = 0
        self._valid_count: int = 0

    async def open_spider(self, spider: Any) -> None:
        logger.info("Opening ValidatePipeline")
        self._invalid_count = 0
        self._valid_count = 0

    async def close_spider(self, spider: Any) -> None:
        logger.info(
            f"Closing ValidatePipeline - valid: {self._valid_count}, "
            f"invalid: {self._invalid_count}"
        )

    async def process_item(self, item: Item) -> Item:
        try:
            self._validate_item(item)
            self._valid_count += 1
            return item
        except ValidationError as e:
            self._invalid_count += 1
            logger.error(f"Pydantic validation failed for item: {e.errors()}")
            if self.drop_invalid:
                msg = f"Validation failed: {e.errors()}"
                raise DropItemException(msg) from e
            return item
        except (ValueError, TypeError) as e:
            self._invalid_count += 1
            logger.error(f"Validation failed for item: {e}")
            if self.drop_invalid:
                msg = f"Validation failed: {e}"
                raise DropItemException(msg) from e
            return item

    def _validate_item(self, item: Item) -> None:
        data = item.raw_data or {}

        if self.required_fields:
            self._validate_required_fields(data)

        if self.field_types:
            self._validate_field_types(data)

        if self.model_class and self.validate_raw:
            self._validate_with_pydantic(data)

    def _validate_required_fields(self, data: dict[str, Any]) -> None:
        missing: list[str] = []
        for field in self.required_fields:
            if field not in data or data[field] is None:
                if isinstance(data.get(field), str) and not data[field].strip():
                    missing.append(field)
                elif not isinstance(data.get(field), str):
                    missing.append(field)

        if missing:
            msg = f"Missing required fields: {missing}"
            raise ValueError(msg)

    def _validate_field_types(self, data: dict[str, Any]) -> None:
        for field, expected_type in self.field_types.items():
            if field not in data or data[field] is None:
                continue
            if not isinstance(data[field], expected_type):
                msg = (
                    f"Field '{field}' has type {type(data[field]).__name__}, "
                    f"expected {expected_type.__name__}"
                )
                raise TypeError(msg)

    def _validate_with_pydantic(self, data: dict[str, Any]) -> None:
        if self.model_class is None:
            return
        self.model_class.model_validate(data)


class DropItemException(PipelineException):  # noqa: N818
    pass
