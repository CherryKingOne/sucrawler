from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from sucrawler.browser.manager.browser_manager import BrowserManager
from sucrawler.browser.network.request_capture import RequestCapture
from sucrawler.platforms.bilibili.config import BiliConfig
from sucrawler.platforms.bilibili.extractor import BiliExtractor
from sucrawler.platforms.bilibili.models.user import BiliUserItem
from sucrawler.platforms.bilibili.models.video import BiliVideoItem


class BiliBrowserSpider:
    def __init__(self, config: BiliConfig) -> None:
        self.config = config
        self.extractor = BiliExtractor()
        self._browser: BrowserManager | None = None
        self._login_checked: bool = False

    async def _ensure_browser(self) -> BrowserManager:
        if self._browser is None:
            browser_config = self.config.browser.model_copy(
                update={"enabled": True, "mode": "cdp"},
            )
            self._browser = BrowserManager(browser_config)
            await self._browser.start()
            logger.info("Bilibili browser spider started")
        return self._browser

    async def _ensure_logged_in(self) -> bool:
        if self._login_checked:
            return True

        bm = await self._ensure_browser()
        page = await bm.new_page()
        try:
            await page.goto(f"{self.config.base_url}", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            cookies = await page.context.cookies()
            sessdata = None
            for cookie in cookies:
                if cookie.get("name") == "SESSDATA":
                    sessdata = cookie.get("value")
                    break

            if sessdata:
                logger.info("Already logged in (SESSDATA found)")
                self._login_checked = True
                return True

            logger.info("Not logged in, please login manually in the browser")
            print("=" * 50)
            print("需要登录 Bilibili 账号")
            print("请在打开的浏览器窗口中完成登录")
            print("登录完成后，程序将自动继续爬取")
            print("=" * 50)

            login_url = "https://passport.bilibili.com/login"
            await page.goto(login_url, wait_until="domcontentloaded")

            max_wait = 300
            check_interval = 3
            waited = 0

            while waited < max_wait:
                await asyncio.sleep(check_interval)
                waited += check_interval

                cookies = await page.context.cookies()
                for cookie in cookies:
                    if cookie.get("name") == "SESSDATA":
                        logger.info("Login detected!")
                        self._login_checked = True
                        await asyncio.sleep(2)
                        return True

                try:
                    current_url = page.url
                    if "passport.bilibili.com" not in current_url:
                        cookies = await page.context.cookies()
                        for cookie in cookies:
                            if cookie.get("name") == "SESSDATA":
                                logger.info("Login successful (redirected away from login page)")
                                self._login_checked = True
                                return True
                except Exception:
                    pass

            logger.warning("Login timeout")
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
                            'Referer': '{self.config.space_url}/',
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
                    if isinstance(data, dict) and data.get("code") == 0:
                        return data
                except (json.JSONDecodeError, TypeError):
                    pass

            return None
        except Exception as e:
            logger.debug(f"Error fetching API via page: {e}")
            return None

    async def crawl_user_info(self, mid: str) -> BiliUserItem | None:
        logger.info(f"Crawling user info (browser mode): {mid}")
        try:
            if not await self._ensure_logged_in():
                logger.warning("Not logged in, crawling without authentication")

            bm = await self._ensure_browser()
            page = await bm.new_page()

            space_url = f"{self.config.space_url}/{mid}"
            logger.info(f"Navigating to: {space_url}")

            await page.goto(space_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            api_url = f"{self.config.api_url}/x/space/wbi/acc/info"
            result = await self._fetch_api_via_page(page, api_url, {"mid": mid})

            if result is None:
                logger.warning("Failed to get user info via fetch, trying capture method")
                result = await self._capture_user_info_via_navigation(page, mid)

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
        mid: str,
    ) -> dict[str, Any] | None:
        try:
            space_url = f"{self.config.space_url}/{mid}"
            async with RequestCapture(page, url_pattern="acc/info") as capture:
                await page.goto(space_url, wait_until="networkidle")
                await asyncio.sleep(3)

                for captured in capture.captured_responses:
                    if "acc/info" in captured["url"] and captured["status"] == 200:
                        try:
                            body = captured.get("body")
                            if body and isinstance(body, str):
                                data = json.loads(body)
                                if data.get("code") == 0:
                                    return data
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.debug(f"Capture method failed: {e}")

        return None

    async def crawl_user_videos(
        self,
        mid: str,
        max_count: int = 0,
    ) -> list[BiliVideoItem]:
        fetch_all = max_count <= 0
        log_msg = f"Crawling user videos (browser mode): {mid}"
        log_msg += ", fetch all" if fetch_all else f", max_count: {max_count}"
        logger.info(log_msg)
        all_videos: list[BiliVideoItem] = []

        try:
            if not await self._ensure_logged_in():
                logger.warning("Not logged in, crawling without authentication")

            bm = await self._ensure_browser()
            page = await bm.new_page()

            videos_data = await self._capture_videos_via_scroll(
                page, mid, max_count
            )

            await page.close()

            unique_videos: dict[str, dict[str, Any]] = {}
            for video in videos_data:
                bvid = video.get("bvid")
                if bvid and bvid not in unique_videos:
                    unique_videos[bvid] = video

            extracted = self.extractor.extract_videos(
                {"vlist": list(unique_videos.values())},
            )
            all_videos.extend(extracted)
            logger.info(f"Got {len(all_videos)} videos via browser mode")

        except Exception as e:
            logger.error(f"Error crawling user videos (browser mode): {e}")

        if max_count > 0:
            return all_videos[:max_count]
        return all_videos

    async def _capture_videos_via_scroll(
        self,
        page: Any,
        mid: str,
        max_count: int = 0,
    ) -> list[dict[str, Any]]:
        fetch_all = max_count <= 0
        videos_data: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        last_scroll_height = 0
        try:
            video_url = f"{self.config.space_url}/{mid}/video"
            async with RequestCapture(page, url_pattern="arc/search") as capture:
                await page.goto(video_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

                max_scrolls = 200 if fetch_all else max(20, (max_count // 30) + 10)
                consecutive_no_new = 0
                max_consecutive_no_new = 8
                scroll_pause_time = 2

                for scroll_idx in range(max_scrolls):
                    try:
                        current_scroll_height = await page.evaluate("document.body.scrollHeight")
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    except Exception:
                        break

                    await asyncio.sleep(scroll_pause_time)

                    new_this_scroll = 0
                    for captured in capture.captured_responses:
                        if "arc/search" in captured["url"] and captured["status"] == 200:
                            try:
                                body = captured.get("body")
                                if body and isinstance(body, str):
                                    data = json.loads(body)
                                    if data.get("code") == 0:
                                        inner = data.get("data", {})
                                        if isinstance(inner, dict):
                                            vlist = inner.get("list", {}).get("vlist", [])
                                            if isinstance(vlist, list):
                                                for video in vlist:
                                                    bvid = video.get("bvid")
                                                    if bvid and bvid not in seen_ids:
                                                        seen_ids.add(bvid)
                                                        videos_data.append(video)
                                                        new_this_scroll += 1
                            except (json.JSONDecodeError, KeyError):
                                continue

                    logger.info(
                        f"Scroll {scroll_idx + 1}/{max_scrolls}: "
                        f"{new_this_scroll} new videos (total: {len(videos_data)})"
                    )

                    if not fetch_all and len(videos_data) >= max_count:
                        logger.info(f"Reached max_count: {max_count}")
                        break

                    if new_this_scroll == 0:
                        consecutive_no_new += 1
                        if consecutive_no_new >= max_consecutive_no_new:
                            logger.info(
                                f"No new videos for {consecutive_no_new} scrolls, reached end"
                            )
                            break
                    else:
                        consecutive_no_new = 0

                    try:
                        new_scroll_height = await page.evaluate("document.body.scrollHeight")
                        if new_scroll_height == last_scroll_height and new_this_scroll == 0:
                            consecutive_no_new += 2
                            if consecutive_no_new >= max_consecutive_no_new:
                                logger.info("Page height stopped changing, reached end")
                                break
                        last_scroll_height = new_scroll_height
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Scroll capture method failed: {e}")

        return videos_data

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.stop()
            self._browser = None
            logger.info("Bilibili browser spider closed")

    async def __aenter__(self) -> BiliBrowserSpider:
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
