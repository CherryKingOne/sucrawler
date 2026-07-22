from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = "sucrawler"
    log_level: str = "INFO"
    env: str = "development"


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["memory", "redis"] = "memory"
    max_tasks: int = 1000


class RetryConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_attempts: int = 3
    backoff_factor: float = 2.0


class DownloaderConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["httpx", "aiohttp", "playwright"] = "httpx"
    timeout: int = 30
    max_concurrent: int = 10
    retry: RetryConfig = Field(default_factory=RetryConfig)


class RateLimitConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    requests_per_second: float = 10.0


class UserAgentConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    rotate: bool = True


class MiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    retry: bool = True
    rate_limit: bool = True
    user_agent: bool = True
    proxy: bool = False
    log: bool = True
    stats: bool = True


class StorageBackendConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str = "local"
    name: str = "default"


class LocalStorageBackendConfig(StorageBackendConfig):
    type: Literal["local"] = "local"
    base_path: str = "./data"


class S3StorageBackendConfig(StorageBackendConfig):
    type: Literal["s3"] = "s3"
    bucket: str = ""
    region: str = "us-east-1"
    access_key: str = ""
    secret_key: str = ""


def get_storage_backend_discriminator(v: object) -> str:
    if isinstance(v, dict):
        type_val = v.get("type", "local")
        return str(type_val)
    if isinstance(v, StorageBackendConfig):
        return v.type
    return "local"


StorageBackend = Annotated[
    Annotated[LocalStorageBackendConfig, Tag("local")]
    | Annotated[S3StorageBackendConfig, Tag("s3")],
    Discriminator(get_storage_backend_discriminator),
]


class StorageConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_backend: str = "default"
    backends: dict[str, StorageBackend] = Field(
        default_factory=lambda: {"default": LocalStorageBackendConfig()}  # type: ignore[arg-type]
    )


class PlatformConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    base_url: str = ""
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    app: AppConfig = Field(default_factory=AppConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    middleware: MiddlewareConfig = Field(default_factory=MiddlewareConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    platforms: dict[str, PlatformConfig] = Field(default_factory=dict)
