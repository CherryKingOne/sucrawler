from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .settings import Settings
from .validator import ConfigException, validate_settings


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigException(f"Config file {path} must contain a YAML mapping")
        return data


def _get_env_value(key: str, current: Any) -> Any:
    env_key = "SUCRAWLER_" + key.upper().replace(".", "_")
    env_val = os.getenv(env_key)
    if env_val is None:
        return current
    if isinstance(current, bool):
        return env_val.lower() in ("1", "true", "yes", "on")
    if isinstance(current, int):
        return int(env_val)
    if isinstance(current, float):
        return float(env_val)
    return env_val


def _apply_env_overrides(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result = data.copy()
    for key, value in result.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result[key] = _apply_env_overrides(value, full_key)
        else:
            result[key] = _get_env_value(full_key, value)
    return result


def load_config(config_path: str | None = None, env: str | None = None) -> Settings:
    load_dotenv()

    if env is None:
        env = os.getenv("SUCRAWLER_ENV", "development")

    if config_path is None:
        config_path = os.getenv("SUCRAWLER_CONFIG_DIR", "config")

    config_dir = Path(config_path)

    base_config = _load_yaml(config_dir / "base.yaml")
    env_config = _load_yaml(config_dir / f"{env}.yaml")

    merged = _deep_merge(base_config, env_config)
    merged = _apply_env_overrides(merged)

    settings = Settings.model_validate(merged)
    validate_settings(settings)

    return settings
