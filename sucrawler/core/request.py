from __future__ import annotations

from typing import Any

from sucrawler.common.constants import DEFAULT_TIMEOUT, GET
from sucrawler.common.types import HeadersType, MetaType, ParamsType


class Request:
    def __init__(
        self,
        url: str,
        method: str = GET,
        headers: HeadersType | None = None,
        params: ParamsType | None = None,
        data: Any = None,
        meta: MetaType | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        proxy: str | None = None,
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.params = params or {}
        self.data = data
        self.meta = meta or {}
        self.timeout = timeout
        self.proxy = proxy

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "params": self.params,
            "data": self.data,
            "meta": self.meta,
            "timeout": self.timeout,
            "proxy": self.proxy,
        }
