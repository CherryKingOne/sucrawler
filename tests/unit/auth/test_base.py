from __future__ import annotations

import pytest

from sucrawler.auth.base import BaseAuthenticator
from sucrawler.auth.exceptions import LoginFailedError, LoginTimeoutError
from sucrawler.auth.types import LoginStatus, LoginType


class FakeAuthenticator(BaseAuthenticator):
    """测试用的认证器实现。"""

    def __init__(
        self,
        login_result: bool = True,
        check_result: bool = False,
        login_type: LoginType = LoginType.QRCODE,
        timeout: int = 300,
    ) -> None:
        super().__init__(login_type=login_type, timeout=timeout)
        self._login_result = login_result
        self._check_result = check_result
        self.login_called = False
        self.check_called = False
        self.logout_called = False
        self.qrcode_called = False
        self.phone_called = False
        self.cookie_called = False

    @property
    def platform_name(self) -> str:
        return "test"

    async def _login_by_qrcode(self) -> bool:
        self.qrcode_called = True
        self.login_called = True
        return self._login_result

    async def _login_by_phone(self) -> bool:
        self.phone_called = True
        self.login_called = True
        return self._login_result

    async def _login_by_cookie(self) -> bool:
        self.cookie_called = True
        self.login_called = True
        return self._login_result

    async def _do_check_login_status(self) -> bool:
        self.check_called = True
        return self._check_result

    async def _do_logout(self) -> None:
        self.logout_called = True


class TestBaseAuthenticator:
    @pytest.mark.asyncio
    async def test_initial_status(self):
        auth = FakeAuthenticator()
        assert auth.status == LoginStatus.LOGGED_OUT
        assert auth.credential is None

    @pytest.mark.asyncio
    async def test_login_success_qrcode(self):
        auth = FakeAuthenticator(login_result=True, login_type=LoginType.QRCODE)
        result = await auth.login()
        assert result is True
        assert auth.status == LoginStatus.LOGGED_IN
        assert auth.qrcode_called is True
        assert auth.phone_called is False
        assert auth.credential is not None
        assert auth.credential.platform == "test"

    @pytest.mark.asyncio
    async def test_login_success_phone(self):
        auth = FakeAuthenticator(login_result=True, login_type=LoginType.PHONE)
        result = await auth.login()
        assert result is True
        assert auth.phone_called is True

    @pytest.mark.asyncio
    async def test_login_success_cookie(self):
        auth = FakeAuthenticator(login_result=True, login_type=LoginType.COOKIE)
        result = await auth.login()
        assert result is True
        assert auth.cookie_called is True

    @pytest.mark.asyncio
    async def test_login_failed(self):
        auth = FakeAuthenticator(login_result=False)
        with pytest.raises(LoginFailedError):
            await auth.login()
        assert auth.status == LoginStatus.LOGGED_OUT

    @pytest.mark.asyncio
    async def test_already_logged_in(self):
        auth = FakeAuthenticator(login_result=True)
        await auth.login()
        auth.login_called = False
        result = await auth.login()
        assert result is True
        assert auth.login_called is False

    @pytest.mark.asyncio
    async def test_check_login_status_true(self):
        auth = FakeAuthenticator(check_result=True)
        result = await auth.check_login_status()
        assert result is True
        assert auth.status == LoginStatus.LOGGED_IN
        assert auth.check_called is True

    @pytest.mark.asyncio
    async def test_check_login_status_false(self):
        auth = FakeAuthenticator(check_result=False)
        result = await auth.check_login_status()
        assert result is False
        assert auth.status == LoginStatus.LOGGED_OUT

    @pytest.mark.asyncio
    async def test_ensure_logged_in_already(self):
        auth = FakeAuthenticator(login_result=True, check_result=True)
        result = await auth.ensure_logged_in()
        assert result is True
        assert auth.login_called is False

    @pytest.mark.asyncio
    async def test_ensure_logged_in_need_login(self):
        auth = FakeAuthenticator(login_result=True, check_result=False)
        result = await auth.ensure_logged_in()
        assert result is True
        assert auth.login_called is True

    @pytest.mark.asyncio
    async def test_logout(self):
        auth = FakeAuthenticator(login_result=True)
        await auth.login()
        assert auth.status == LoginStatus.LOGGED_IN
        await auth.logout()
        assert auth.status == LoginStatus.LOGGED_OUT
        assert auth.credential is None
        assert auth.logout_called is True

    @pytest.mark.asyncio
    async def test_unsupported_login_type(self):
        auth = FakeAuthenticator()
        auth.login_type = "invalid"
        with pytest.raises(LoginFailedError, match="Unsupported login type"):
            await auth.login()
