from __future__ import annotations

from typing import Any

from sucrawler.common.exceptions import ParseException
from sucrawler.core.interfaces.parser import BaseParser
from sucrawler.core.response import Response


class BaseParserImpl(BaseParser):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def parse(self, response: Response) -> dict[str, Any]:
        try:
            return await self._do_parse(response)
        except Exception as e:
            msg = f"Failed to parse response from {response.request.url}"
            raise ParseException(msg) from e

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        msg = "_do_parse must be implemented by subclass"
        raise NotImplementedError(msg)
