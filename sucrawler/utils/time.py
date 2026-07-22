import time
from datetime import datetime, timezone


def timestamp_now() -> int:
    return int(time.time())


def timestamp_now_ms() -> int:
    return int(time.time() * 1000)


def timestamp_to_datetime(timestamp: int, tz: timezone | None = None) -> datetime:
    ts: float = float(timestamp)
    if timestamp > 10**12:
        ts = ts / 1000
    return datetime.fromtimestamp(ts, tz=tz)


def datetime_to_timestamp(dt: datetime) -> int:
    return int(dt.timestamp())


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(fmt)


def parse_datetime(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    return datetime.strptime(date_str, fmt)


def format_timestamp(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    dt = timestamp_to_datetime(timestamp)
    return format_datetime(dt, fmt)


class Timer:
    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0

    def start(self) -> None:
        self._start = time.perf_counter()

    def stop(self) -> float:
        self._end = time.perf_counter()
        return self.elapsed

    @property
    def elapsed(self) -> float:
        return self._end - self._start

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.stop()


def time_elapsed(start_time: float) -> float:
    return time.perf_counter() - start_time
