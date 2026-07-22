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

    async def crawl_video_detail(self, bvid: str) -> dict[str, Any] | None:
        """访问单个视频页面，解析详情页 HTML 获取标签、统计、下载链接等。"""
        video_url = f"{self.config.base_url}/video/{bvid}"
        logger.info(f"Fetching video detail page: {video_url}")
        try:
            bm = await self._ensure_browser()
            page = await bm.new_page()
            await page.goto(video_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            html = await page.content()
            await page.close()

            detail = self.extractor.parser.parse_video_detail_page(html)
            logger.info(
                f"Video {bvid}: {len(detail.get('tags', []))} tags, "
                f"{len(detail.get('video_urls', []))} video streams, "
                f"{len(detail.get('audio_urls', []))} audio streams"
            )
            return detail
        except Exception as e:
            logger.error(f"Error fetching video detail for {bvid}: {e}")
            return None

    async def _enrich_videos_with_detail(
        self,
        videos: list[BiliVideoItem],
        max_detail_count: int = 0,
    ) -> list[BiliVideoItem]:
        """为每个视频补充详情页数据（标签、统计、下载链接）。"""
        fetch_all = max_detail_count <= 0
        total = len(videos) if fetch_all else min(max_detail_count, len(videos))
        logger.info(f"Enriching {total}/{len(videos)} videos with detail page data...")

        for i, video in enumerate(videos[:total]):
            if not video.bvid:
                continue
            detail = await self.crawl_video_detail(video.bvid)
            if detail:
                # 补充标签（列表 API 不提供）
                if detail.get("tags"):
                    video.tags = detail["tags"]
                # 用详情页的更准确统计数据覆盖
                if detail.get("play", 0) > 0:
                    video.play = detail["play"]
                if detail.get("like", 0) > 0:
                    video.like = detail["like"]
                if detail.get("coin", 0) > 0:
                    video.coin = detail["coin"]
                if detail.get("collect", 0) > 0:
                    video.collect = detail["collect"]
                if detail.get("share", 0) > 0:
                    video.share = detail["share"]
                if detail.get("danmaku", 0) > 0:
                    video.danmaku = detail["danmaku"]
                if detail.get("comment", 0) > 0:
                    video.comment = detail["comment"]
                if detail.get("duration", 0) > 0:
                    video.duration = detail["duration"]
                if detail.get("pubdate", 0) > 0:
                    video.pubdate = detail["pubdate"]
                # 下载链接
                video.video_urls = detail.get("video_urls", [])
                video.audio_urls = detail.get("audio_urls", [])
                video.accept_quality = detail.get("accept_quality", [])
                video.accept_description = detail.get("accept_description", [])
                # 补充描述（列表 API 有时为空）
                if detail.get("description") and not video.description:
                    video.description = detail["description"]

            logger.info(f"Enriched {i + 1}/{total}: {video.bvid}")
            await asyncio.sleep(1)  # 适度延迟

        return videos

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

            videos_data = await self._capture_videos_via_pagination(
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

            # 为每个视频补充详情页数据（标签、下载链接等）
            all_videos = await self._enrich_videos_with_detail(
                all_videos, max_count,
            )

        except Exception as e:
            logger.error(f"Error crawling user videos (browser mode): {e}")

        if max_count > 0:
            return all_videos[:max_count]
        return all_videos

    async def _capture_videos_via_pagination(
        self,
        page: Any,
        mid: str,
        max_count: int = 0,
    ) -> list[dict[str, Any]]:
        fetch_all = max_count <= 0
        videos_data: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        current_page = 1

        try:
            video_url = f"{self.config.space_url}/{mid}/video"
            async with RequestCapture(page, url_pattern="arc/search") as capture:
                await page.goto(video_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

                max_pages = 50 if fetch_all else max(1, (max_count // 30) + 2)
                max_retries = 3
                page_pause_time = 2

                while True:
                    new_on_page = 0
                    page_videos: list[dict[str, Any]] = []

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
                                                        page_videos.append(video)
                                                        new_on_page += 1
                            except (json.JSONDecodeError, KeyError):
                                continue

                    videos_data.extend(page_videos)
                    logger.info(
                        f"Page {current_page}: "
                        f"{new_on_page} new videos (total: {len(videos_data)})"
                    )

                    if not fetch_all and len(videos_data) >= max_count:
                        logger.info(f"Reached max_count: {max_count}")
                        break

                    if not fetch_all and current_page >= max_pages:
                        logger.info(f"Reached max_pages: {max_pages}")
                        break

                    has_next = await self._has_next_page(page)
                    if not has_next:
                        logger.info("No next page, reached last page")
                        break

                    clicked = await self._click_next_page(page)
                    if not clicked:
                        logger.warning("Failed to click next page")
                        break

                    current_page += 1
                    await asyncio.sleep(page_pause_time)

                    retry_count = 0
                    while retry_count < max_retries:
                        new_data_found = False
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
                                                            new_data_found = True
                                                            break
                                except (json.JSONDecodeError, KeyError):
                                    continue
                            if new_data_found:
                                break

                        if new_data_found:
                            break

                        retry_count += 1
                        logger.debug(
                            f"Waiting for page {current_page} data... "
                            f"retry {retry_count}/{max_retries}"
                        )
                        await asyncio.sleep(page_pause_time)

                    if retry_count >= max_retries:
                        logger.warning(
                            f"Page {current_page} data not loaded after {max_retries} retries"
                        )
                        break

        except Exception as e:
            logger.error(f"Pagination capture method error: {e}")

        return videos_data

    async def _has_next_page(self, page: Any) -> bool:
        try:
            result = await page.evaluate("""
                () => {
                    const nextBtn = document.querySelector('.vui_pagenation--btn-side:last-child');
                    if (!nextBtn) return false;
                    if (nextBtn.disabled) return false;
                    const text = nextBtn.textContent || '';
                    return text.includes('下一页');
                }
            """)
            return bool(result)
        except Exception as e:
            logger.debug(f"Error checking next page: {e}")
            return False

    async def _click_next_page(self, page: Any) -> bool:
        try:
            result = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('.vui_pagenation--btn-side');
                    let nextBtn = null;
                    for (const btn of btns) {
                        const text = btn.textContent || '';
                        if (text.includes('下一页')) {
                            nextBtn = btn;
                            break;
                        }
                    }
                    if (!nextBtn || nextBtn.disabled) return false;
                    nextBtn.click();
                    return true;
                }
            """)
            return bool(result)
        except Exception as e:
            logger.debug(f"Error clicking next page: {e}")
            return False

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
