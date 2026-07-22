from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from sucrawler.auth.types import CredentialInfo, LoginStatus, LoginType


class TestLoginType:
    def test_qrcode(self):
        assert LoginType.QRCODE.value == "qrcode"

    def test_phone(self):
        assert LoginType.PHONE.value == "phone"

    def test_cookie(self):
        assert LoginType.COOKIE.value == "cookie"


class TestLoginStatus:
    def test_logged_out(self):
        assert LoginStatus.LOGGED_OUT.value == "logged_out"

    def test_logging_in(self):
        assert LoginStatus.LOGGING_IN.value == "logging_in"

    def test_logged_in(self):
        assert LoginStatus.LOGGED_IN.value == "logged_in"

    def test_expired(self):
        assert LoginStatus.EXPIRED.value == "expired"


class TestCredentialInfo:
    def test_default_values(self):
        cred = CredentialInfo(platform="xhs", login_type=LoginType.QRCODE)
        assert cred.platform == "xhs"
        assert cred.login_type == LoginType.QRCODE
        assert cred.status == LoginStatus.LOGGED_OUT
        assert cred.cookies == []
        assert isinstance(cred.created_at, datetime)
        assert isinstance(cred.updated_at, datetime)

    def test_is_valid_logged_in(self):
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_IN,
        )
        assert cred.is_valid() is True

    def test_is_valid_logged_out(self):
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_OUT,
        )
        assert cred.is_valid() is False

    def test_is_valid_expired_status(self):
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.QRCODE,
            status=LoginStatus.EXPIRED,
        )
        assert cred.is_valid() is False

    def test_is_valid_with_expires_at_future(self):
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_IN,
            expires_at=datetime.now() + timedelta(days=1),
        )
        assert cred.is_valid() is True

    def test_is_valid_with_expires_at_past(self):
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_IN,
            expires_at=datetime.now() - timedelta(days=1),
        )
        assert cred.is_valid() is False

    def test_with_cookies(self):
        cookies = [
            {"name": "session", "value": "abc123", "domain": ".xhs.com"},
            {"name": "web_session", "value": "xyz", "domain": ".xhs.com"},
        ]
        cred = CredentialInfo(
            platform="xhs",
            login_type=LoginType.COOKIE,
            status=LoginStatus.LOGGED_IN,
            cookies=cookies,
        )
        assert len(cred.cookies) == 2
        assert cred.cookies[0]["name"] == "session"
