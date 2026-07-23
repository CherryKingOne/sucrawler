"""媒体下载服务：下载视频和/或封面图片。

支持三种下载模式（通过 download_type 参数控制）：
- "video": 仅下载视频（通过 yt-dlp 从视频页面 URL 下载）
- "image": 仅下载封面图片
- "all":   同时下载视频和封面图片

video_url 字段存储的是浏览器可访问的视频页面 URL
（如 https://www.bilibili.com/video/BV1xxx），
视频下载通过调用 yt-dlp 子进程实现。

封面图片直接通过 httpx 下载保存。

依赖：
- yt-dlp（视频下载）: pip install yt-dlp 或 brew install yt-dlp
- ffmpeg（可选，yt-dlp 合并音视频流时需要）: brew install ffmpeg
"""

from __future__ import annotations

import asyncio
import shutil
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
# 单个文件下载超时（秒）
DOWNLOAD_TIMEOUT = 120


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
    try:
        async with client.stream(
            "GET", pic_url, headers=headers, timeout=DOWNLOAD_TIMEOUT,
        ) as response:
            if response.status_code != 200:
                logger.warning(
                    f"封面下载失败 HTTP {response.status_code}: {pic_url[:80]}...",
                )
                return False
            with output_path.open("wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    f.write(chunk)
        logger.info(f"封面下载完成: {image_id}{ext}")
        return True
    except Exception as e:
        logger.error(f"封面下载出错 {pic_url[:80]}...: {e}")
        return False


async def _download_video_ytdlp(
    video_id: str,
    video_url: str,
    video_dir: Path,
) -> bool:
    """通过 yt-dlp 下载视频到指定目录。

    Args:
        video_id: 视频 ID（bvid），用作文件名
        video_url: 视频页面 URL（如 https://www.bilibili.com/video/BV1xxx）
        video_dir: 视频保存目录
    """
    output_path = video_dir / f"{video_id}.mp4"
    if output_path.exists():
        logger.info(f"视频已存在，跳过: {video_id}.mp4")
        return True

    # 检查 yt-dlp 是否可用
    ytdlp_path = shutil.which("yt-dlp")
    if not ytdlp_path:
        logger.error(
            f"未找到 yt-dlp，无法下载视频 [{video_id}]。"
            "请安装: pip install yt-dlp 或 brew install yt-dlp"
        )
        return False

    cmd = [
        ytdlp_path,
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        "--no-warnings",
        video_url,
    ]

    try:
        logger.info(f"[{video_id}] 正在通过 yt-dlp 下载: {video_url}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_text = stderr.decode()[:300] if stderr else ""
            logger.error(f"[{video_id}] yt-dlp 下载失败 (code={proc.returncode}): {error_text}")
            return False
        logger.info(f"[{video_id}] 视频下载完成: {output_path.name}")
        return True
    except Exception as e:
        logger.error(f"[{video_id}] yt-dlp 下载异常: {e}")
        return False


async def download_media(
    items: list[Any],
    output_dir: Path,
    platform: str = "bilibili",
    download_type: str = "all",
) -> None:
    """批量下载视频和/或封面图片。

    Args:
        items: 爬取到的视频/笔记 item 列表（Pydantic model 或 dict）
        output_dir: 输出根目录（如 output/bilibili/博主名称）
        platform: 平台名称
        download_type: 下载类型 ("video"=仅视频, "image"=仅封面, "all"=全部)
    """
    download_video = download_type in ("video", "all")
    download_image = download_type in ("image", "all")

    video_dir = output_dir / "video"
    image_dir = output_dir / "image"

    if download_video:
        video_dir.mkdir(parents=True, exist_ok=True)
    if download_image:
        image_dir.mkdir(parents=True, exist_ok=True)

    total = len(items)
    video_success = 0
    image_success = 0

    targets = []
    if download_video:
        targets.append("视频")
    if download_image:
        targets.append("封面图片")
    logger.info(f"开始下载{'和'.join(targets)}：{total} 个项目，并发数 {MAX_CONCURRENT_DOWNLOADS}")

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(DOWNLOAD_TIMEOUT),
    ) as client:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

        async def _download_one(item: Any) -> tuple[bool, bool]:
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
                    return False, False

                video_url = data.get("video_url", "")
                pic_url = data.get("pic") or data.get("cover") or ""

                v_ok = False
                i_ok = False

                # 下载视频
                if download_video and video_url:
                    v_ok = await _download_video_ytdlp(str(video_id), video_url, video_dir)
                elif download_video and not video_url:
                    logger.warning(f"[{video_id}] 无视频页面 URL，跳过视频下载")

                # 下载封面
                if download_image and pic_url:
                    i_ok = await _download_image(client, str(video_id), pic_url, image_dir)
                elif download_image and not pic_url:
                    logger.warning(f"[{video_id}] 无封面 URL，跳过封面下载")

                return v_ok, i_ok

        tasks = [_download_one(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                logger.error(f"下载任务异常: {r}")
            elif isinstance(r, tuple):
                if r[0]:
                    video_success += 1
                if r[1]:
                    image_success += 1

    if download_video:
        logger.info(f"视频下载完成：{video_success}/{total} 个成功")
        logger.info(f"  视频目录: {video_dir}")
    if download_image:
        logger.info(f"封面下载完成：{image_success}/{total} 个成功")
        logger.info(f"  封面目录: {image_dir}")
