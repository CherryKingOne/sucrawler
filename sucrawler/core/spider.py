from datetime import datetime
from enum import StrEnum

from sucrawler.common.types import MetaType, TaskId
from sucrawler.core.request import Request


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Task:
    def __init__(
        self,
        task_id: TaskId,
        request: Request,
        status: TaskStatus = TaskStatus.PENDING,
        retry_count: int = 0,
        error: str | None = None,
        created_at: datetime | None = None,
        meta: MetaType | None = None,
    ) -> None:
        self.task_id = task_id
        self.request = request
        self.status = status
        self.retry_count = retry_count
        self.error = error
        self.created_at = created_at or datetime.now()
        self.meta = meta or {}

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "request": self.request.to_dict(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "meta": self.meta,
        }
