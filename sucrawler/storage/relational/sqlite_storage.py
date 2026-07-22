import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("sqlite")
class SQLiteStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.db_path: str = self.config.get("db_path", "crawler.db")
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._create_table()
            logger.info(f"SQLite storage initialized: {self.db_path}")
        except Exception as e:
            msg = f"Failed to initialize SQLite storage: {e}"
            raise StorageException(msg) from e

    def _create_table(self) -> None:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                raw_data TEXT
            )
        """)
        self._conn.commit()

    async def save(self, item: Item) -> bool:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        try:
            cursor = self._conn.cursor()
            sql = (
                "INSERT OR REPLACE INTO items "
                "(id, platform, crawled_at, raw_data) VALUES (?, ?, ?, ?)"
            )
            raw_data_json = (
                json.dumps(item.raw_data, ensure_ascii=False)
                if item.raw_data
                else None
            )
            cursor.execute(
                sql,
                (
                    item.id,
                    item.platform,
                    item.crawled_at.isoformat(),
                    raw_data_json,
                ),
            )
            self._conn.commit()
            logger.debug(f"Item saved: {item.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save item {item.id}: {e}")
            return False

    async def save_batch(self, items: list[Item]) -> int:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        if not items:
            return 0
        try:
            cursor = self._conn.cursor()
            rows = [
                (
                    item.id,
                    item.platform,
                    item.crawled_at.isoformat(),
                    json.dumps(item.raw_data, ensure_ascii=False) if item.raw_data else None,
                )
                for item in items
            ]
            sql = (
                "INSERT OR REPLACE INTO items "
                "(id, platform, crawled_at, raw_data) VALUES (?, ?, ?, ?)"
            )
            cursor.executemany(sql, rows)
            self._conn.commit()
            logger.debug(f"Batch saved {len(items)} items")
            return len(items)
        except Exception as e:
            logger.error(f"Failed to batch save items: {e}")
            return 0

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        try:
            query = "SELECT * FROM items WHERE 1=1"
            params: list[Any] = []
            for key, value in condition.items():
                query += f" AND {key} = ?"
                params.append(value)
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            items: list[Item] = []
            for row in rows:
                items.append(
                    Item(
                        id=row["id"],
                        platform=row["platform"],
                        crawled_at=datetime.fromisoformat(row["crawled_at"]),
                        raw_data=json.loads(row["raw_data"]) if row["raw_data"] else None,
                    )
                )
            logger.debug(f"Query returned {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"Failed to query items: {e}")
            return []

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        try:
            cursor = self._conn.cursor()
            set_clause = ", ".join(f"{k} = ?" for k in data.keys())
            params = list(data.values()) + [item_id]
            cursor.execute(f"UPDATE items SET {set_clause} WHERE id = ?", params)
            self._conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.debug(f"Item updated: {item_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update item {item_id}: {e}")
            return False

    async def delete(self, item_id: str) -> bool:
        if self._conn is None:
            msg = "Database connection not initialized"
            raise StorageException(msg)
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            self._conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.debug(f"Item deleted: {item_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("SQLite storage closed")
