class CrawlerException(Exception):  # noqa: N818
    pass


class DownloadException(CrawlerException):  # noqa: N818
    pass


class ParseException(CrawlerException):  # noqa: N818
    pass


class ExtractException(CrawlerException):  # noqa: N818
    pass


class StorageException(CrawlerException):  # noqa: N818
    pass


class SchedulerException(CrawlerException):  # noqa: N818
    pass


class MiddlewareException(CrawlerException):  # noqa: N818
    pass


class PipelineException(CrawlerException):  # noqa: N818
    pass


class PlatformNotFoundException(CrawlerException):  # noqa: N818
    pass


class ConfigException(CrawlerException):  # noqa: N818
    pass
