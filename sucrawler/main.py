from __future__ import annotations

import argparse
import asyncio
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sucrawler",
        description="企业级多平台爬虫框架",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="显示版本信息",
    )
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="dev",
        help="环境 (dev, test, prod)",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    run_parser = subparsers.add_parser("run", help="运行爬虫任务")
    run_parser.add_argument("--platform", "-p", type=str, default="xiaohongshu", help="平台名称")
    run_parser.add_argument("--url", "-u", type=str, help="爬取 URL")
    run_parser.add_argument("--keyword", "-k", type=str, help="搜索关键词")

    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口")
    serve_parser.add_argument("--reload", action="store_true", help="自动重载")

    crawl_user_parser = subparsers.add_parser("crawl-user", help="爬取博主主页")
    crawl_user_parser.add_argument("--platform", "-p", type=str, default="xiaohongshu", help="平台名称")
    crawl_user_parser.add_argument("--url", "-u", type=str, help="博主主页 URL")
    crawl_user_parser.add_argument("--user-id", type=str, help="博主用户 ID")
    crawl_user_parser.add_argument("--max-notes", "-n", type=int, default=20, help="爬取笔记数量上限")
    crawl_user_parser.add_argument("--output", "-o", type=str, help="输出文件路径 (JSON)")
    crawl_user_parser.add_argument("--cookie", type=str, help="Cookie")
    crawl_user_parser.add_argument("--browser", action="store_true", default=False, help="使用浏览器模式 (CDP) 爬取")
    crawl_user_parser.add_argument("--headless", action="store_true", default=False, help="浏览器无头模式")
    crawl_user_parser.add_argument("--connect-existing", action="store_true", default=False, help="连接已有浏览器")
    crawl_user_parser.add_argument("--debug-port", type=int, default=9222, help="已有浏览器调试端口")

    subparsers.add_parser("init-db", help="初始化数据库")
    subparsers.add_parser("list-platforms", help="列出支持的平台")

    auth_parser = subparsers.add_parser("auth", help="登录认证管理")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", help="认证子命令")

    auth_login_parser = auth_subparsers.add_parser("login", help="登录指定平台")
    auth_login_parser.add_argument("--platform", "-p", type=str, default="xiaohongshu", help="平台名称")
    auth_login_parser.add_argument(
        "--login-type", "-t", type=str, choices=["qrcode", "phone", "cookie"], default="qrcode", help="登录方式"
    )
    auth_login_parser.add_argument("--cookie", type=str, help="Cookie 字符串")
    auth_login_parser.add_argument("--headless", action="store_true", default=False, help="浏览器无头模式")

    auth_logout_parser = auth_subparsers.add_parser("logout", help="登出指定平台")
    auth_logout_parser.add_argument("--platform", "-p", type=str, default="xiaohongshu", help="平台名称")

    auth_status_parser = auth_subparsers.add_parser("status", help="查看登录状态")
    auth_status_parser.add_argument("--platform", "-p", type=str, default="all", help="平台名称")

    auth_subparsers.add_parser("list", help="列出所有已保存凭证的平台")

    args = parser.parse_args()

    if args.version:
        print("sucrawler 0.1.0")
        return

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "serve":
        _cmd_serve(args)
    elif args.command == "crawl-user":
        asyncio.run(_cmd_crawl_user(args))
    elif args.command == "init-db":
        _cmd_init_db(args)
    elif args.command == "list-platforms":
        _cmd_list_platforms(args)
    elif args.command == "auth":
        asyncio.run(_cmd_auth(args))
    else:
        parser.print_help()


def _cmd_run(args: argparse.Namespace) -> None:
    print("Starting crawler...")
    print(f"Environment: {args.env}")
    print("Platform: {args.platform}".format(platform=args.platform))
    if args.url:
        print(f"URL: {args.url}")
    if args.keyword:
        print(f"Keyword: {args.keyword}")
    print("使用 scripts/run_spider.py 进行详细的爬虫控制")


def _cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


async def _cmd_crawl_user(args: argparse.Namespace) -> None:
    from sucrawler.cli.crawl_user import crawl_user

    exit_code = await crawl_user(args)
    sys.exit(exit_code)


def _cmd_init_db(args: argparse.Namespace) -> None:
    print("初始化数据库...")
    print(f"环境: {args.env}")
    print("使用 scripts/init_db.py 进行详细的数据库初始化")


def _cmd_list_platforms(args: argparse.Namespace) -> None:
    from sucrawler.platforms import PlatformRegistry

    platforms = PlatformRegistry.list_platforms()
    platform_names = {
        "xiaohongshu": "小红书",
        "bilibili": "哔哩哔哩",
    }
    print("支持的平台：")
    for p in platforms:
        name = platform_names.get(p, p)
        print(f"  - {p} ({name})")


async def _cmd_auth(args: argparse.Namespace) -> None:
    from sucrawler.cli.auth import auth_login, auth_logout, auth_status, auth_list

    if not args.auth_command:
        print("请指定认证子命令: login, logout, status, list")
        print("示例:")
        print("  uv run sucrawler auth login --platform xiaohongshu")
        print("  uv run sucrawler auth status")
        sys.exit(1)

    if args.auth_command == "login":
        exit_code = await auth_login(args)
    elif args.auth_command == "logout":
        exit_code = await auth_logout(args)
    elif args.auth_command == "status":
        exit_code = await auth_status(args)
    elif args.auth_command == "list":
        exit_code = await auth_list(args)
    else:
        print(f"未知的认证子命令: {args.auth_command}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
