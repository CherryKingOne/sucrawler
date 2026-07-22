from __future__ import annotations

import pytest

from sucrawler.cache.base import AbstractCache
from sucrawler.cache.factory import CacheFactory
from sucrawler.cache.local_cache import ExpiringLocalCache


class TestCacheFactory:
    def setup_method(self):
        CacheFactory.reset()

    def test_create_local_cache(self):
        cache = CacheFactory.create_cache("local")
        assert isinstance(cache, ExpiringLocalCache)
        assert isinstance(cache, AbstractCache)

    def test_create_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported cache type"):
            CacheFactory.create_cache("unsupported")

    def test_singleton_same_params(self):
        cache1 = CacheFactory.create_cache("local", cron_interval=10)
        cache2 = CacheFactory.create_cache("local", cron_interval=10)
        assert cache1 is cache2

    def test_different_params_different_instance(self):
        cache1 = CacheFactory.create_cache("local", cron_interval=10)
        cache2 = CacheFactory.create_cache("local", cron_interval=20)
        assert cache1 is not cache2

    def test_reset(self):
        cache1 = CacheFactory.create_cache("local")
        CacheFactory.reset()
        cache2 = CacheFactory.create_cache("local")
        assert cache1 is not cache2
