from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from .exceptions import InvalidCredentialError
from .types import CredentialInfo


class CredentialStore:
    """凭证存储管理器。

    负责登录凭证的持久化存储和加载，支持多平台凭证隔离。
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """初始化凭证存储。

        Args:
            base_dir: 凭证存储根目录，默认为 ~/.sucrawler/credentials
        """
        if base_dir is None:
            base_dir = Path.home() / ".sucrawler" / "credentials"
        self.base_dir = Path(base_dir)
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """确保存储目录存在。"""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_platform_dir(self, platform: str) -> Path:
        """获取平台凭证目录。

        Args:
            platform: 平台名称

        Returns:
            平台目录路径
        """
        platform_dir = self.base_dir / platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        return platform_dir

    def _get_credential_path(self, platform: str) -> Path:
        """获取凭证文件路径。

        Args:
            platform: 平台名称

        Returns:
            凭证文件路径
        """
        return self._get_platform_dir(platform) / "credential.json"

    def save(self, credential: CredentialInfo) -> Path:
        """保存凭证。

        Args:
            credential: 凭证信息

        Returns:
            保存的文件路径
        """
        path = self._get_credential_path(credential.platform)

        data = credential.model_dump(mode="json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Credential saved for platform '{credential.platform}' to {path}")
        return path

    def load(self, platform: str) -> CredentialInfo | None:
        """加载凭证。

        Args:
            platform: 平台名称

        Returns:
            凭证信息，不存在则返回 None
        """
        path = self._get_credential_path(platform)

        if not path.exists():
            logger.debug(f"No credential found for platform '{platform}'")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            credential = CredentialInfo.model_validate(data)
            logger.info(f"Credential loaded for platform '{platform}'")
            return credential
        except Exception as e:
            logger.error(f"Failed to load credential for platform '{platform}': {e}")
            return None

    def load_valid(self, platform: str) -> CredentialInfo | None:
        """加载有效的凭证。

        Args:
            platform: 平台名称

        Returns:
            有效凭证，不存在或已过期则返回 None
        """
        credential = self.load(platform)
        if credential and credential.is_valid():
            return credential
        if credential:
            logger.warning(f"Credential for platform '{platform}' is invalid or expired")
        return None

    def delete(self, platform: str) -> bool:
        """删除凭证。

        Args:
            platform: 平台名称

        Returns:
            是否删除成功
        """
        path = self._get_credential_path(platform)

        if path.exists():
            path.unlink()
            logger.info(f"Credential deleted for platform '{platform}'")
            return True

        logger.debug(f"No credential to delete for platform '{platform}'")
        return False

    def exists(self, platform: str) -> bool:
        """检查凭证是否存在。

        Args:
            platform: 平台名称

        Returns:
            凭证是否存在
        """
        return self._get_credential_path(platform).exists()

    def is_valid(self, platform: str) -> bool:
        """检查凭证是否有效。

        Args:
            platform: 平台名称

        Returns:
            凭证是否有效
        """
        credential = self.load(platform)
        return credential is not None and credential.is_valid()

    def list_platforms(self) -> list[str]:
        """列出所有有凭证的平台。

        Returns:
            平台名称列表
        """
        platforms: list[str] = []
        if not self.base_dir.exists():
            return platforms

        for item in self.base_dir.iterdir():
            if item.is_dir() and (item / "credential.json").exists():
                platforms.append(item.name)

        return sorted(platforms)

    def update_cookies(self, platform: str, cookies: list[dict[str, Any]]) -> CredentialInfo:
        """更新平台凭证的 Cookies。

        Args:
            platform: 平台名称
            cookies: 新的 Cookie 列表

        Returns:
            更新后的凭证信息

        Raises:
            InvalidCredentialError: 平台没有现有凭证
        """
        credential = self.load(platform)
        if credential is None:
            raise InvalidCredentialError(f"No credential found for platform '{platform}'")

        from datetime import datetime

        credential = credential.model_copy(
            update={
                "cookies": cookies,
                "updated_at": datetime.now(),
            }
        )
        self.save(credential)
        return credential
