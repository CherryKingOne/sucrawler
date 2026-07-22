from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from sucrawler.auth.credential_store import CredentialStore
from sucrawler.auth.types import LoginStatus, LoginType
from sucrawler.platforms.xiaohongshu.auth.xhs_login import XHSAuthenticator


class TestXHSAuthenticator:
    @pytest.fixture
    def temp_credential_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "credentials"

    @pytest.fixture
    def credential_store(self, temp_credential_dir: Path) -> CredentialStore:
        return CredentialStore(base_dir=temp_credential_dir)

    @pytest.fixture
    def mock_page(self) -> MagicMock:
        page = MagicMock()
        page.goto = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        page.evaluate = AsyncMock()
        return page

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        context = MagicMock()
        context.cookies = AsyncMock(return_value=[])
        context.add_cookies = AsyncMock()
        return context

    @pytest.fixture
    def auth(
        self,
        mock_page: MagicMock,
        mock_context: MagicMock,
        credential_store: CredentialStore,
    ) -> XHSAuthenticator:
        authenticator = XHSAuthenticator(
            login_type=LoginType.QRCODE,
            timeout=10,
            credential_store=credential_store,
        )
        authenticator.attach_browser(mock_page, mock_context)
        return authenticator

    def test_platform_name(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        assert auth.platform_name == "xiaohongshu"

    def test_attach_browser(
        self,
        mock_page: MagicMock,
        mock_context: MagicMock,
        credential_store: CredentialStore,
    ):
        auth = XHSAuthenticator(credential_store=credential_store)
        assert auth._page is None
        assert auth._browser_context is None

        auth.attach_browser(mock_page, mock_context)
        assert auth._page is mock_page
        assert auth._browser_context is mock_context

    @pytest.mark.asyncio
    async def test_check_login_status_no_page(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        result = await auth.check_login_status()
        assert result is False
        assert auth.status == LoginStatus.LOGGED_OUT

    @pytest.mark.asyncio
    async def test_check_login_status_via_ui(self, auth: XHSAuthenticator, mock_page: MagicMock):
        mock_element = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        result = await auth.check_login_status()
        assert result is True
        assert auth.status == LoginStatus.LOGGED_IN

    @pytest.mark.asyncio
    async def test_check_login_status_via_cookie(
        self,
        auth: XHSAuthenticator,
        mock_context: MagicMock,
    ):
        mock_context.cookies = AsyncMock(return_value=[
            {"name": "web_session", "value": "test_session", "domain": ".xiaohongshu.com"}
        ])

        result = await auth.check_login_status()
        assert result is True
        assert auth.status == LoginStatus.LOGGED_IN

    @pytest.mark.asyncio
    async def test_check_login_status_false(self, auth: XHSAuthenticator):
        result = await auth.check_login_status()
        assert result is False
        assert auth.status == LoginStatus.LOGGED_OUT

    @pytest.mark.asyncio
    async def test_login_by_cookie_success(
        self,
        mock_page: MagicMock,
        mock_context: MagicMock,
        credential_store: CredentialStore,
    ):
        mock_context.cookies = AsyncMock(return_value=[
            {"name": "web_session", "value": "test123", "domain": ".xiaohongshu.com"}
        ])
        mock_element = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        auth = XHSAuthenticator(
            login_type=LoginType.COOKIE,
            cookie_str="web_session=test123",
            credential_store=credential_store,
        )
        auth.attach_browser(mock_page, mock_context)

        result = await auth.login()
        assert result is True
        assert auth.status == LoginStatus.LOGGED_IN

    @pytest.mark.asyncio
    async def test_login_by_cookie_no_context(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(
            login_type=LoginType.COOKIE,
            cookie_str="",
            credential_store=credential_store,
        )
        result = await auth._login_by_cookie()
        assert result is False

    @pytest.mark.asyncio
    async def test_login_by_qrcode_no_page(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(
            login_type=LoginType.QRCODE,
            credential_store=credential_store,
        )
        result = await auth._login_by_qrcode()
        assert result is False

    @pytest.mark.asyncio
    async def test_login_by_phone_no_page(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(
            login_type=LoginType.PHONE,
            credential_store=credential_store,
        )
        result = await auth._login_by_phone()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_cookies(self, auth: XHSAuthenticator, mock_context: MagicMock):
        test_cookies = [
            {"name": "a1", "value": "123", "domain": ".xiaohongshu.com"},
            {"name": "web_session", "value": "sess", "domain": ".xiaohongshu.com"},
        ]
        mock_context.cookies = AsyncMock(return_value=test_cookies)

        cookies = await auth._get_cookies()
        assert len(cookies) == 2
        assert cookies[0]["name"] == "a1"

    @pytest.mark.asyncio
    async def test_get_cookies_no_context(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        cookies = await auth._get_cookies()
        assert cookies == []

    def test_has_web_session_true(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        cookies = [
            {"name": "web_session", "value": "test", "domain": ".xiaohongshu.com"}
        ]
        assert auth._has_web_session(cookies) is True

    def test_has_web_session_false(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        cookies = [
            {"name": "a1", "value": "test", "domain": ".xiaohongshu.com"}
        ]
        assert auth._has_web_session(cookies) is False

    def test_has_web_session_empty_value(self, credential_store: CredentialStore):
        auth = XHSAuthenticator(credential_store=credential_store)
        cookies = [
            {"name": "web_session", "value": "", "domain": ".xiaohongshu.com"}
        ]
        assert auth._has_web_session(cookies) is False

    @pytest.mark.asyncio
    async def test_load_credential(
        self,
        auth: XHSAuthenticator,
        mock_context: MagicMock,
    ):
        from sucrawler.auth.types import CredentialInfo

        credential = CredentialInfo(
            platform="xiaohongshu",
            login_type=LoginType.COOKIE,
            status=LoginStatus.LOGGED_IN,
            cookies=[{"name": "web_session", "value": "test", "domain": ".xiaohongshu.com"}],
        )

        result = await auth.load_credential(credential)
        assert result is True
        mock_context.add_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_credential_no_context(self, credential_store: CredentialStore):
        from sucrawler.auth.types import CredentialInfo

        auth = XHSAuthenticator(credential_store=credential_store)
        credential = CredentialInfo(
            platform="xiaohongshu",
            login_type=LoginType.COOKIE,
            status=LoginStatus.LOGGED_IN,
            cookies=[{"name": "web_session", "value": "test"}],
        )

        result = await auth.load_credential(credential)
        assert result is False
