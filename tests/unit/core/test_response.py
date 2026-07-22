from __future__ import annotations

import json
from datetime import timedelta

import pytest

from sucrawler.core.request import Request
from sucrawler.core.response import Response


class TestResponse:
    def test_create_response(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=200,
            text='{"key": "value"}',
            content=b'{"key": "value"}',
            headers={"Content-Type": "application/json"},
            elapsed=timedelta(seconds=0.5),
            meta={"platform": "test"},
        )
        assert response.request == request
        assert response.status_code == 200
        assert response.text == '{"key": "value"}'
        assert response.content == b'{"key": "value"}'
        assert response.headers == {"Content-Type": "application/json"}
        assert response.elapsed == timedelta(seconds=0.5)
        assert response.meta == {"platform": "test"}

    def test_ok_property_success(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=200,
            text="OK",
            content=b"OK",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        assert response.ok is True

    def test_ok_property_299(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=299,
            text="OK",
            content=b"OK",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        assert response.ok is True

    def test_ok_property_client_error(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=404,
            text="Not Found",
            content=b"Not Found",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        assert response.ok is False

    def test_ok_property_server_error(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=500,
            text="Internal Server Error",
            content=b"Internal Server Error",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        assert response.ok is False

    def test_json_method(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=200,
            text='{"key": "value", "number": 42}',
            content=b'{"key": "value", "number": 42}',
            headers={"Content-Type": "application/json"},
            elapsed=timedelta(seconds=0.1),
        )
        data = response.json()
        assert data["key"] == "value"
        assert data["number"] == 42

    def test_json_method_invalid_json(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=200,
            text="not json",
            content=b"not json",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        with pytest.raises(json.JSONDecodeError):
            response.json()

    def test_default_meta(self) -> None:
        request = Request(url="https://example.com")
        response = Response(
            request=request,
            status_code=200,
            text="",
            content=b"",
            headers={},
            elapsed=timedelta(seconds=0.1),
        )
        assert response.meta == {}
