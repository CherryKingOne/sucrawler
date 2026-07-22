from __future__ import annotations

import pytest

from sucrawler.auth import cookie_utils


class TestCookieUtils:
    def test_cookies_list_to_string(self):
        cookies = [
            {"name": "a", "value": "1"},
            {"name": "b", "value": "2"},
            {"name": "c", "value": "3"},
        ]
        result = cookie_utils.cookies_list_to_string(cookies)
        assert result == "a=1; b=2; c=3"

    def test_cookies_list_to_string_empty(self):
        assert cookie_utils.cookies_list_to_string([]) == ""

    def test_string_to_cookies_list(self):
        cookie_str = "a=1; b=2; c=3"
        result = cookie_utils.string_to_cookies_list(cookie_str, domain=".example.com")
        assert len(result) == 3
        assert result[0]["name"] == "a"
        assert result[0]["value"] == "1"
        assert result[0]["domain"] == ".example.com"
        assert result[0]["path"] == "/"

    def test_string_to_cookies_list_empty(self):
        result = cookie_utils.string_to_cookies_list("")
        assert result == []

    def test_cookies_list_to_dict(self):
        cookies = [
            {"name": "a", "value": "1"},
            {"name": "b", "value": "2"},
        ]
        result = cookie_utils.cookies_list_to_dict(cookies)
        assert result == {"a": "1", "b": "2"}

    def test_dict_to_cookies_list(self):
        cookie_dict = {"a": "1", "b": "2"}
        result = cookie_utils.dict_to_cookies_list(cookie_dict, domain=".xhs.com")
        assert len(result) == 2
        assert result[0]["domain"] == ".xhs.com"
        assert {c["name"]: c["value"] for c in result} == {"a": "1", "b": "2"}

    def test_filter_cookies_by_domain_exact(self):
        cookies = [
            {"name": "a", "value": "1", "domain": ".xhs.com"},
            {"name": "b", "value": "2", "domain": ".douyin.com"},
            {"name": "c", "value": "3", "domain": ".xhs.com"},
        ]
        result = cookie_utils.filter_cookies_by_domain(cookies, ".xhs.com")
        assert len(result) == 2

    def test_filter_cookies_by_domain_subdomain(self):
        cookies = [
            {"name": "a", "value": "1", "domain": ".xhs.com"},
        ]
        result = cookie_utils.filter_cookies_by_domain(cookies, "www.xhs.com")
        assert len(result) == 1

    def test_merge_cookies(self):
        cookies1 = [
            {"name": "a", "value": "1", "domain": ".x.com", "path": "/"},
            {"name": "b", "value": "2", "domain": ".x.com", "path": "/"},
        ]
        cookies2 = [
            {"name": "b", "value": "new2", "domain": ".x.com", "path": "/"},
            {"name": "c", "value": "3", "domain": ".x.com", "path": "/"},
        ]
        result = cookie_utils.merge_cookies(cookies1, cookies2)
        result_dict = {c["name"]: c["value"] for c in result}
        assert result_dict["a"] == "1"
        assert result_dict["b"] == "new2"
        assert result_dict["c"] == "3"

    def test_roundtrip_list_string_list(self):
        original = [
            {"name": "a", "value": "1"},
            {"name": "b", "value": "2"},
        ]
        s = cookie_utils.cookies_list_to_string(original)
        back = cookie_utils.string_to_cookies_list(s)
        assert {c["name"]: c["value"] for c in back} == {"a": "1", "b": "2"}

    def test_roundtrip_list_dict_list(self):
        original = [
            {"name": "a", "value": "1"},
            {"name": "b", "value": "2"},
        ]
        d = cookie_utils.cookies_list_to_dict(original)
        back = cookie_utils.dict_to_cookies_list(d)
        assert {c["name"]: c["value"] for c in back} == {"a": "1", "b": "2"}
