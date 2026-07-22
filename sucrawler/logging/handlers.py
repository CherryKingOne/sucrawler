from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from .formatters import DEFAULT_FORMAT, patcher


def configure_console_handler(level: str = "INFO", json_format: bool = False) -> None:
    logger.configure(patcher=patcher)  # type: ignore[arg-type]
    if json_format:
        from .formatters import json_sink
        logger.add(
            json_sink,
            level=level,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format=DEFAULT_FORMAT,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )


def configure_file_handler(
    log_dir: str | Path = "logs",
    level: str = "INFO",
    json_format: bool = False,
    rotation: str = "00:00",
    retention: str = "30 days",
) -> None:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    suffix = ".json" if json_format else ".log"
    file_path = log_path / f"sucrawler{suffix}"

    if json_format:
        from .formatters import json_file_sink_factory
        sink = json_file_sink_factory(str(file_path), rotation=rotation, retention=retention)
        logger.add(
            sink,
            level=level,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        logger.add(
            str(file_path),
            level=level,
            format=DEFAULT_FORMAT,
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )
