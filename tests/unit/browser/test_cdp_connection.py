from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sucrawler.browser.cdp.connection import CDPConnection
from sucrawler.browser.exceptions import BrowserConnectionError


class TestCDPConnection:
    def test_init(self):
        conn = CDPConnection(debug_port=9222)
        assert conn.debug_port == 9222
        assert conn.host == "localhost"
        assert conn.ws_url is None
        assert conn.browser_info is None

    def test_init_custom_host(self):
        conn = CDPConnection(debug_port=9222, host="127.0.0.1")
        assert conn.host == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        conn = CDPConnection(debug_port=19999)
        result = await conn.test_connection(timeout=1.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_browser_info_success(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Browser": "Chrome/120.0.0.0",
            "Protocol-Version": "1.3",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/abc123",
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            info = await conn.fetch_browser_info()

        assert info["Browser"] == "Chrome/120.0.0.0"
        assert conn.browser_info == info
        assert conn.ws_url == "ws://localhost:9222/devtools/browser/abc123"

    @pytest.mark.asyncio
    async def test_fetch_browser_info_http_error(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(BrowserConnectionError):
                await conn.fetch_browser_info()

    @pytest.mark.asyncio
    async def test_fetch_browser_info_network_error(self):
        conn = CDPConnection(debug_port=9222)

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("fail")):
            with pytest.raises(BrowserConnectionError):
                await conn.fetch_browser_info()

    @pytest.mark.asyncio
    async def test_get_websocket_url_cached(self):
        conn = CDPConnection(debug_port=9222)
        conn._ws_url = "ws://cached:9222/url"

        url = await conn.get_websocket_url()
        assert url == "ws://cached:9222/url"

    @pytest.mark.asyncio
    async def test_get_websocket_url_connect_existing(self):
        conn = CDPConnection(debug_port=9222)
        url = await conn.get_websocket_url(connect_existing=True)
        assert url == "ws://localhost:9222/devtools/browser"
        assert conn.ws_url == "ws://localhost:9222/devtools/browser"

    @pytest.mark.asyncio
    async def test_get_websocket_url_via_json_version(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/xyz",
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            url = await conn.get_websocket_url()

        assert url == "ws://localhost:9222/devtools/browser/xyz"

    @pytest.mark.asyncio
    async def test_list_targets(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "1", "type": "page", "url": "https://example.com"},
            {"id": "2", "type": "page", "url": "https://test.com"},
        ]

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            targets = await conn.list_targets()

        assert len(targets) == 2
        assert targets[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_new_page(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "new-page-id",
            "type": "page",
            "url": "about:blank",
        }

        with patch("httpx.AsyncClient.put", new_callable=AsyncMock, return_value=mock_response):
            page = await conn.new_page("about:blank")

        assert page["id"] == "new-page-id"

    @pytest.mark.asyncio
    async def test_close_page_success(self):
        conn = CDPConnection(debug_port=9222)
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await conn.close_page("page-id-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_close_page_network_error(self):
        conn = CDPConnection(debug_port=9222)

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("fail")):
            result = await conn.close_page("page-id-123")

        assert result is False

    def test_test_sync_failure(self):
        conn = CDPConnection(debug_port=19999)
        result = conn._test_sync(timeout=1.0)
        assert result is False
