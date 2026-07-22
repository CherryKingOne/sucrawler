from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from sucrawler.config.loader import load_config
from sucrawler.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Settings:
    config_dir = Path(__file__).parent.parent / "config"
    return load_config(config_path=str(config_dir), env="test")


@pytest.fixture
def sample_request_data() -> dict[str, Any]:
    return {
        "url": "https://example.com",
        "method": "GET",
        "headers": {"Content-Type": "application/json"},
        "params": {"page": 1},
        "data": None,
        "meta": {"platform": "test"},
        "timeout": 30,
        "proxy": None,
    }


@pytest.fixture
def sample_item_data() -> dict[str, Any]:
    return {
        "id": "test-123",
        "platform": "test",
        "raw_data": {"title": "Test Item", "content": "Test content"},
    }
