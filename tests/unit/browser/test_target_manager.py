from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sucrawler.browser.cdp.connection import CDPConnection
from sucrawler.browser.cdp.target import TargetManager


class TestTargetManager:
    def test_init(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)
        assert manager.targets == []

    @pytest.mark.asyncio
    async def test_refresh(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        targets_data = [
            {"id": "1", "type": "page", "url": "https://a.com"},
            {"id": "2", "type": "page", "url": "https://b.com"},
            {"id": "3", "type": "browser", "url": ""},
        ]

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=targets_data):
            result = await manager.refresh()

        assert len(result) == 3
        assert len(manager.targets) == 3

    @pytest.mark.asyncio
    async def test_get_pages(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        targets_data = [
            {"id": "1", "type": "page", "url": "https://a.com"},
            {"id": "2", "type": "page", "url": "https://b.com"},
            {"id": "3", "type": "browser", "url": ""},
        ]

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=targets_data):
            pages = await manager.get_pages()

        assert len(pages) == 2
        assert all(p["type"] == "page" for p in pages)

    @pytest.mark.asyncio
    async def test_get_first_page(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        targets_data = [
            {"id": "1", "type": "page", "url": "https://a.com"},
            {"id": "2", "type": "page", "url": "https://b.com"},
        ]

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=targets_data):
            page = await manager.get_first_page()

        assert page is not None
        assert page["id"] == "1"

    @pytest.mark.asyncio
    async def test_get_first_page_none(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=[]):
            page = await manager.get_first_page()

        assert page is None

    @pytest.mark.asyncio
    async def test_find_page_by_url(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        targets_data = [
            {"id": "1", "type": "page", "url": "https://example.com/page1"},
            {"id": "2", "type": "page", "url": "https://test.com/page2"},
        ]

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=targets_data):
            page = await manager.find_page_by_url(r"example\.com")

        assert page is not None
        assert page["id"] == "1"

    @pytest.mark.asyncio
    async def test_new_page(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        new_target = {"id": "new-id", "type": "page", "url": "about:blank"}
        with patch.object(conn, "new_page", new_callable=AsyncMock, return_value=new_target):
            page = await manager.new_page("about:blank")

        assert page["id"] == "new-id"
        assert len(manager.targets) == 1

    @pytest.mark.asyncio
    async def test_close_page(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)
        manager._targets = [
            {"id": "1", "type": "page", "url": "https://a.com"},
            {"id": "2", "type": "page", "url": "https://b.com"},
        ]

        with patch.object(conn, "close_page", new_callable=AsyncMock, return_value=True):
            result = await manager.close_page("1")

        assert result is True
        assert len(manager.targets) == 1
        assert manager.targets[0]["id"] == "2"

    @pytest.mark.asyncio
    async def test_close_all_pages(self):
        conn = CDPConnection(debug_port=9222)
        manager = TargetManager(conn)

        targets_data = [
            {"id": "1", "type": "page", "url": "https://a.com"},
            {"id": "2", "type": "page", "url": "https://b.com"},
            {"id": "3", "type": "browser", "url": ""},
        ]

        with patch.object(conn, "list_targets", new_callable=AsyncMock, return_value=targets_data):
            with patch.object(conn, "close_page", new_callable=AsyncMock, return_value=True):
                count = await manager.close_all_pages()

        assert count == 2
