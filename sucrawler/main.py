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

    subparsers.add_parser("init-db", help="初始化数据库")
    subparsers.add_parser("list-platforms", help="列出支持的平台")

    args = parser.parse_args()

    if args.version:
        print("sucrawler 0.1.0")
        return

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "serve":
        _cmd_serve(args)
    elif args.command == "crawl-user":
        _cmd_crawl_user(args)
    elif args.command == "init-db":
        _cmd_init_db(args)
    elif args.command == "list-platforms":
        _cmd_list_platforms(args)
    else:
        parser.print_help()


def _cmd_run(args: argparse.Namespace) -> None:
    from scripts.run_spider import main as run_spider_main

    sys.argv = [
        "run_spider.py",
        "--platform", args.platform,
        "--env", args.env,
    ]
    if args.url:
        sys.argv.extend(["--url", args.url])
    if args.keyword:
        sys.argv.extend(["--keyword", args.keyword])

    asyncio.run(run_spider_main())


def _cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _cmd_crawl_user(args: argparse.Namespace) -> None:
    from scripts.crawl_user import main as crawl_user_main

    sys.argv = ["crawl_user.py"]
    if args.platform:
        sys.argv.extend(["--platform", args.platform])
    if args.url:
        sys.argv.extend(["--url", args.url])
    if args.user_id:
        sys.argv.extend(["--user-id", args.user_id])
    if args.max_notes:
        sys.argv.extend(["--max-notes", str(args.max_notes)])
    if args.output:
        sys.argv.extend(["--output", args.output])
    if args.cookie:
        sys.argv.extend(["--cookie", args.cookie])
    sys.argv.extend(["--env", args.env])

    asyncio.run(crawl_user_main())


def _cmd_init_db(args: argparse.Namespace) -> None:
    print("初始化数据库...")
    print(f"环境: {args.env}")
    print("使用 scripts/init_db.py 进行详细的数据库初始化")


def _cmd_list_platforms(args: argparse.Namespace) -> None:
    print("支持的平台：")
    print("  - xiaohongshu (小红书)")


if __name__ == "__main__":
    main()
