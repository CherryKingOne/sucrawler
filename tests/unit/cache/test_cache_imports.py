from __future__ import annotations


def test_cache_imports():
    from sucrawler.cache import AbstractCache, CacheFactory, ExpiringLocalCache

    assert AbstractCache is not None
    assert CacheFactory is not None
    assert ExpiringLocalCache is not None
