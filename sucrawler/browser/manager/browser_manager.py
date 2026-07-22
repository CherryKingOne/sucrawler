from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Any, Optional

from loguru import logger

from sucrawler.auth.base import BaseAuthenticator
from sucrawler.auth.credential_store import CredentialStore
from sucrawler.browser.cdp.connection import CDPConnection
from sucrawler.browser.cdp.target import TargetManager
from sucrawler.browser.cookie import CookieManager
from sucrawler.browser.exceptions import (
    BrowserConnectionError,
    BrowserLaunchError,
    BrowserTimeoutError,
)
from sucrawler.browser.launcher import ChromeLauncher, PathDetector
from sucrawler.browser.types import BrowserConfig, BrowserInfo, LaunchOptions


class BrowserManager:
    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._launcher: Optional[ChromeLauncher] = None
        self._cdp: Optional[CDPConnection] = None
        self._targets: Optional[TargetManager] = None
        self._cookies: Optional[CookieManager] = None
        self._playwright_browser: Optional[Any] = None
        self._playwright_context: Optional[Any] = None
        self._playwright_instance: Optional[Any] = None
        self._debug_port: int = 0
        self._browser_info: Optional[BrowserInfo] = None
        self._started: bool = False
        self._cleanup_registered: bool = False
        self._authenticator: Optional[BaseAuthenticator] = None
        self._credential_store: Optional[CredentialStore] = None

    @property
    def config(self) -> BrowserConfig:
        return self._config

    @property
    def debug_port(self) -> int:
        return self._debug_port

    @property
    def cdp(self) -> Optional[CDPConnection]:
        return self._cdp

    @property
    def targets(self) -> Optional[TargetManager]:
        return self._targets

    @property
    def cookies(self) -> Optional[CookieManager]:
        return self._cookies

    @property
    def playwright_browser(self) -> Optional[Any]:
        return self._playwright_browser

    @property
    def playwright_context(self) -> Optional[Any]:
        return self._playwright_context

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def authenticator(self) -> Optional[BaseAuthenticator]:
        return self._authenticator

    @property
    def credential_store(self) -> Optional[CredentialStore]:
        return self._credential_store

    def set_authenticator(self, authenticator: BaseAuthenticator) -> None:
        self._authenticator = authenticator
        if self._playwright_context and self._authenticator:
            self._authenticator.attach_browser(
                page=None,
                context=self._playwright_context,
            )
        logger.info("[BrowserManager] Authenticator set")

    async def ensure_logged_in(self, platform: str = "") -> bool:
        if not self._authenticator:
            logger.warning("[BrowserManager] No authenticator set")
            return False

        if self._playwright_context:
            page = await self.new_page()
            try:
                self._authenticator.attach_browser(page, self._playwright_context)
                result = await self._authenticator.ensure_logged_in()
                if result and self._config.save_credentials:
                    await self._save_current_credential()
                return result
            finally:
                await page.close()

        return await self._authenticator.ensure_logged_in()

    async def _save_current_credential(self) -> None:
        if not self._authenticator or not self._credential_store:
            return
        if self._authenticator.credential:
            self._credential_store.save(self._authenticator.credential)
            logger.info("[BrowserManager] Credential saved")

    async def start(self) -> None:
        if self._started:
            logger.warning("[BrowserManager] Browser already started")
            return

        logger.info("[BrowserManager] Starting browser...")

        try:
            if self._config.cdp_connect_existing:
                await self._connect_existing()
            else:
                await self._launch_and_connect()

            await self._init_playwright()
            await self._init_cookie_manager()
            self._init_credential_store()
            self._register_cleanup()
            self._started = True
            logger.info("[BrowserManager] Browser started successfully")
        except Exception as e:
            logger.error(f"[BrowserManager] Failed to start browser: {e}")
            await self.stop()
            raise

    async def stop(self, force: bool = False) -> None:
        if not self._started and not force:
            return

        logger.info("[BrowserManager] Stopping browser...")

        try:
            await self._cleanup_playwright()
            self._cleanup_launcher(force)
        except Exception as e:
            logger.error(f"[BrowserManager] Error during stop: {e}")
        finally:
            self._started = False
            logger.info("[BrowserManager] Browser stopped")

    async def new_page(self, url: str = "about:blank") -> Any:
        if not self._playwright_context:
            raise BrowserConnectionError("Browser context not initialized")
        page = await self._playwright_context.new_page()
        logger.debug(f"[BrowserManager] Created new page: {page.url}")
        if url and url != "about:blank":
            await page.goto(url)
        return page

    async def get_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "started": self._started,
            "debug_port": self._debug_port,
            "mode": self._config.mode,
            "connect_existing": self._config.cdp_connect_existing,
        }

        if self._browser_info:
            info["browser"] = {
                "name": self._browser_info.name,
                "version": self._browser_info.version,
                "type": self._browser_info.type,
            }

        if self._playwright_browser:
            try:
                info["contexts_count"] = len(self._playwright_browser.contexts)
                info["is_connected"] = self._playwright_browser.is_connected()
            except Exception:
                pass

        return info

    async def _launch_and_connect(self) -> None:
        browser_path = self._resolve_browser_path()

        launcher = ChromeLauncher()
        self._launcher = launcher

        port = self._config.debug_port
        if not self._config.cdp_connect_existing and self._is_port_in_use(port):
            port = launcher.find_available_port(port)
        self._debug_port = port

        user_data_dir = self._resolve_user_data_dir()

        options = LaunchOptions(
            browser_path=browser_path,
            debug_port=self._debug_port,
            headless=self._config.headless,
            user_data_dir=user_data_dir,
            user_agent=self._config.user_agent if self._config.user_agent else None,
            proxy=self._config.proxy if self._config.proxy else None,
        )

        launcher.launch(options)

        self._cdp = CDPConnection(debug_port=self._debug_port)

        ready = await self._cdp.wait_until_ready(timeout=self._config.launch_timeout)
        if not ready:
            raise BrowserTimeoutError(
                f"Browser not ready within {self._config.launch_timeout}s"
            )

        self._targets = TargetManager(self._cdp)

    async def _connect_existing(self) -> None:
        self._debug_port = self._config.debug_port
        self._cdp = CDPConnection(debug_port=self._debug_port)

        ready = await self._cdp.wait_until_ready(timeout=self._config.launch_timeout)
        if not ready:
            raise BrowserConnectionError(
                f"Cannot connect to existing browser on port {self._debug_port}"
            )

        self._targets = TargetManager(self._cdp)
        logger.info("[BrowserManager] Connected to existing browser")

    async def _init_playwright(self) -> None:
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise BrowserLaunchError(
                "Playwright not installed. Install with: uv pip install playwright"
            ) from e

        self._playwright_instance = await async_playwright().start()

        ws_url = await self._cdp.get_websocket_url(
            connect_existing=self._config.cdp_connect_existing
        )

        logger.info(f"[BrowserManager] Connecting Playwright via CDP: {ws_url}")

        try:
            self._playwright_browser = await self._playwright_instance.chromium.connect_over_cdp(
                ws_url,
                timeout=self._config.launch_timeout * 1000,
            )
        except Exception as e:
            if not self._config.cdp_connect_existing:
                raise

            logger.warning(
                f"[BrowserManager] Direct CDP connection failed: {e}, trying discovery..."
            )
            ws_url = await self._cdp.get_websocket_url(connect_existing=False)
            self._playwright_browser = await self._playwright_instance.chromium.connect_over_cdp(
                ws_url,
                timeout=self._config.launch_timeout * 1000,
            )

        contexts = self._playwright_browser.contexts
        if contexts:
            self._playwright_context = contexts[0]
            logger.info("[BrowserManager] Using existing browser context")
        else:
            self._playwright_context = await self._playwright_browser.new_context(
                viewport={
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height,
                },
                accept_downloads=True,
            )
            logger.info("[BrowserManager] Created new browser context")

        if self._config.stealth_script_path and os.path.exists(
            self._config.stealth_script_path
        ):
            try:
                await self._playwright_context.add_init_script(
                    path=self._config.stealth_script_path
                )
                logger.info(
                    f"[BrowserManager] Added stealth script: {self._config.stealth_script_path}"
                )
            except Exception as e:
                logger.warning(f"[BrowserManager] Failed to add stealth script: {e}")

    async def _init_cookie_manager(self) -> None:
        if not self._playwright_context:
            return
        self._cookies = CookieManager(self._playwright_context)
        if self._config.save_login_state:
            state_file = self._get_state_file()
            if os.path.exists(state_file):
                try:
                    await self._cookies.load_from_file(state_file)
                    logger.info("[BrowserManager] Loaded saved login state")
                except Exception as e:
                    logger.warning(f"[BrowserManager] Failed to load state: {e}")

    def _init_credential_store(self) -> None:
        credential_dir = self._config.credential_dir
        if not credential_dir:
            credential_dir = os.path.join(
                os.path.expanduser("~"),
                ".sucrawler",
                "credentials",
            )
        try:
            self._credential_store = CredentialStore(base_dir=credential_dir)
            logger.info(f"[BrowserManager] Credential store initialized at {credential_dir}")
        except Exception as e:
            logger.warning(f"[BrowserManager] Failed to init credential store: {e}")

    async def _cleanup_playwright(self) -> None:
        if self._playwright_context:
            try:
                if self._config.save_login_state and self._cookies:
                    state_file = self._get_state_file()
                    os.makedirs(os.path.dirname(state_file), exist_ok=True)
                    await self._cookies.save_to_file(state_file)
                    logger.info("[BrowserManager] Saved login state")
            except Exception as e:
                logger.warning(f"[BrowserManager] Failed to save state: {e}")

            try:
                await self._playwright_context.close()
                logger.info("[BrowserManager] Browser context closed")
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    logger.warning(f"[BrowserManager] Failed to close context: {e}")
            finally:
                self._playwright_context = None

        if self._playwright_browser:
            try:
                if self._playwright_browser.is_connected():
                    await self._playwright_browser.close()
                    logger.info("[BrowserManager] Playwright disconnected")
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    logger.warning(f"[BrowserManager] Failed to disconnect: {e}")
            finally:
                self._playwright_browser = None

        if self._playwright_instance:
            try:
                await self._playwright_instance.stop()
                logger.info("[BrowserManager] Playwright stopped")
            except Exception as e:
                logger.warning(f"[BrowserManager] Failed to stop playwright: {e}")
            finally:
                self._playwright_instance = None

    def _cleanup_launcher(self, force: bool = False) -> None:
        if self._config.cdp_connect_existing:
            logger.info("[BrowserManager] Connected to existing browser, skip process cleanup")
            return

        if not force and not self._config.auto_close:
            logger.info("[BrowserManager] auto_close=False, keeping browser running")
            return

        if self._launcher:
            try:
                self._launcher.cleanup()
                logger.info("[BrowserManager] Browser process cleaned up")
            except Exception as e:
                logger.warning(f"[BrowserManager] Failed to cleanup launcher: {e}")
            finally:
                self._launcher = None

    def _resolve_browser_path(self) -> str:
        if self._config.custom_browser_path:
            path = self._config.custom_browser_path
            if not os.path.isfile(path):
                raise BrowserLaunchError(f"Custom browser path not found: {path}")
            return path

        detector = PathDetector()
        browser = detector.find_first(browser_type=self._config.browser_type)
        if not browser:
            raise BrowserLaunchError(
                f"No {self._config.browser_type} browser found on this system"
            )
        self._browser_info = browser
        logger.info(f"[BrowserManager] Found browser: {browser.name} - {browser.version}")
        return browser.path

    def _resolve_user_data_dir(self) -> Optional[str]:
        if self._config.user_data_dir:
            os.makedirs(self._config.user_data_dir, exist_ok=True)
            return self._config.user_data_dir

        if self._config.save_login_state:
            default_dir = os.path.join(
                os.path.expanduser("~"),
                ".sucrawler",
                "browser_profiles",
                self._config.browser_type,
            )
            os.makedirs(default_dir, exist_ok=True)
            return default_dir

        return None

    def _get_state_file(self) -> str:
        base_dir = self._config.user_data_dir or os.path.join(
            os.path.expanduser("~"),
            ".sucrawler",
            "browser_profiles",
            self._config.browser_type,
        )
        return os.path.join(base_dir, "browser_state.json")

    def _is_port_in_use(self, port: int) -> bool:
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return False
        except OSError:
            return True

    def _register_cleanup(self) -> None:
        if self._cleanup_registered:
            return

        if sys.platform != "win32":
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop:
                for sig in (signal.SIGINT, signal.SIGTERM):
                    try:
                        loop.add_signal_handler(
                            sig,
                            lambda s=sig: asyncio.create_task(self._signal_handler(s)),
                        )
                    except (NotImplementedError, RuntimeError):
                        pass

        self._cleanup_registered = True

    async def _signal_handler(self, sig: int) -> None:
        logger.info(f"[BrowserManager] Received signal {sig}, cleaning up...")
        await self.stop(force=True)

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()
