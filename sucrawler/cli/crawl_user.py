from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.config.loader import load_config
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.spiders.user_spider import XHSUserSpider
from sucrawler.utils.url_parser import extract_user_id_from_url


def build_crawl_user_parser(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            description="爬取指定平台的博主主页数据",
        )
    parser.add_argument(
        "--platform",
        "-p",
        type=str,
        default="xiaohongshu",
        help="平台名称 (默认: xiaohongshu)",
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        help="博主主页 URL",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="博主用户 ID（与 --url 二选一）",
    )
    parser.add_argument(
        "--max-notes",
        "-n",
        type=int,
        default=20,
        help="爬取的笔记数量上限 (默认: 20)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径 (JSON 格式)，不指定则打印到控制台",
    )
    parser.add_argument(
        "--cookie",
        type=str,
        help="小红书 Cookie（也可通过环境变量 XHS_COOKIE 设置）",
    )
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="dev",
        help="环境 (dev, test, prod)",
    )
    return parser


async def crawl_user(args: argparse.Namespace) -> int:
    if not args.url and not args.user_id:
        print("错误：必须提供 --url 或 --user-id 其中之一")
        print()
        print("示例：")
        print("  uv run sucrawler crawl-user --url https://www.xiaohongshu.com/user/profile/xxxxxxxx")
        print("  uv run sucrawler crawl-user --user-id xxxxxxxx")
        return 1

    user_id = args.user_id
    if args.url:
        extracted = extract_user_id_from_url(args.url)
        if not extracted:
            print(f"错误：无法从 URL 中提取用户 ID: {args.url}")
            return 1
        user_id = extracted
        logger.info(f"从 URL 提取用户 ID: {user_id}")

    load_config(env=args.env)

    xhs_config = XHSConfig()
    if args.cookie:
        xhs_config.cookie = args.cookie

    if not xhs_config.cookie:
        logger.warning("未设置 Cookie，部分接口可能无法正常访问")

    spider = XHSUserSpider(xhs_config)

    try:
        print(f"正在爬取博主信息，用户 ID: {user_id}")
        print("-" * 50)

        user_info = await spider.crawl_user_info(user_id)
        if user_info:
            print(f"昵称: {user_info.nickname}")
            print(f"简介: {user_info.desc}")
            print(f"粉丝: {user_info.fans_count}")
            print(f"关注: {user_info.follows_count}")
            print(f"获赞: {user_info.liked_count}")
            print(f"笔记数: {user_info.notes_count}")
        else:
            print("未获取到博主信息")

        print("-" * 50)
        print(f"正在爬取博主笔记，最多 {args.max_notes} 条...")

        notes = await spider.crawl_user_notes(user_id, max_count=args.max_notes)
        print(f"成功爬取 {len(notes)} 条笔记")

        result: dict[str, Any] = {
            "platform": args.platform,
            "user_id": user_id,
            "user_info": user_info.model_dump() if user_info else None,
            "notes_count": len(notes),
            "notes": [note.model_dump() for note in notes],
        }

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_path}")
        else:
            print("-" * 50)
            print("笔记列表：")
            for i, note in enumerate(notes[:10], 1):
                title = getattr(note, "title", "") or "(无标题)"
                liked = getattr(note, "liked_count", "N/A")
                print(f"  {i}. {title} - {liked} 赞")
            if len(notes) > 10:
                print(f"  ... 还有 {len(notes) - 10} 条")

        return 0
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        return 1
    finally:
        await spider.close()


async def crawl_user_main() -> None:
    parser = build_crawl_user_parser()
    args = parser.parse_args()
    sys.exit(await crawl_user(args))
