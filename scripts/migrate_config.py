from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

CONFIG_VERSION = "1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Config migration tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize config with version")
    init_parser.add_argument(
        "--config-dir",
        "-d",
        type=str,
        default="config",
        help="Config directory path",
    )

    check_parser = subparsers.add_parser("check", help="Check config version")
    check_parser.add_argument(
        "--config-dir",
        "-d",
        type=str,
        default="config",
        help="Config directory path",
    )

    convert_parser = subparsers.add_parser("convert", help="Convert config format")
    convert_parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input config file path",
    )
    convert_parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output config file path",
    )
    convert_parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["yaml", "json"],
        default="yaml",
        help="Output format",
    )

    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data or {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_config(config_dir: str) -> None:
    config_path = Path(config_dir)
    base_config = load_yaml(config_path / "base.yaml")

    if "version" in base_config:
        logger.info(f"Config already has version: {base_config['version']}")
        return

    base_config["version"] = CONFIG_VERSION
    save_yaml(config_path / "base.yaml", base_config)
    logger.info(f"Config initialized with version {CONFIG_VERSION}")


def check_config(config_dir: str) -> None:
    config_path = Path(config_dir)
    base_config = load_yaml(config_path / "base.yaml")

    version = base_config.get("version", "unknown")
    logger.info(f"Config version: {version}")
    logger.info(f"Current version: {CONFIG_VERSION}")

    if version == CONFIG_VERSION:
        logger.info("Config is up to date")
    else:
        logger.warning("Config version mismatch, consider migrating")


def convert_config(input_path: str, output_path: str, output_format: str) -> None:
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    data = load_yaml(input_file)

    if output_format == "yaml":
        save_yaml(output_file, data)
    elif output_format == "json":
        save_json(output_file, data)

    logger.info(f"Converted {input_path} -> {output_path} ({output_format})")


def main() -> None:
    args = parse_args()

    if args.command == "init":
        init_config(args.config_dir)
    elif args.command == "check":
        check_config(args.config_dir)
    elif args.command == "convert":
        convert_config(args.input, args.output, args.format)
    else:
        logger.error("Unknown command. Use --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
