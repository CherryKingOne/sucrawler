from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger


def build_auth_parser(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            description="管理登录认证状态",
        )
    subparsers = parser.add_subparsers(dest="auth_command", help="认证子命令")

    login_parser = subparsers.add_parser("login", help="登录指定平台")
    login_parser.add_argument(
        "--platform",
        "-p",
        type=str,
        default="xiaohongshu",
        help="平台名称 (默认: xiaohongshu)",
    )
    login_parser.add_argument(
        "--login-type",
        "-t",
        type=str,
        choices=["qrcode", "phone", "cookie"],
        default="qrcode",
        help="登录方式 (默认: qrcode)",
    )
    login_parser.add_argument(
        "--cookie",
        type=str,
        help="Cookie 字符串（仅 cookie 登录方式有效）",
    )
    login_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="浏览器无头模式（仅扫码登录需显示浏览器）",
    )

    logout_parser = subparsers.add_parser("logout", help="登出指定平台")
    logout_parser.add_argument(
        "--platform",
        "-p",
        type=str,
        default="xiaohongshu",
        help="平台名称 (默认: xiaohongshu)",
    )

    status_parser = subparsers.add_parser("status", help="查看登录状态")
    status_parser.add_argument(
        "--platform",
        "-p",
        type=str,
        default="all",
        help="平台名称，all 表示查看所有 (默认: all)",
    )

    list_parser = subparsers.add_parser("list", help="列出所有已保存凭证的平台")

    return parser


async def auth_login(args: argparse.Namespace) -> int:
    platform = args.platform
    login_type = args.login_type

    print(f"正在登录平台: {platform}")
    print(f"登录方式: {login_type}")

    if platform != "xiaohongshu":
        print(f"错误：暂不支持平台 '{platform}'")
        return 1

    try:
        from sucrawler.auth.credential_store import CredentialStore
        from sucrawler.auth.types import LoginType
        from sucrawler.browser.manager.browser_manager import BrowserManager
        from sucrawler.browser.types import BrowserConfig
        from sucrawler.platforms.xiaohongshu.auth.xhs_login import XHSAuthenticator

        credential_store = CredentialStore()

        browser_config = BrowserConfig(
            enabled=True,
            mode="cdp",
            headless=args.headless,
            auto_close=False,
        )

        auth = XHSAuthenticator(
            login_type=LoginType(login_type),
            cookie_str=args.cookie or "",
            credential_store=credential_store,
        )

        if login_type == "cookie" and args.cookie:
            print("Cookie 登录模式...")
            bm = BrowserManager(browser_config)
            await bm.start()
            try:
                bm.set_authenticator(auth)
                success = await bm.ensure_logged_in()
                if success:
                    print("登录成功！")
                    return 0
                else:
                    print("登录失败，请检查 Cookie 是否有效")
                    return 1
            finally:
                await bm.stop()
        else:
            print("浏览器登录模式...")
            print("提示：请在弹出的浏览器窗口中完成登录")
            bm = BrowserManager(browser_config)
            await bm.start()
            try:
                bm.set_authenticator(auth)
                success = await bm.ensure_logged_in()
                if success:
                    print("登录成功！凭证已保存")
                    return 0
                else:
                    print("登录失败或超时")
                    return 1
            finally:
                await bm.stop()

    except ImportError as e:
        print(f"错误：缺少依赖 - {e}")
        print("请确保已安装 playwright: uv pip install playwright")
        return 1
    except Exception as e:
        logger.error(f"登录失败: {e}")
        print(f"登录失败: {e}")
        return 1


async def auth_logout(args: argparse.Namespace) -> int:
    platform = args.platform

    try:
        from sucrawler.auth.credential_store import CredentialStore

        store = CredentialStore()

        if not store.exists(platform):
            print(f"平台 '{platform}' 没有保存的登录凭证")
            return 0

        store.delete(platform)
        print(f"已清除平台 '{platform}' 的登录凭证")
        return 0

    except Exception as e:
        logger.error(f"登出失败: {e}")
        print(f"登出失败: {e}")
        return 1


async def auth_status(args: argparse.Namespace) -> int:
    platform = args.platform

    try:
        from sucrawler.auth.credential_store import CredentialStore

        store = CredentialStore()

        if platform == "all":
            platforms = store.list_platforms()
            if not platforms:
                print("没有保存任何平台的登录凭证")
                return 0

            print(f"已保存登录凭证的平台 ({len(platforms)} 个):")
            for p in platforms:
                valid = store.is_valid(p)
                status = "✓ 有效" if valid else "✗ 已过期/无效"
                print(f"  - {p}: {status}")
            return 0

        if not store.exists(platform):
            print(f"平台 '{platform}' 没有保存的登录凭证")
            return 0

        valid = store.is_valid(platform)
        credential = store.load(platform)

        print(f"平台: {platform}")
        print(f"状态: {'已登录 (有效)' if valid else '已过期/无效'}")
        if credential:
            print(f"登录方式: {credential.login_type.value}")
            print(f"创建时间: {credential.created_at}")
            print(f"更新时间: {credential.updated_at}")
            if credential.expires_at:
                print(f"过期时间: {credential.expires_at}")
            print(f"Cookie 数量: {len(credential.cookies)}")
        return 0

    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        print(f"获取状态失败: {e}")
        return 1


async def auth_list(args: argparse.Namespace) -> int:
    try:
        from sucrawler.auth.credential_store import CredentialStore

        store = CredentialStore()
        platforms = store.list_platforms()

        if not platforms:
            print("没有保存任何平台的登录凭证")
            return 0

        print(f"已保存登录凭证的平台 ({len(platforms)} 个):")
        for p in platforms:
            valid = store.is_valid(p)
            status = "有效" if valid else "已过期/无效"
            print(f"  - {p}: {status}")

        return 0

    except Exception as e:
        logger.error(f"获取列表失败: {e}")
        print(f"获取列表失败: {e}")
        return 1


async def auth_main() -> None:
    parser = build_auth_parser()
    args = parser.parse_args()

    if not args.auth_command:
        parser.print_help()
        sys.exit(1)

    if args.auth_command == "login":
        sys.exit(await auth_login(args))
    elif args.auth_command == "logout":
        sys.exit(await auth_logout(args))
    elif args.auth_command == "status":
        sys.exit(await auth_status(args))
    elif args.auth_command == "list":
        sys.exit(await auth_list(args))
    else:
        parser.print_help()
        sys.exit(1)
