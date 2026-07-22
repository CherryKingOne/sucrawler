from __future__ import annotations

from sucrawler.core.request import Request


class TestRequest:
    def test_create_request(self) -> None:
        req = Request(url="https://example.com")
        assert req.url == "https://example.com"
        assert req.method == "GET"
        assert req.headers == {}
        assert req.params == {}
        assert req.data is None
        assert req.meta == {}
        assert req.timeout == 30
        assert req.proxy is None

    def test_create_request_with_params(self) -> None:
        req = Request(
            url="https://example.com",
            method="post",
            headers={"X-Test": "value"},
            params={"key": "value"},
            data={"foo": "bar"},
            meta={"platform": "test"},
            timeout=60,
            proxy="http://proxy:8080",
        )
        assert req.url == "https://example.com"
        assert req.method == "POST"
        assert req.headers == {"X-Test": "value"}
        assert req.params == {"key": "value"}
        assert req.data == {"foo": "bar"}
        assert req.meta == {"platform": "test"}
        assert req.timeout == 60
        assert req.proxy == "http://proxy:8080"

    def test_to_dict(self) -> None:
        req = Request(
            url="https://example.com",
            method="GET",
            headers={"X-Test": "value"},
            params={"page": 1},
            meta={"platform": "test"},
        )
        result = req.to_dict()
        assert isinstance(result, dict)
        assert result["url"] == "https://example.com"
        assert result["method"] == "GET"
        assert result["headers"] == {"X-Test": "value"}
        assert result["params"] == {"page": 1}
        assert result["meta"] == {"platform": "test"}
        assert "timeout" in result
        assert "proxy" in result

    def test_method_uppercase(self) -> None:
        req = Request(url="https://example.com", method="get")
        assert req.method == "GET"

        req2 = Request(url="https://example.com", method="Post")
        assert req2.method == "POST"
