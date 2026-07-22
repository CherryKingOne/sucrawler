from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from .handlers import configure_console_handler, configure_file_handler

if TYPE_CHECKING:
    from loguru import Logger

_initialized = False


def setup_logging(
    log_level: str = "INFO",
    log_dir: str | Path = "logs",
    json_format: bool = False,
) -> None:
    global _initialized
    logger.remove()
    configure_console_handler(level=log_level, json_format=json_format)
    configure_file_handler(log_dir=log_dir, level=log_level, json_format=json_format)
    _initialized = True


def get_logger(name: str) -> Logger:
    if not _initialized:
        setup_logging()
    return logger.bind(module=name)
