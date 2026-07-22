from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.core.base.base_parser import BaseParserImpl
from sucrawler.core.response import Response


class JsonParser(BaseParserImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._data: dict[str, Any] | None = None

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        logger.debug(f"Parsing JSON response from {response.request.url}")
        data = response.json()
        if isinstance(data, dict):
            self._data = data
        else:
            self._data = {"data": data}
        return self._data

    def jsonpath(self, path: str) -> list[Any]:
        if self._data is None:
            msg = "Data not initialized. Call parse() first."
            raise RuntimeError(msg)
        return self._resolve_path(path)

    def jsonpath_one(self, path: str) -> Any:
        results = self.jsonpath(path)
        return results[0] if results else None

    def _resolve_path(self, path: str) -> list[Any]:
        if self._data is None:
            return []

        parts = path.split(".")
        results: list[Any] = [self._data]

        for part in parts:
            temp_results: list[Any] = []
            for result in results:
                if isinstance(result, dict):
                    if part == "*":
                        temp_results.extend(result.values())
                    elif part in result:
                        temp_results.append(result[part])
                elif isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            if part == "*":
                                temp_results.extend(item.values())
                            elif part in item:
                                temp_results.append(item[part])
            results = temp_results

        return results
