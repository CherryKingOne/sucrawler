from __future__ import annotations

import pytest

from sucrawler.auth.exceptions import (
    AuthError,
    InvalidCredentialError,
    LoginFailedError,
    LoginTimeoutError,
    QRCodeExpiredError,
)


class TestAuthExceptions:
    def test_auth_error(self):
        with pytest.raises(AuthError):
            raise AuthError("test")

    def test_login_failed(self):
        with pytest.raises(AuthError):
            raise LoginFailedError("login failed")

    def test_login_timeout(self):
        with pytest.raises(AuthError):
            raise LoginTimeoutError("timeout")

    def test_qrcode_expired(self):
        with pytest.raises(AuthError):
            raise QRCodeExpiredError("expired")

    def test_invalid_credential(self):
        with pytest.raises(AuthError):
            raise InvalidCredentialError("invalid")

    def test_error_message(self):
        try:
            raise LoginFailedError("custom message")
        except LoginFailedError as e:
            assert str(e) == "custom message"
