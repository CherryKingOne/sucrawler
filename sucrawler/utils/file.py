import os
import tempfile
from pathlib import Path


def ensure_dir(dir_path: str) -> None:
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def safe_write(file_path: str, content: str | bytes, encoding: str = "utf-8") -> None:
    dir_path = os.path.dirname(file_path)
    if dir_path:
        ensure_dir(dir_path)
    temp_path = f"{file_path}.tmp"
    if isinstance(content, bytes):
        with open(temp_path, "wb") as f:
            f.write(content)
    else:
        with open(temp_path, "w", encoding=encoding) as f:
            f.write(content)
    os.replace(temp_path, file_path)


def safe_write_async(file_path: str, content: str | bytes) -> None:
    safe_write(file_path, content)


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.2f} {units[unit_index]}"


def get_file_size(file_path: str) -> int:
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path)


def dir_exists(dir_path: str) -> bool:
    return os.path.isdir(dir_path)


def get_temp_dir() -> str:
    return tempfile.gettempdir()


def get_temp_file(suffix: str = "", prefix: str = "tmp") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path
