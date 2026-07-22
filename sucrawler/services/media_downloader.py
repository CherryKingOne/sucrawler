"""媒体下载服务：自动下载视频和封面图片。

视频下载流程：
1. 从 video_urls 中选取最高分辨率的视频流 URL
2. 从 audio_urls 中选取最高码率的音频流 URL
3. 分别下载视频流和音频流到临时文件
4. 使用 ffmpeg 合并为 MP4 文件

封面图片直接下载保存。
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

# Bilibili 下载所需的请求头
BILI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
}

# 下载并发数
MAX_CONCURRENT_DOWNLOADS = 3
# 单个流下载超时（秒）
DOWNLOAD_TIMEOUT = 120


async def _download_file(
    client: httpx.AsyncClient,
    url: str,
    output_path: Path,
    headers: dict[str, str] | None = None,
) -> bool:
    """下载单个文件到指定路径。"""
    try:
        req_headers = headers or BILI_HEADERS
        async with client.stream(
            "GET", url, headers=req_headers, timeout=DOWNLOAD_TIMEOUT,
        ) as response:
            if response.status_code != 200:
                logger.warning(
                    f"下载失败 HTTP {response.status_code}: {url[:80]}...",
                )
                return False
            with output_path.open("wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    f.write(chunk)
        logger.debug(f"下载完成: {output_path.name} ({output_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        logger.error(f"下载出错 {url[:80]}...: {e}")
        return False


async def _merge_video_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
) -> bool:
    """使用 ffmpeg 合并视频和音频流为 MP4。"""
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c", "copy",
        "-y",
        str(output_path),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(
                f"ffmpeg 合并失败 (code={proc.returncode}): "
                f"{stderr.decode()[:200]}",
            )
            return False
        logger.info(f"合并完成: {output_path.name}")
        return True
    except FileNotFoundError:
        logger.error("未找到 ffmpeg，请先安装: brew install ffmpeg")
        return False
    except Exception as e:
        logger.error(f"ffmpeg 合并异常: {e}")
        return False


def _pick_best_url(urls: list[Any]) -> str | None:
    """从 URL 列表中选取最佳 URL。

    优先选择 upos-sz 域名（更稳定），其次取第一个。
    支持两种格式：
    - list[str]: 直接使用
    - list[dict]: 取 bandwidth 最大的
    """
    if not urls:
        return None
    # 统一转为 (url, bandwidth) 列表
    parsed: list[tuple[str, int]] = []
    for item in urls:
        if isinstance(item, str):
            parsed.append((item, 0))
        elif isinstance(item, dict):
            url = item.get("url") or item.get("baseUrl") or item.get("base_url", "")
            bw = item.get("bandwidth", 0)
            if url:
                parsed.append((url, bw))
    if not parsed:
        return None
    # 优先 upos-sz 域名，其次按 bandwidth 降序
    parsed.sort(key=lambda x: ("upos-sz" not in x[0], -x[1]))
    return parsed[0][0]


def _get_all_urls(urls: list[Any]) -> list[str]:
    """从 URL 列表中提取所有 URL 字符串，优先 upos-sz 域名。"""
    if not urls:
        return []
    result: list[str] = []
    for item in urls:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            url = item.get("url") or item.get("baseUrl") or item.get("base_url", "")
            if url:
                result.append(url)
    # upos-sz 域名排前面
    result.sort(key=lambda u: "upos-sz" not in u)
    return result


async def _try_download_urls(
    client: httpx.AsyncClient,
    urls: list[str],
    output_path: Path,
    label: str = "",
) -> bool:
    """尝试多个 URL 逐个下载，直到成功。"""
    for i, url in enumerate(urls):
        if await _download_file(client, url, output_path):
            return True
        logger.debug(f"{label} URL {i+1}/{len(urls)} 失败，尝试下一个...")
    return False


async def _download_video(
    client: httpx.AsyncClient,
    video_id: str,
    video_urls: list[Any],
    audio_urls: list[Any],
    video_dir: Path,
) -> bool:
    """下载单个视频（最高分辨率视频流 + 最高码率音频流 → MP4）。"""
    all_video_urls = _get_all_urls(video_urls)
    all_audio_urls = _get_all_urls(audio_urls)

    if not all_video_urls:
        logger.warning(f"视频 {video_id} 无可用视频流 URL，跳过")
        return False

    output_path = video_dir / f"{video_id}.mp4"
    if output_path.exists():
        logger.info(f"视频已存在，跳过: {video_id}.mp4")
        return True

    # 创建临时目录
    tmp_dir = Path(tempfile.mkdtemp(prefix="bili_dl_"))
    try:
        # 下载视频流（尝试多个 URL）
        video_tmp = tmp_dir / "video.m4s"
        logger.info(f"[{video_id}] 下载视频流 ({len(all_video_urls)} 个候选 URL)...")
        if not await _try_download_urls(client, all_video_urls, video_tmp, f"[{video_id}] 视频"):
            logger.error(f"[{video_id}] 所有视频流 URL 均下载失败")
            return False

        if all_audio_urls:
            # 下载音频流（尝试多个 URL）
            audio_tmp = tmp_dir / "audio.m4s"
            logger.info(f"[{video_id}] 下载音频流 ({len(all_audio_urls)} 个候选 URL)...")
            if not await _try_download_urls(client, all_audio_urls, audio_tmp, f"[{video_id}] 音频"):
                logger.warning(f"[{video_id}] 所有音频流 URL 均下载失败，仅保存视频流")
                shutil.copy2(video_tmp, output_path)
                logger.info(f"[{video_id}] 已保存（无音频）: {output_path.name}")
                return True
            # 合并视频和音频
            logger.info(f"[{video_id}] 合并音视频流...")
            return await _merge_video_audio(video_tmp, audio_tmp, output_path)
        else:
            # 无音频 URL，直接复制视频流
            shutil.copy2(video_tmp, output_path)
            logger.info(f"[{video_id}] 已保存（无音频）: {output_path.name}")
            return True
    finally:
        # 清理临时文件
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _download_image(
    client: httpx.AsyncClient,
    image_id: str,
    pic_url: str,
    image_dir: Path,
) -> bool:
    """下载封面图片。"""
    if not pic_url:
        return False

    # 根据URL判断扩展名
    if ".png" in pic_url:
        ext = ".png"
    else:
        ext = ".jpg"

    output_path = image_dir / f"{image_id}{ext}"
    if output_path.exists():
        logger.debug(f"封面已存在，跳过: {image_id}{ext}")
        return True

    # 封面图片不需要特殊 Referer
    headers = {
        "User-Agent": BILI_HEADERS["User-Agent"],
    }
    success = await _download_file(client, pic_url, output_path, headers=headers)
    if success:
        logger.info(f"封面下载完成: {image_id}{ext}")
    return success


async def download_media(
    items: list[Any],
    output_dir: Path,
    platform: str = "bilibili",
) -> None:
    """批量下载视频和封面图片。

    Args:
        items: 爬取到的视频/笔记 item 列表（Pydantic model 或 dict）
        output_dir: 输出根目录（如 output/bilibili/博主名称）
        platform: 平台名称
    """
    video_dir = output_dir / "video"
    image_dir = output_dir / "image"
    video_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    headers = BILI_HEADERS if platform == "bilibili" else {
        "User-Agent": BILI_HEADERS["User-Agent"],
    }

    total = len(items)
    success_count = 0
    logger.info(f"开始下载媒体文件：{total} 个视频，并发数 {MAX_CONCURRENT_DOWNLOADS}")

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(DOWNLOAD_TIMEOUT),
    ) as client:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

        async def _download_one(item: Any) -> bool:
            async with semaphore:
                # 提取字段（兼容 Pydantic model 和 dict）
                if hasattr(item, "model_dump"):
                    data = item.model_dump(mode="json")
                elif isinstance(item, dict):
                    data = item
                else:
                    data = vars(item)

                video_id = data.get("bvid") or data.get("aid") or data.get("note_id") or ""
                if not video_id:
                    logger.warning("无法获取视频 ID，跳过")
                    return False

                video_urls = data.get("video_urls", [])
                audio_urls = data.get("audio_urls", [])
                pic_url = data.get("pic") or data.get("cover") or ""

                # 下载视频
                video_ok = False
                if video_urls:
                    video_ok = await _download_video(
                        client, str(video_id), video_urls, audio_urls, video_dir,
                    )
                else:
                    logger.info(f"[{video_id}] 无视频流 URL，跳过视频下载")

                # 下载封面
                if pic_url:
                    await _download_image(client, str(video_id), pic_url, image_dir)

                return video_ok

        tasks = [_download_one(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if r is True:
                success_count += 1
            elif isinstance(r, Exception):
                logger.error(f"下载任务异常: {r}")

    logger.info(f"媒体下载完成：{success_count}/{total} 个视频成功")
    logger.info(f"  视频目录: {video_dir}")
    logger.info(f"  封面目录: {image_dir}")
