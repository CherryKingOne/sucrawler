from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    platform: str = Field(..., description="Platform name")
    spider_type: str = Field(default="detail", description="Spider type")
    url: str | None = Field(default=None, description="URL to crawl")
    keyword: str | None = Field(default=None, description="Keyword to search")
    priority: int = Field(default=0, description="Task priority")
    meta: dict[str, Any] = Field(default_factory=dict, description="Additional meta data")


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Task ID")
    platform: str = Field(..., description="Platform name")
    spider_type: str = Field(..., description="Spider type")
    status: str = Field(..., description="Task status")
    progress: float = Field(default=0.0, description="Task progress (0-1)")
    items_count: int = Field(default=0, description="Number of items crawled")
    error: str | None = Field(default=None, description="Error message if failed")
    created_at: str = Field(..., description="Task creation time")
    updated_at: str | None = Field(default=None, description="Task last update time")


class TaskListResponse(BaseModel):
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    items: list[TaskResponse] = Field(default_factory=list, description="List of tasks")


class TaskCancelResponse(BaseModel):
    task_id: str = Field(..., description="Task ID")
    success: bool = Field(..., description="Whether the task was cancelled successfully")
    message: str = Field(default="", description="Additional message")
