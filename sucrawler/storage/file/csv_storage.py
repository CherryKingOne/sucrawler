import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("csv")
class CSVStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.file_path: str = self.config.get("file_path", "items.csv")
        self.append: bool = self.config.get("append", True)
        self._fieldnames: list[str] = ["id", "platform", "crawled_at", "raw_data"]
        self._ensure_file()
        logger.info(f"CSV storage initialized: {self.file_path}")

    def _ensure_file(self) -> None:
        try:
            file_path = Path(self.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            needs_header = False
            if not file_path.exists() or not self.append:
                needs_header = True
            elif file_path.stat().st_size == 0:
                needs_header = True
            if needs_header:
                with file_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                    writer.writeheader()
        except Exception as e:
            msg = f"Failed to ensure CSV file: {e}"
            raise StorageException(msg) from e

    async def save(self, item: Item) -> bool:
        try:
            with Path(self.file_path).open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                raw_data_str = (
                    json.dumps(item.raw_data, ensure_ascii=False)
                    if item.raw_data
                    else ""
                )
                writer.writerow(
                    {
                        "id": item.id or "",
                        "platform": item.platform,
                        "crawled_at": item.crawled_at.isoformat(),
                        "raw_data": raw_data_str,
                    }
                )
            logger.debug(f"Item saved to CSV: {item.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save item to CSV: {e}")
            return False

    async def save_batch(self, items: list[Item]) -> int:
        if not items:
            return 0
        try:
            with Path(self.file_path).open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                for item in items:
                    raw_data_str = (
                        json.dumps(item.raw_data, ensure_ascii=False)
                        if item.raw_data
                        else ""
                    )
                    writer.writerow(
                        {
                            "id": item.id or "",
                            "platform": item.platform,
                            "crawled_at": item.crawled_at.isoformat(),
                            "raw_data": raw_data_str,
                        }
                    )
            logger.debug(f"Batch saved {len(items)} items to CSV")
            return len(items)
        except Exception as e:
            logger.error(f"Failed to batch save items to CSV: {e}")
            return 0

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        try:
            items: list[Item] = []
            with Path(self.file_path).open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    match = True
                    for key, value in condition.items():
                        if row.get(key) != str(value):
                            match = False
                            break
                    if match:
                        items.append(
                            Item(
                                id=row["id"] or None,
                                platform=row["platform"],
                                crawled_at=datetime.fromisoformat(row["crawled_at"]),
                                raw_data=json.loads(row["raw_data"]) if row["raw_data"] else None,
                            )
                        )
            logger.debug(f"CSV query returned {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"Failed to query items from CSV: {e}")
            return []

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("CSVStorage.update not fully supported, rewriting entire file")
        try:
            items = await self.query({})
            updated = False
            with Path(self.file_path).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                writer.writeheader()
                for item in items:
                    if item.id == item_id:
                        for key, value in data.items():
                            if hasattr(item, key):
                                setattr(item, key, value)
                        updated = True
                    raw_data_str = (
                        json.dumps(item.raw_data, ensure_ascii=False)
                        if item.raw_data
                        else ""
                    )
                    writer.writerow(
                        {
                            "id": item.id or "",
                            "platform": item.platform,
                            "crawled_at": item.crawled_at.isoformat(),
                            "raw_data": raw_data_str,
                        }
                    )
            if updated:
                logger.debug(f"Item updated in CSV: {item_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update item in CSV: {e}")
            return False

    async def delete(self, item_id: str) -> bool:
        logger.warning("CSVStorage.delete not fully supported, rewriting entire file")
        try:
            items = await self.query({})
            deleted = False
            with Path(self.file_path).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames)
                writer.writeheader()
                for item in items:
                    if item.id == item_id:
                        deleted = True
                        continue
                    raw_data_str = (
                        json.dumps(item.raw_data, ensure_ascii=False)
                        if item.raw_data
                        else ""
                    )
                    writer.writerow(
                        {
                            "id": item.id or "",
                            "platform": item.platform,
                            "crawled_at": item.crawled_at.isoformat(),
                            "raw_data": raw_data_str,
                        }
                    )
            if deleted:
                logger.debug(f"Item deleted from CSV: {item_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete item from CSV: {e}")
            return False
