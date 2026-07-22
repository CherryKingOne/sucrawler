from datetime import datetime

from pydantic import Field

from sucrawler.models.base import BaseModel
from sucrawler.models.enums import TaskStatus


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SoftDeleteMixin(BaseModel):
    is_deleted: bool = False
    deleted_at: datetime | None = None


class StatusMixin(BaseModel):
    status: TaskStatus = TaskStatus.PENDING
