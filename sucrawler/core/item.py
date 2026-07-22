from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Item(BaseModel):
    id: str | None = None
    platform: str
    crawled_at: datetime = Field(default_factory=datetime.now)
    raw_data: dict[str, Any] | None = None
