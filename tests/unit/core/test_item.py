from __future__ import annotations

from datetime import datetime

from sucrawler.core.item import Item


class TestItem:
    def test_create_item(self) -> None:
        item = Item(platform="test", id="test-123")
        assert item.id == "test-123"
        assert item.platform == "test"
        assert item.raw_data is None
        assert isinstance(item.crawled_at, datetime)

    def test_default_id(self) -> None:
        item = Item(platform="test")
        assert item.id is None

    def test_default_crawled_at(self) -> None:
        before = datetime.now()
        item = Item(platform="test")
        after = datetime.now()
        assert before <= item.crawled_at <= after

    def test_default_raw_data(self) -> None:
        item = Item(platform="test")
        assert item.raw_data is None

    def test_create_item_with_raw_data(self) -> None:
        raw_data = {"title": "Test", "content": "Content"}
        item = Item(platform="test", raw_data=raw_data)
        assert item.raw_data == raw_data

    def test_item_model_validation(self) -> None:
        item = Item.model_validate({"platform": "test", "id": "123"})
        assert item.platform == "test"
        assert item.id == "123"
