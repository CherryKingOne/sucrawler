from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from .exceptions import (
    InvalidCredentialError,
    LoginFailedError,
    LoginTimeoutError,
)
from .types import CredentialInfo, LoginStatus, LoginType


class BaseAuthenticator(ABC):
    """认证器抽象基类。

    各平台需继承此类并实现具体的登录逻辑。
    """

    def __init__(
        self,
        login_type: LoginType = LoginType.QRCODE,
        timeout: int = 300,
    ) -> None:
        """初始化认证器。

        Args:
            login_type: 登录方式
            timeout: 登录超时时间（秒）
        """
        self.login_type = login_type
        self.timeout = timeout
        self._status: LoginStatus = LoginStatus.LOGGED_OUT
        self._credential: CredentialInfo | None = None

    @property
    def status(self) -> LoginStatus:
        """当前登录状态。"""
        return self._status

    @property
    def credential(self) -> CredentialInfo | None:
        """当前凭证信息。"""
        return self._credential

    async def login(self) -> bool:
        """执行登录流程。

        Returns:
            是否登录成功

        Raises:
            LoginTimeoutError: 登录超时
            LoginFailedError: 登录失败
        """
        if self._status == LoginStatus.LOGGED_IN:
            logger.debug(f"[{self.platform_name}] Already logged in")
            return True

        if not isinstance(self.login_type, LoginType):
            raise LoginFailedError(f"Unsupported login type: {self.login_type}")

        self._status = LoginStatus.LOGGING_IN
        logger.info(f"[{self.platform_name}] Starting login (type: {self.login_type.value})")

        try:
            if self.login_type == LoginType.QRCODE:
                success = await self._login_by_qrcode()
            elif self.login_type == LoginType.PHONE:
                success = await self._login_by_phone()
            elif self.login_type == LoginType.COOKIE:
                success = await self._login_by_cookie()
            else:
                raise LoginFailedError(f"Unsupported login type: {self.login_type}")

            if success:
                self._status = LoginStatus.LOGGED_IN
                self._credential = await self._build_credential()
                logger.info(f"[{self.platform_name}] Login successful")
                return True

            self._status = LoginStatus.LOGGED_OUT
            raise LoginFailedError(f"[{self.platform_name}] Login failed")

        except LoginTimeoutError:
            self._status = LoginStatus.LOGGED_OUT
            raise
        except LoginFailedError:
            self._status = LoginStatus.LOGGED_OUT
            raise
        except Exception as e:
            self._status = LoginStatus.LOGGED_OUT
            logger.error(f"[{self.platform_name}] Login error: {e}")
            raise LoginFailedError(str(e)) from e

    async def check_login_status(self) -> bool:
        """检查当前是否已登录。

        Returns:
            是否已登录
        """
        try:
            is_logged_in = await self._do_check_login_status()
            if is_logged_in:
                if self._status != LoginStatus.LOGGED_IN:
                    self._status = LoginStatus.LOGGED_IN
                    logger.info(f"[{self.platform_name}] Login status: logged in")
            else:
                if self._status == LoginStatus.LOGGED_IN:
                    self._status = LoginStatus.EXPIRED
                    logger.warning(f"[{self.platform_name}] Login status: expired")
                else:
                    self._status = LoginStatus.LOGGED_OUT

            return is_logged_in
        except Exception as e:
            logger.error(f"[{self.platform_name}] Check login status error: {e}")
            return False

    async def ensure_logged_in(self) -> bool:
        """确保已登录，未登录则触发登录。

        Returns:
            是否已登录
        """
        if await self.check_login_status():
            return True

        logger.info(f"[{self.platform_name}] Not logged in, starting login...")
        return await self.login()

    async def logout(self) -> None:
        """登出。"""
        try:
            await self._do_logout()
        except Exception as e:
            logger.warning(f"[{self.platform_name}] Logout error: {e}")

        self._status = LoginStatus.LOGGED_OUT
        self._credential = None
        logger.info(f"[{self.platform_name}] Logged out")

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称。"""

    @abstractmethod
    async def _login_by_qrcode(self) -> bool:
        """扫码登录。

        Returns:
            是否登录成功
        """

    @abstractmethod
    async def _login_by_phone(self) -> bool:
        """手机号登录。

        Returns:
            是否登录成功
        """

    @abstractmethod
    async def _login_by_cookie(self) -> bool:
        """Cookie 登录。

        Returns:
            是否登录成功
        """

    @abstractmethod
    async def _do_check_login_status(self) -> bool:
        """实际检查登录状态的实现。

        Returns:
            是否已登录
        """

    async def _do_logout(self) -> None:
        """实际登出操作的实现。

        默认不做任何操作，子类可覆盖。
        """

    async def _build_credential(self) -> CredentialInfo:
        """构建凭证信息。

        Returns:
            凭证信息
        """
        cookies: list[dict[str, Any]] = []
        try:
            cookies = await self._get_cookies()
        except Exception as e:
            logger.warning(f"[{self.platform_name}] Get cookies failed: {e}")

        return CredentialInfo(
            platform=self.platform_name,
            login_type=self.login_type,
            status=LoginStatus.LOGGED_IN,
            cookies=cookies,
        )

    async def _get_cookies(self) -> list[dict[str, Any]]:
        """获取当前浏览器的 Cookie。

        默认返回空列表，有浏览器上下文的子类应覆盖此方法。

        Returns:
            Cookie 列表
        """
        return []

    async def load_credential(self, credential: CredentialInfo) -> bool:
        """加载凭证。

        Args:
            credential: 凭证信息

        Returns:
            是否加载成功
        """
        if not credential.is_valid():
            raise InvalidCredentialError("Credential is invalid or expired")

        try:
            success = await self._do_load_credential(credential)
            if success:
                self._credential = credential
                self._status = LoginStatus.LOGGED_IN
                logger.info(f"[{self.platform_name}] Credential loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"[{self.platform_name}] Load credential failed: {e}")
            return False

    async def _do_load_credential(self, credential: CredentialInfo) -> bool:
        """实际加载凭证的实现。

        默认返回 False，子类应覆盖此方法。

        Args:
            credential: 凭证信息

        Returns:
            是否加载成功
        """
        return False
