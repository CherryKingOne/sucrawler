from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from sucrawler.config.loader import load_config
from sucrawler.platforms.xiaohongshu.config import XHSConfig
from sucrawler.platforms.xiaohongshu.spiders.browser_spider import XHSBrowserSpider
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
        default=0,
        help="爬取的笔记数量上限 (默认: 0 = 全部)",
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
    parser.add_argument(
        "--browser",
        action="store_true",
        default=False,
        help="使用浏览器模式 (CDP) 爬取，反检测能力更强",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="浏览器无头模式（不显示窗口），仅在 --browser 模式下有效",
    )
    parser.add_argument(
        "--connect-existing",
        action="store_true",
        default=False,
        help="连接已有浏览器（需先以调试模式启动 Chrome），便于先登录再爬取",
    )
    parser.add_argument(
        "--debug-port",
        type=int,
        default=9222,
        help="已有浏览器的调试端口 (默认: 9222)",
    )
    return parser


async def crawl_user(args: argparse.Namespace) -> int:
    if not args.url and not args.user_id:
        print("错误：必须提供 --url 或 --user-id 其中之一")
        print()
        print("示例：")
        print("  uv run sucrawler crawl-user --url https://www.xiaohongshu.com/user/profile/xxxxxxxx")
        print("  uv run sucrawler crawl-user --user-id xxxxxxxx")
        print("  uv run sucrawler crawl-user --user-id xxxxxxxx --browser")
        print("  uv run sucrawler crawl-user --user-id xxxxxxxx --browser --connect-existing")
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

    if args.browser:
        xhs_config.use_browser = True
        browser_updates = {"enabled": True, "mode": "cdp", "headless": args.headless}
        if args.connect_existing:
            browser_updates["cdp_connect_existing"] = True
            browser_updates["debug_port"] = args.debug_port
        xhs_config.browser = xhs_config.browser.model_copy(update=browser_updates)

    if not xhs_config.use_browser and not xhs_config.cookie:
        logger.warning("未设置 Cookie，部分接口可能无法正常访问")
        logger.info("提示：可使用 --browser 参数启用浏览器模式，绕过签名验证")

    if xhs_config.use_browser:
        spider = XHSBrowserSpider(xhs_config)
        logger.info("使用浏览器 (CDP) 模式爬取")
    else:
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
