from __future__ import annotations

import time

import pytest

from sucrawler.cache.local_cache import ExpiringLocalCache


class TestExpiringLocalCache:
    def test_set_and_get(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("key1", "value1", expire_time=100)
        assert cache.get("key1") == "value1"

    def test_get_nonexistent(self):
        cache = ExpiringLocalCache(cron_interval=100)
        assert cache.get("nonexistent") is None

    def test_expired_key(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("key1", "value1", expire_time=0)
        time.sleep(0.1)
        assert cache.get("key1") is None

    def test_delete(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("key1", "value1", expire_time=100)
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.delete("nonexistent")

    def test_clear(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("key1", "value1", expire_time=100)
        cache.set("key2", "value2", expire_time=100)
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_keys_all(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("a1", "v1", expire_time=100)
        cache.set("a2", "v2", expire_time=100)
        cache.set("b1", "v3", expire_time=100)
        keys = cache.keys("*")
        assert len(keys) == 3

    def test_keys_pattern_contains(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("xhs_abc", "v1", expire_time=100)
        cache.set("xhs_def", "v2", expire_time=100)
        cache.set("dy_abc", "v3", expire_time=100)
        keys = cache.keys("xhs_")
        assert len(keys) == 2
        assert all("xhs_" in k for k in keys)

    def test_keys_pattern_wildcard(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("user_123_name", "v1", expire_time=100)
        cache.set("user_456_name", "v2", expire_time=100)
        cache.set("post_123_title", "v3", expire_time=100)
        keys = cache.keys("user_*_name")
        assert len(keys) == 2

    def test_clear_expired(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("key1", "v1", expire_time=0)
        cache.set("key2", "v2", expire_time=100)
        time.sleep(0.1)
        cache._clear_expired()
        assert cache.get("key1") is None
        assert cache.get("key2") == "v2"

    def test_different_value_types(self):
        cache = ExpiringLocalCache(cron_interval=100)
        cache.set("str", "hello", expire_time=100)
        cache.set("int", 42, expire_time=100)
        cache.set("dict", {"a": 1}, expire_time=100)
        cache.set("list", [1, 2, 3], expire_time=100)
        assert cache.get("str") == "hello"
        assert cache.get("int") == 42
        assert cache.get("dict") == {"a": 1}
        assert cache.get("list") == [1, 2, 3]
