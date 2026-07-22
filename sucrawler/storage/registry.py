from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger

from sucrawler.common.exceptions import StorageException
from sucrawler.core.interfaces.storage import BaseStorage

T = TypeVar("T", bound=type[BaseStorage])


class StorageRegistry:
    _storages: dict[str, type[BaseStorage]] = {}

    @classmethod
    def register(cls, name: str, storage_cls: type[BaseStorage]) -> None:
        if name in cls._storages:
            logger.warning(f"Storage '{name}' already registered, overwriting")
        cls._storages[name] = storage_cls
        logger.debug(f"Storage '{name}' registered successfully")

    @classmethod
    def get(cls, name: str, config: Any = None) -> BaseStorage:
        if name not in cls._storages:
            msg = f"Storage '{name}' not found. Available: {cls.list_storages()}"
            raise StorageException(msg)
        storage_cls = cls._storages[name]
        return storage_cls(config)

    @classmethod
    def list_storages(cls) -> list[str]:
        return sorted(cls._storages.keys())


def register_storage(name: str) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        StorageRegistry.register(name, cls)
        return cls

    return decorator
