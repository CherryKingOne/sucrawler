from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sucrawler.core.item import Item
from sucrawler.storage.file.csv_storage import CSVStorage


@pytest.fixture
def temp_csv_file() -> str:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def csv_storage(temp_csv_file: str) -> CSVStorage:
    return CSVStorage({"file_path": temp_csv_file, "append": True})


@pytest.fixture
def sample_item() -> Item:
    return Item(
        id="test-001",
        platform="test",
        raw_data={"title": "Test Title", "content": "Test Content"},
    )


class TestCSVStorage:
    @pytest.mark.asyncio
    async def test_save(self, csv_storage: CSVStorage, sample_item: Item) -> None:
        result = await csv_storage.save(sample_item)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_batch(self, csv_storage: CSVStorage) -> None:
        items = [
            Item(id=f"test-{i}", platform="test", raw_data={"index": i})
            for i in range(5)
        ]
        count = await csv_storage.save_batch(items)
        assert count == 5

    @pytest.mark.asyncio
    async def test_save_batch_empty(self, csv_storage: CSVStorage) -> None:
        count = await csv_storage.save_batch([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_query(self, csv_storage: CSVStorage, sample_item: Item) -> None:
        await csv_storage.save(sample_item)
        results = await csv_storage.query({"platform": "test"})
        assert len(results) >= 1
        assert results[0].id == "test-001"
        assert results[0].platform == "test"
        assert results[0].raw_data is not None
        assert results[0].raw_data["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_query_empty_result(self, csv_storage: CSVStorage) -> None:
        results = await csv_storage.query({"platform": "nonexistent"})
        assert results == []

    @pytest.mark.asyncio
    async def test_query_all(self, csv_storage: CSVStorage) -> None:
        items = [
            Item(id=f"test-{i}", platform="test", raw_data={"index": i})
            for i in range(3)
        ]
        await csv_storage.save_batch(items)
        results = await csv_storage.query({})
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_save_and_query_roundtrip(self, csv_storage: CSVStorage) -> None:
        item = Item(
            id="roundtrip-1",
            platform="test_platform",
            raw_data={"key": "value", "number": 42},
        )
        await csv_storage.save(item)
        results = await csv_storage.query({"id": "roundtrip-1"})
        assert len(results) == 1
        assert results[0].id == "roundtrip-1"
        assert results[0].platform == "test_platform"
        assert results[0].raw_data == {"key": "value", "number": 42}
