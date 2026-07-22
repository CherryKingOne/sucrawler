import os
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage
from sucrawler.core.item import Item
from sucrawler.storage.registry import register_storage


@register_storage("image")
class ImageStorage(BaseStorage):
    def __init__(self, config: Any = None) -> None:
        self.config = config or {}
        self.save_dir: str = self.config.get("save_dir", "images")
        self._ensure_dir()
        logger.info(f"Image storage initialized: {self.save_dir}")

    def _ensure_dir(self) -> None:
        try:
            Path(self.save_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            msg = f"Failed to create save directory: {e}"
            raise StorageException(msg) from e

    def _get_save_path(self, filename: str) -> str:
        return os.path.join(self.save_dir, filename)

    async def save(self, item: Item) -> bool:
        logger.warning("ImageStorage.save requires raw_data with url and content")
        if not item.raw_data:
            return False
        try:
            url = item.raw_data.get("url", "")
            content = item.raw_data.get("content")
            filename = item.raw_data.get("filename") or os.path.basename(url) or f"{item.id}.bin"
            save_path = self._get_save_path(filename)
            if content and isinstance(content, bytes):
                with open(save_path, "wb") as f:
                    f.write(content)
                logger.debug(f"Media saved: {save_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to save media: {e}")
            return False

    async def save_batch(self, items: list[Item]) -> int:
        if not items:
            return 0
        count = 0
        for item in items:
            if await self.save(item):
                count += 1
        return count

    async def query(self, condition: dict[str, Any]) -> list[Item]:
        logger.warning("ImageStorage.query not implemented")
        return []

    async def update(self, item_id: str, data: dict[str, Any]) -> bool:
        logger.warning("ImageStorage.update not implemented")
        return False

    async def delete(self, item_id: str) -> bool:
        logger.warning("ImageStorage.delete not implemented")
        return False
