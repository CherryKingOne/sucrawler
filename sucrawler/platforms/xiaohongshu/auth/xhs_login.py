from __future__ import annotations

from typing import Any

from loguru import logger

from sucrawler.auth.base import BaseAuthenticator
from sucrawler.auth.credential_store import CredentialStore
from sucrawler.auth.cookie_utils import cookies_list_to_dict, string_to_cookies_list
from sucrawler.auth.qrcode import QRCodeUtils
from sucrawler.auth.types import LoginType


class XHSAuthenticator(BaseAuthenticator):
    """小红书平台认证器。

    实现小红书平台的登录认证逻辑，支持扫码登录、手机号登录和 Cookie 登录。
    """

    LOGIN_URL = "https://www.xiaohongshu.com"
    QRCODE_IMG_SELECTOR = "img.qrcode-img"
    LOGIN_CHECK_SELECTOR = "a.user.side-bar-user"

    def __init__(
        self,
        login_type: LoginType = LoginType.QRCODE,
        timeout: int = 300,
        cookie_str: str = "",
        credential_store: CredentialStore | None = None,
    ) -> None:
        """初始化小红书认证器。

        Args:
            login_type: 登录方式
            timeout: 登录超时时间（秒）
            cookie_str: Cookie 登录时的 Cookie 字符串
            credential_store: 凭证存储实例
        """
        super().__init__(login_type=login_type, timeout=timeout)
        self._cookie_str = cookie_str
        self._credential_store = credential_store or CredentialStore()
        self._page: Any = None
        self._browser_context: Any = None

    @property
    def platform_name(self) -> str:
        return "xiaohongshu"

    def attach_browser(self, page: Any, context: Any | None = None) -> None:
        """绑定浏览器页面和上下文。

        Args:
            page: Playwright Page 对象
            context: Playwright BrowserContext 对象
        """
        self._page = page
        self._browser_context = context

    async def _login_by_qrcode(self) -> bool:
        """扫码登录。

        Returns:
            是否登录成功
        """
        if self._page is None:
            logger.error("No browser page attached for QR code login")
            return False

        try:
            await self._page.goto(self.LOGIN_URL, wait_until="domcontentloaded")

            qrcode_data = await self._extract_qrcode()
            if qrcode_data:
                QRCodeUtils.display_qrcode_terminal(qrcode_data)
                logger.info("Please scan the QR code to login")

            success = await self._wait_for_login()
            if success:
                logger.info("QR code login successful")
                return True

            return False

        except Exception as e:
            logger.error(f"QR code login error: {e}")
            return False

    async def _extract_qrcode(self) -> bytes | None:
        """从页面提取二维码图片。

        Returns:
            二维码图片二进制数据
        """
        if self._page is None:
            return None

        try:
            img_element = await self._page.query_selector(self.QRCODE_IMG_SELECTOR)
            if img_element:
                src = await img_element.get_attribute("src")
                if src:
                    return QRCodeUtils.extract_qrcode_from_img_src(src)
        except Exception as e:
            logger.debug(f"Extract QR code failed: {e}")

        return None

    async def _wait_for_login(self) -> bool:
        """等待登录完成。

        Returns:
            是否登录成功
        """
        import asyncio

        if self._page is None:
            return False

        check_interval = 2
        qrcode_refresh_interval = 60
        max_checks = self.timeout // check_interval
        last_qrcode_time = 0
        checks_since_refresh = 0

        for i in range(max_checks):
            try:
                user_element = await self._page.query_selector(self.LOGIN_CHECK_SELECTOR)
                if user_element:
                    return True

                cookies = await self._get_cookies()
                if self._has_web_session(cookies):
                    return True

                checks_since_refresh += 1
                if checks_since_refresh * check_interval >= qrcode_refresh_interval:
                    checks_since_refresh = 0
                    qrcode_data = await self._extract_qrcode()
                    if qrcode_data:
                        QRCodeUtils.display_qrcode_terminal(qrcode_data)
                        logger.info("QR code refreshed, please scan to login")

            except Exception:
                pass

            await asyncio.sleep(check_interval)

        return False

    def _has_web_session(self, cookies: list[dict[str, Any]]) -> bool:
        """检查 Cookie 中是否有有效的 web_session。

        Args:
            cookies: Cookie 列表

        Returns:
            是否包含有效 web_session
        """
        cookie_dict = cookies_list_to_dict(cookies)
        return "web_session" in cookie_dict and bool(cookie_dict["web_session"])

    async def _login_by_phone(self) -> bool:
        """手机号登录。

        Returns:
            是否登录成功
        """
        if self._page is None:
            logger.error("No browser page attached for phone login")
            return False

        try:
            await self._page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            logger.info("Phone login is not fully implemented, please use QR code or cookie login")
            return False

        except Exception as e:
            logger.error(f"Phone login error: {e}")
            return False

    async def _login_by_cookie(self) -> bool:
        """Cookie 登录。

        Returns:
            是否登录成功
        """
        if not self._cookie_str and self._browser_context is None:
            logger.error("No cookie string provided for cookie login")
            return False

        try:
            if self._cookie_str and self._browser_context:
                cookies = string_to_cookies_list(
                    self._cookie_str,
                    domain=".xiaohongshu.com",
                )
                await self._browser_context.add_cookies(cookies)
                logger.info(f"Added {len(cookies)} cookies from cookie string")

            if self._page:
                await self._page.goto(self.LOGIN_URL, wait_until="domcontentloaded")

                if await self._do_check_login_status():
                    logger.info("Cookie login successful")
                    return True

            return False

        except Exception as e:
            logger.error(f"Cookie login error: {e}")
            return False

    async def _do_check_login_status(self) -> bool:
        """实际检查登录状态。

        Returns:
            是否已登录
        """
        if self._page is None:
            return False

        try:
            user_element = await self._page.query_selector(self.LOGIN_CHECK_SELECTOR)
            if user_element:
                return True

            cookies = await self._get_cookies()
            if self._has_web_session(cookies):
                return True

        except Exception as e:
            logger.debug(f"Check login status error: {e}")

        return False

    async def _get_cookies(self) -> list[dict[str, Any]]:
        """获取当前浏览器的 Cookie。

        Returns:
            Cookie 列表
        """
        if self._browser_context is None:
            return []

        try:
            cookies = await self._browser_context.cookies()
            return list(cookies)
        except Exception as e:
            logger.debug(f"Get cookies error: {e}")
            return []

    async def _do_load_credential(self, credential: Any) -> bool:
        """加载凭证。

        Args:
            credential: 凭证信息

        Returns:
            是否加载成功
        """
        if self._browser_context is None:
            logger.warning("No browser context, cannot load credential cookies")
            return False

        try:
            if credential.cookies:
                await self._browser_context.add_cookies(credential.cookies)
                logger.info(f"Loaded {len(credential.cookies)} cookies from credential")
                return True
        except Exception as e:
            logger.error(f"Load credential error: {e}")

        return False

    async def save_credential(self) -> None:
        """保存当前凭证到存储。"""
        if self._credential:
            self._credential_store.save(self._credential)
            logger.info("Credential saved to store")

    async def load_credential_from_store(self) -> bool:
        """从存储加载凭证。

        Returns:
            是否加载成功
        """
        credential = self._credential_store.load_valid(self.platform_name)
        if credential:
            return await self.load_credential(credential)
        return False
