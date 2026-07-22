from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .trace import get_trace_id

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<yellow>trace_id={extra[trace_id]}</yellow> - "
    "<level>{message}</level>"
)


def _default_json_serializer(obj: Any) -> Any:
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def _build_json_log_entry(record: dict[str, Any]) -> dict[str, Any]:
    trace_id = get_trace_id()
    extra = dict(record.get("extra", {}))
    log_entry: dict[str, Any] = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
        "trace_id": trace_id,
        "message": record["message"],
    }
    if record.get("exception") is not None:
        log_entry["exception"] = str(record["exception"])
    if extra:
        log_entry["extra"] = {k: v for k, v in extra.items() if k != "trace_id"}
    return log_entry


def json_sink(message: Any) -> None:
    record = message.record
    log_entry = _build_json_log_entry(record)
    json_str = json.dumps(
        log_entry, default=_default_json_serializer, ensure_ascii=False
    )
    sys.stderr.write(json_str + "\n")
    sys.stderr.flush()


class JsonFileSink:
    def __init__(
        self,
        path: str,
        rotation: str = "00:00",
        retention: str = "30 days",
        encoding: str = "utf-8",
    ) -> None:
        self._path = Path(path)
        self._rotation = rotation
        self._retention = retention
        self._encoding = encoding
        self._current_file = self._path
        self._file = self._open_file(self._current_file)
        self._next_rotation = self._compute_next_rotation()

    def _open_file(self, path: Path) -> Any:
        path.parent.mkdir(parents=True, exist_ok=True)
        return open(path, "a", encoding=self._encoding)

    def _compute_next_rotation(self) -> datetime:
        now = datetime.now()
        if self._rotation == "00:00":
            tomorrow = now + timedelta(days=1)
            return datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        return now + timedelta(days=1)

    def _rotate(self) -> None:
        self._file.close()
        timestamp = datetime.now().strftime("%Y-%m-%d")
        rotated_path = self._path.with_suffix(f".{timestamp}{self._path.suffix}")
        if self._current_file.exists():
            self._current_file.rename(rotated_path)
        self._current_file = self._path
        self._file = self._open_file(self._current_file)
        self._next_rotation = self._compute_next_rotation()
        self._cleanup_old_files()

    def _cleanup_old_files(self) -> None:
        try:
            retention_days = 30
            parts = self._retention.split()
            if len(parts) == 2 and parts[1] in ("day", "days"):
                retention_days = int(parts[0])
            cutoff = datetime.now() - timedelta(days=retention_days)
            for file_path in self._path.parent.glob(f"{self._path.stem}.*{self._path.suffix}"):
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        file_path.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    def write(self, message: Any) -> None:
        if datetime.now() >= self._next_rotation:
            self._rotate()
        record = message.record
        log_entry = _build_json_log_entry(record)
        json_str = json.dumps(
            log_entry, default=_default_json_serializer, ensure_ascii=False
        )
        self._file.write(json_str + "\n")
        self._file.flush()

    def stop(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()


def json_file_sink_factory(
    path: str,
    rotation: str = "00:00",
    retention: str = "30 days",
) -> JsonFileSink:
    return JsonFileSink(path, rotation=rotation, retention=retention)


def patcher(record: dict[str, Any]) -> None:
    extra = record.get("extra")
    if extra is None:
        extra = {}
        record["extra"] = extra
    if "trace_id" not in extra:
        extra["trace_id"] = get_trace_id()
