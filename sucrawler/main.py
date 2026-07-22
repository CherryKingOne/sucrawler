from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sucrawler",
        description="Enterprise-level multi-platform crawler framework",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version information",
    )
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="dev",
        help="Environment (dev, test, prod)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("run", help="Run a spider task")
    subparsers.add_parser("serve", help="Start API server")
    subparsers.add_parser("init-db", help="Initialize database")
    subparsers.add_parser("list-platforms", help="List available platforms")

    args = parser.parse_args()

    if args.version:
        print("sucrawler 0.1.0")
        return

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "serve":
        _cmd_serve(args)
    elif args.command == "init-db":
        _cmd_init_db(args)
    elif args.command == "list-platforms":
        _cmd_list_platforms(args)
    else:
        parser.print_help()


def _cmd_run(args: argparse.Namespace) -> None:
    print("Starting crawler...")
    print(f"Environment: {args.env}")
    print("Use scripts/run_spider.py for detailed spider control")


def _cmd_serve(args: argparse.Namespace) -> None:
    print("Starting API server...")
    print(f"Environment: {args.env}")
    print("Run with: uvicorn api.app:app --reload")


def _cmd_init_db(args: argparse.Namespace) -> None:
    print("Initializing database...")
    print(f"Environment: {args.env}")
    print("Use scripts/init_db.py for detailed database initialization")


def _cmd_list_platforms(args: argparse.Namespace) -> None:
    print("Available platforms:")
    print("  - xiaohongshu")


if __name__ == "__main__":
    main()
