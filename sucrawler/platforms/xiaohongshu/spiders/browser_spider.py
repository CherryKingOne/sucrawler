from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from sucrawler.auth.types import LoginType
from sucrawler.browser.manager.browser_manager import BrowserManager
from sucrawler.browser.network.request_capture import RequestCapture
from sucrawler.platforms.xiaohongshu.auth.xhs_login import XHSAuthenticator
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.extractor import XHSExtractor
from sucrawler.platforms.xiaohongshu.models.note import XHSNoteItem
from sucrawler.platforms.xiaohongshu.models.user import XHSUserItem


class XHSBrowserSpider:
    def __init__(self, config: XHSConfig) -> None:
        self.config = config
        self.extractor = XHSExtractor()
        self._browser: BrowserManager | None = None
        self._authenticator: XHSAuthenticator | None = None
        self._login_checked: bool = False

    async def _ensure_browser(self) -> BrowserManager:
        if self._browser is None:
            browser_config = self.config.browser.model_copy(
                update={"enabled": True, "mode": "cdp"},
            )
            self._browser = BrowserManager(browser_config)
            await self._browser.start()

            self._authenticator = XHSAuthenticator(
                login_type=LoginType.QRCODE,
                timeout=300,
                cookie_str=self.config.cookie or "",
                credential_store=self._browser.credential_store,
            )
            self._browser.set_authenticator(self._authenticator)

            logger.info("XHS browser spider started")
        return self._browser

    async def _ensure_logged_in(self) -> bool:
        if self._login_checked:
            return True

        bm = await self._ensure_browser()
        if not self._authenticator:
            logger.warning("No authenticator available")
            return False

        page = await bm.new_page()
        try:
            self._authenticator.attach_browser(page, bm.playwright_context)

            await page.goto(self.config.base_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            if await self._authenticator.check_login_status():
                logger.info("Already logged in")
                self._login_checked = True
                return True

            logger.info("Not logged in, starting login flow...")
            print("=" * 50)
            print("需要登录小红书账号")
            print("请使用小红书 App 扫描终端中的二维码登录")
            print("=" * 50)

            success = await self._authenticator.login()
            if success:
                await asyncio.sleep(3)
                logger.info("Login successful, verifying on target page...")

                verify_page = await bm.new_page()
                try:
                    self._authenticator.attach_browser(verify_page, bm.playwright_context)
                    await verify_page.goto(self.config.base_url, wait_until="domcontentloaded")
                    await asyncio.sleep(2)

                    if await self._authenticator.check_login_status():
                        logger.info("Login verified on new page")
                        self._login_checked = True
                        if self._authenticator.credential and bm.credential_store:
                            bm.credential_store.save(self._authenticator.credential)
                            logger.info("Credential saved")
                        return True
                    else:
                        logger.warning("Login not verified on new page, retrying...")
                        await asyncio.sleep(3)
                        if await self._authenticator.check_login_status():
                            logger.info("Login verified after retry")
                            self._login_checked = True
                            if self._authenticator.credential and bm.credential_store:
                                bm.credential_store.save(self._authenticator.credential)
                                logger.info("Credential saved")
                            return True
                finally:
                    await verify_page.close()

                return True
            else:
                logger.error("Login failed")
                return False
        finally:
            await page.close()

    async def _fetch_api_via_page(
        self,
        page: Any,
        api_url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            url = api_url
            if params:
                from urllib.parse import urlencode

                url = f"{api_url}?{urlencode(params)}"

            js_code = f"""
            async () => {{
                try {{
                    const response = await fetch('{url}', {{
                        method: 'GET',
                        credentials: 'include',
                        headers: {{
                            'Accept': 'application/json',
                        }}
                    }});
                    const text = await response.text();
                    return {{
                        status: response.status,
                        ok: response.ok,
                        body: text
                    }};
                }} catch (e) {{
                    return {{ error: e.message }};
                }}
            }}
            """
            result = await page.evaluate(js_code)

            if result and result.get("ok") and result.get("body"):
                try:
                    data = json.loads(result["body"])
                    if isinstance(data, dict) and data.get("success"):
                        return data
                except (json.JSONDecodeError, TypeError):
                    pass

            return None
        except Exception as e:
            logger.debug(f"Error fetching API via page: {e}")
            return None

    async def crawl_user_info(self, user_id: str) -> XHSUserItem | None:
        logger.info(f"Crawling user info (browser mode): {user_id}")
        try:
            if not await self._ensure_logged_in():
                logger.error("Failed to login, cannot crawl user info")
                return None

            bm = await self._ensure_browser()
            page = await bm.new_page()

            user_profile_url = f"{self.config.base_url}/user/profile/{user_id}"
            logger.info(f"Navigating to: {user_profile_url}")

            await page.goto(user_profile_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            api_url = f"{self.config.api_url}/user/profile"
            result = await self._fetch_api_via_page(page, api_url, {"user_id": user_id})

            if result is None:
                logger.warning("Failed to get user info via browser fetch, trying capture method")
                result = await self._capture_user_info_via_navigation(page, user_id)

            await page.close()

            if result is None:
                logger.warning("Failed to get user info")
                return None

            user_data = result.get("data", {})
            users = self.extractor.extract_users({"data": [user_data]})
            return users[0] if users else None

        except Exception as e:
            logger.error(f"Error crawling user info (browser mode): {e}")
            return None

    async def _capture_user_info_via_navigation(
        self,
        page: Any,
        user_id: str,
    ) -> dict[str, Any] | None:
        try:
            user_profile_url = f"{self.config.base_url}/user/profile/{user_id}"
            async with RequestCapture(page, url_pattern="user/profile") as capture:
                await page.goto(user_profile_url, wait_until="networkidle")
                await asyncio.sleep(3)

                for captured in capture.captured_responses:
                    if "user/profile" in captured["url"] and captured["status"] == 200:
                        try:
                            body = captured.get("body")
                            if body and isinstance(body, str):
                                data = json.loads(body)
                                if data.get("success"):
                                    return data
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.debug(f"Capture method failed: {e}")

        return None

    async def crawl_user_notes(
        self,
        user_id: str,
        max_count: int = 100,
    ) -> list[XHSNoteItem]:
        logger.info(f"Crawling user notes (browser mode): {user_id}, max_count: {max_count}")
        all_notes: list[XHSNoteItem] = []

        try:
            if not await self._ensure_logged_in():
                logger.error("Failed to login, cannot crawl user notes")
                return all_notes

            bm = await self._ensure_browser()
            page = await bm.new_page()

            user_profile_url = f"{self.config.base_url}/user/profile/{user_id}"
            await page.goto(user_profile_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            api_url = f"{self.config.api_url}/user/profile/notes"
            params = {"user_id": user_id, "cursor": "", "page_size": 20}
            result = await self._fetch_api_via_page(page, api_url, params)

            if result is None:
                logger.warning("Failed to get notes via page fetch, trying scroll capture")
                notes_data = await self._capture_notes_via_scroll(page, user_id)
            else:
                notes_data = self._extract_notes_from_result(result)
                cursor = self._get_next_cursor(result)

                while len(notes_data) < max_count and cursor:
                    params["cursor"] = cursor
                    result = await self._fetch_api_via_page(page, api_url, params)
                    if result is None:
                        break
                    page_notes = self._extract_notes_from_result(result)
                    notes_data.extend(page_notes)
                    cursor = self._get_next_cursor(result)
                    if not page_notes:
                        break

            await page.close()

            unique_notes: dict[str, dict[str, Any]] = {}
            for note in notes_data:
                note_id = note.get("note_id") or note.get("id")
                if note_id and note_id not in unique_notes:
                    unique_notes[note_id] = note

            extracted = self.extractor.extract_notes(
                {"notes": list(unique_notes.values())},
            )
            all_notes.extend(extracted)
            logger.info(f"Got {len(all_notes)} notes via browser mode")

        except Exception as e:
            logger.error(f"Error crawling user notes (browser mode): {e}")

        return all_notes[:max_count]

    def _extract_notes_from_result(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        inner = result.get("data", {})
        if isinstance(inner, dict):
            notes = inner.get("notes", [])
            return notes if isinstance(notes, list) else []
        return []

    def _get_next_cursor(self, result: dict[str, Any]) -> str:
        inner = result.get("data", {})
        if isinstance(inner, dict):
            return str(inner.get("cursor", ""))
        return ""

    async def _capture_notes_via_scroll(
        self,
        page: Any,
        user_id: str,
    ) -> list[dict[str, Any]]:
        notes_data: list[dict[str, Any]] = []
        try:
            user_profile_url = f"{self.config.base_url}/user/profile/{user_id}"
            async with RequestCapture(page, url_pattern="user/profile/notes") as capture:
                await page.goto(user_profile_url, wait_until="networkidle")

                for _ in range(5):
                    try:
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)
                    except Exception:
                        break

                for captured in capture.captured_responses:
                    if "user/profile/notes" in captured["url"] and captured["status"] == 200:
                        try:
                            body = captured.get("body")
                            if body and isinstance(body, str):
                                data = json.loads(body)
                                if data.get("success"):
                                    inner = data.get("data", {})
                                    if isinstance(inner, dict):
                                        page_notes = inner.get("notes", [])
                                        if isinstance(page_notes, list):
                                            notes_data.extend(page_notes)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.debug(f"Scroll capture method failed: {e}")

        return notes_data

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.stop()
            self._browser = None
            logger.info("XHS browser spider closed")

    async def __aenter__(self) -> XHSBrowserSpider:
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
