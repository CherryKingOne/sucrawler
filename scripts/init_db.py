from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from sucrawler.config.loader import load_config
from sucrawler.storage.registry import get_storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize database tables")
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="dev",
        help="Environment (dev, test, prod)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Config directory path",
    )
    parser.add_argument(
        "--backend",
        "-b",
        type=str,
        default=None,
        help="Storage backend to initialize (uses default if not specified)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = load_config(config_path=args.config, env=args.env)

    backend_name = args.backend or config.storage.default_backend
    if backend_name not in config.storage.backends:
        logger.error(f"Backend '{backend_name}' not found in config")
        sys.exit(1)

    backend_config = config.storage.backends[backend_name]
    storage = get_storage(backend_name, backend_config)

    logger.info(f"Initializing storage backend: {backend_name}")

    if hasattr(storage, "init_db") and callable(storage.init_db):
        import asyncio

        asyncio.run(storage.init_db())
        logger.info("Database initialization completed")
    else:
        logger.warning(f"Storage backend '{backend_name}' does not support init_db")

    logger.info("Done")


if __name__ == "__main__":
    main()
