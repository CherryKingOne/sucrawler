from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sucrawler.auth.credential_store import CredentialStore
from sucrawler.auth.exceptions import InvalidCredentialError
from sucrawler.auth.types import CredentialInfo, LoginStatus, LoginType


class TestCredentialStore:
    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "credentials"

    @pytest.fixture
    def store(self, temp_dir: Path) -> CredentialStore:
        return CredentialStore(base_dir=temp_dir)

    @pytest.fixture
    def valid_credential(self) -> CredentialInfo:
        return CredentialInfo(
            platform="xiaohongshu",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_IN,
            cookies=[{"name": "web_session", "value": "test123", "domain": ".xiaohongshu.com"}],
        )

    @pytest.fixture
    def expired_credential(self) -> CredentialInfo:
        return CredentialInfo(
            platform="xiaohongshu",
            login_type=LoginType.COOKIE,
            status=LoginStatus.LOGGED_IN,
            expires_at=datetime.now() - timedelta(days=1),
            cookies=[{"name": "web_session", "value": "expired", "domain": ".xiaohongshu.com"}],
        )

    def test_init_creates_dir(self, temp_dir: Path):
        assert not temp_dir.exists()
        CredentialStore(base_dir=temp_dir)
        assert temp_dir.exists()

    def test_save_and_load(self, store: CredentialStore, valid_credential: CredentialInfo):
        path = store.save(valid_credential)
        assert path.exists()

        loaded = store.load("xiaohongshu")
        assert loaded is not None
        assert loaded.platform == "xiaohongshu"
        assert loaded.login_type == LoginType.QRCODE
        assert loaded.status == LoginStatus.LOGGED_IN
        assert len(loaded.cookies) == 1
        assert loaded.cookies[0]["name"] == "web_session"

    def test_load_nonexistent(self, store: CredentialStore):
        result = store.load("nonexistent")
        assert result is None

    def test_load_valid(self, store: CredentialStore, valid_credential: CredentialInfo):
        store.save(valid_credential)
        loaded = store.load_valid("xiaohongshu")
        assert loaded is not None
        assert loaded.is_valid()

    def test_load_valid_expired(self, store: CredentialStore, expired_credential: CredentialInfo):
        store.save(expired_credential)
        loaded = store.load_valid("xiaohongshu")
        assert loaded is None

    def test_delete(self, store: CredentialStore, valid_credential: CredentialInfo):
        store.save(valid_credential)
        assert store.exists("xiaohongshu")

        result = store.delete("xiaohongshu")
        assert result is True
        assert not store.exists("xiaohongshu")

    def test_delete_nonexistent(self, store: CredentialStore):
        result = store.delete("nonexistent")
        assert result is False

    def test_exists(self, store: CredentialStore, valid_credential: CredentialInfo):
        assert not store.exists("xiaohongshu")
        store.save(valid_credential)
        assert store.exists("xiaohongshu")

    def test_is_valid(self, store: CredentialStore, valid_credential: CredentialInfo, expired_credential: CredentialInfo):
        assert not store.is_valid("xiaohongshu")

        store.save(valid_credential)
        assert store.is_valid("xiaohongshu")

        store.save(expired_credential)
        assert not store.is_valid("xiaohongshu")

    def test_list_platforms(self, store: CredentialStore):
        assert store.list_platforms() == []

        cred1 = CredentialInfo(platform="xiaohongshu", login_type=LoginType.QRCODE)
        cred2 = CredentialInfo(platform="douyin", login_type=LoginType.PHONE)
        store.save(cred1)
        store.save(cred2)

        platforms = store.list_platforms()
        assert "xiaohongshu" in platforms
        assert "douyin" in platforms
        assert len(platforms) == 2

    def test_update_cookies(self, store: CredentialStore, valid_credential: CredentialInfo):
        store.save(valid_credential)

        new_cookies = [
            {"name": "web_session", "value": "new_value", "domain": ".xiaohongshu.com"},
            {"name": "a1", "value": "a1_value", "domain": ".xiaohongshu.com"},
        ]
        updated = store.update_cookies("xiaohongshu", new_cookies)

        assert len(updated.cookies) == 2
        assert updated.cookies[0]["value"] == "new_value"
        assert updated.updated_at > valid_credential.updated_at

        reloaded = store.load("xiaohongshu")
        assert reloaded is not None
        assert len(reloaded.cookies) == 2

    def test_update_cookies_nonexistent(self, store: CredentialStore):
        with pytest.raises(InvalidCredentialError):
            store.update_cookies("nonexistent", [])

    def test_multiple_platforms(self, store: CredentialStore):
        cred1 = CredentialInfo(
            platform="xiaohongshu",
            login_type=LoginType.QRCODE,
            status=LoginStatus.LOGGED_IN,
            cookies=[{"name": "xhs_cookie", "value": "x"}],
        )
        cred2 = CredentialInfo(
            platform="douyin",
            login_type=LoginType.PHONE,
            status=LoginStatus.LOGGED_IN,
            cookies=[{"name": "dy_cookie", "value": "y"}],
        )

        store.save(cred1)
        store.save(cred2)

        xhs = store.load("xiaohongshu")
        dy = store.load("douyin")

        assert xhs is not None
        assert dy is not None
        assert xhs.platform == "xiaohongshu"
        assert dy.platform == "douyin"
        assert xhs.cookies[0]["name"] == "xhs_cookie"
        assert dy.cookies[0]["name"] == "dy_cookie"

    def test_save_overwrites(self, store: CredentialStore, valid_credential: CredentialInfo):
        store.save(valid_credential)

        updated_cred = valid_credential.model_copy(
            update={"login_type": LoginType.PHONE}
        )
        store.save(updated_cred)

        loaded = store.load("xiaohongshu")
        assert loaded is not None
        assert loaded.login_type == LoginType.PHONE
