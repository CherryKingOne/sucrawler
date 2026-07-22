from __future__ import annotations


class ConfigException(Exception):  # noqa: N818
    pass


def validate_settings(settings: object) -> bool:
    from .settings import Settings

    if not isinstance(settings, Settings):
        raise ConfigException("Invalid settings type")

    if settings.downloader.max_concurrent <= 0:
        raise ConfigException("downloader.max_concurrent must be greater than 0")

    if settings.downloader.timeout <= 0:
        raise ConfigException("downloader.timeout must be greater than 0")

    if settings.downloader.retry.max_attempts < 0:
        raise ConfigException("downloader.retry.max_attempts must be non-negative")

    if settings.downloader.retry.backoff_factor <= 0:
        raise ConfigException("downloader.retry.backoff_factor must be greater than 0")

    if settings.scheduler.max_tasks <= 0:
        raise ConfigException("scheduler.max_tasks must be greater than 0")

    if settings.storage.default_backend not in settings.storage.backends:
        raise ConfigException(
            f"storage.default_backend '{settings.storage.default_backend}' not found in backends"
        )

    for backend_name, backend in settings.storage.backends.items():
        if backend.type == "s3":
            from .settings import S3StorageBackendConfig

            if not isinstance(backend, S3StorageBackendConfig):
                continue
            if not backend.bucket:
                raise ConfigException(
                    f"storage.backends.{backend_name}.bucket must not be empty for s3 backend"
                )

    return True
