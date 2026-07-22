from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from sucrawler.common.types import HeadersType, MetaType
from sucrawler.core.request import Request


class Response:
    def __init__(
        self,
        request: Request,
        status_code: int,
        text: str,
        content: bytes,
        headers: HeadersType,
        elapsed: timedelta,
        meta: MetaType | None = None,
    ) -> None:
        self.request = request
        self.status_code = status_code
        self.text = text
        self.content = content
        self.headers = headers
        self.elapsed = elapsed
        self.meta = meta or {}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        return json.loads(self.text)
