from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class StorageType(StrEnum):
    MYSQL = "mysql"
    POSTGRES = "postgres"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    CSV = "csv"
    JSON = "json"


class DownloaderType(StrEnum):
    HTTPX = "httpx"
    AIOHTTP = "aiohttp"
    PLAYWRIGHT = "playwright"


class SchedulerType(StrEnum):
    MEMORY = "memory"
    REDIS = "redis"
