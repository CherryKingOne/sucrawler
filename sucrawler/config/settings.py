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


class RetryMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    max_attempts: int = 3
    backoff_factor: float = 2.0


class RateLimitMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    requests_per_second: float = 10.0


class UserAgentMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    rotate: bool = True


class ProxyMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    proxy_list: list[str] = []


class LogMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    level: str = "INFO"


class StatsMiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True


class MiddlewareConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    retry: RetryMiddlewareConfig = Field(default_factory=RetryMiddlewareConfig)
    rate_limit: RateLimitMiddlewareConfig = Field(default_factory=RateLimitMiddlewareConfig)
    user_agent: UserAgentMiddlewareConfig = Field(default_factory=UserAgentMiddlewareConfig)
    proxy: ProxyMiddlewareConfig = Field(default_factory=ProxyMiddlewareConfig)
    log: LogMiddlewareConfig = Field(default_factory=LogMiddlewareConfig)
    stats: StatsMiddlewareConfig = Field(default_factory=StatsMiddlewareConfig)


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


class JsonStorageBackendConfig(StorageBackendConfig):
    type: Literal["json"] = "json"
    file_path: str = "./data/items.json"


class CsvStorageBackendConfig(StorageBackendConfig):
    type: Literal["csv"] = "csv"
    file_path: str = "./data/items.csv"


class SqliteStorageBackendConfig(StorageBackendConfig):
    type: Literal["sqlite"] = "sqlite"
    db_path: str = "./data/sucrawler.db"


class MysqlStorageBackendConfig(StorageBackendConfig):
    type: Literal["mysql"] = "mysql"
    host: str = "localhost"
    port: int = 3306
    database: str = "sucrawler"
    user: str = "root"
    password: str = ""


class PostgresStorageBackendConfig(StorageBackendConfig):
    type: Literal["postgres"] = "postgres"
    host: str = "localhost"
    port: int = 5432
    database: str = "sucrawler"
    user: str = "postgres"
    password: str = ""


class MongodbStorageBackendConfig(StorageBackendConfig):
    type: Literal["mongodb"] = "mongodb"
    uri: str = "mongodb://localhost:27017"
    database: str = "sucrawler"
    collection: str = "items"


class RedisStorageBackendConfig(StorageBackendConfig):
    type: Literal["redis"] = "redis"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""


class EsStorageBackendConfig(StorageBackendConfig):
    type: Literal["es", "elasticsearch"] = "elasticsearch"
    hosts: list[str] = ["http://localhost:9200"]
    index: str = "sucrawler"


def get_storage_backend_discriminator(v: object) -> str:
    if isinstance(v, dict):
        type_val = v.get("type", "local")
        return str(type_val)
    if isinstance(v, StorageBackendConfig):
        return v.type
    return "local"


StorageBackend = Annotated[
    Annotated[LocalStorageBackendConfig, Tag("local")]
    | Annotated[S3StorageBackendConfig, Tag("s3")]
    | Annotated[JsonStorageBackendConfig, Tag("json")]
    | Annotated[CsvStorageBackendConfig, Tag("csv")]
    | Annotated[SqliteStorageBackendConfig, Tag("sqlite")]
    | Annotated[MysqlStorageBackendConfig, Tag("mysql")]
    | Annotated[PostgresStorageBackendConfig, Tag("postgres")]
    | Annotated[MongodbStorageBackendConfig, Tag("mongodb")]
    | Annotated[RedisStorageBackendConfig, Tag("redis")]
    | Annotated[EsStorageBackendConfig, Tag("elasticsearch")]
    | Annotated[EsStorageBackendConfig, Tag("es")],
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
