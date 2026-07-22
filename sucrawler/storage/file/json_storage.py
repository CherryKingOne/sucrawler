import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("json")
class JSONStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.file_path: str = self.config.get("file_path", "items.json")
        self._ensure_file()
        logger.info(f"JSON storage initialized: {self.file_path}")

    def _ensure_file(self) -> None:
        try:
            file_path = Path(self.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if not file_path.exists():
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
        except Exception as e:
            msg = f"Failed to ensure JSON file: {e}"
            raise StorageException(msg) from e

    def _read_all(self) -> list[dict[str, Any]]:
        try:
            with Path(self.file_path).open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        with Path(self.file_path).open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def _item_to_dict(self, item: Item) -> dict[str, Any]:
        return {
            "id": item.id,
            "platform": item.platform,
            "crawled_at": item.crawled_at.isoformat(),
            "raw_data": item.raw_data,
        }

    def _dict_to_item(self, data: dict[str, Any]) -> Item:
        return Item(
            id=data.get("id"),
            platform=data["platform"],
            crawled_at=datetime.fromisoformat(data["crawled_at"]),
            raw_data=data.get("raw_data"),
        )

    async def save(self, item: Item) -> bool:
        try:
            items = self._read_all()
            item_dict = self._item_to_dict(item)
            for i, existing in enumerate(items):
                if existing.get("id") == item.id:
                    items[i] = item_dict
                    break
            else:
                items.append(item_dict)
            self._write_all(items)
            logger.debug(f"Item saved to JSON: {item.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save item to JSON: {e}")
            return False

    async def save_batch(self, items: list[Item]) -> int:
        if not items:
            return 0
        try:
            existing_items = self._read_all()
            item_map: dict[str, dict[str, Any]] = {}
            for existing in existing_items:
                if existing.get("id"):
                    item_map[existing["id"]] = existing
            for item in items:
                item_dict = self._item_to_dict(item)
                if item.id:
                    item_map[item.id] = item_dict
                else:
                    existing_items.append(item_dict)
            self._write_all(list(item_map.values()))
            logger.debug(f"Batch saved {len(items)} items to JSON")
            return len(items)
        except Exception as e:
            logger.error(f"Failed to batch save items to JSON: {e}")
            return 0

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        try:
            all_items = self._read_all()
            result: list[Item] = []
            for item_dict in all_items:
                match = True
                for key, value in condition.items():
                    if item_dict.get(key) != value:
                        match = False
                        break
                if match:
                    result.append(self._dict_to_item(item_dict))
            logger.debug(f"JSON query returned {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"Failed to query items from JSON: {e}")
            return []

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        try:
            items = self._read_all()
            updated = False
            for item_dict in items:
                if item_dict.get("id") == item_id:
                    item_dict.update(data)
                    updated = True
                    break
            if updated:
                self._write_all(items)
                logger.debug(f"Item updated in JSON: {item_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update item in JSON: {e}")
            return False

    async def delete(self, item_id: str) -> bool:
        try:
            items = self._read_all()
            new_items = [item for item in items if item.get("id") != item_id]
            deleted = len(items) != len(new_items)
            if deleted:
                self._write_all(new_items)
                logger.debug(f"Item deleted from JSON: {item_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete item from JSON: {e}")
            return False
