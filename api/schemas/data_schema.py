from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataQueryRequest(BaseModel):
    platform: str | None = Field(default=None, description="Filter by platform")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional filters")


class DataResponse(BaseModel):
    id: str = Field(..., description="Data item ID")
    platform: str = Field(..., description="Platform name")
    crawled_at: datetime = Field(..., description="Crawl timestamp")
    raw_data: dict[str, Any] | None = Field(default=None, description="Raw data")


class DataListResponse(BaseModel):
    total: int = Field(..., description="Total number of data items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    items: list[DataResponse] = Field(default_factory=list, description="List of data items")


class DataStatsResponse(BaseModel):
    platform: str | None = Field(default=None, description="Platform name")
    total_items: int = Field(..., description="Total number of items")
    today_items: int = Field(default=0, description="Items crawled today")
    last_crawled_at: datetime | None = Field(default=None, description="Last crawl time")


class DataExportResponse(BaseModel):
    export_id: str = Field(..., description="Export task ID")
    status: str = Field(..., description="Export status")
    download_url: str | None = Field(default=None, description="Download URL when ready")
    format: str = Field(default="csv", description="Export format")
    total_items: int = Field(default=0, description="Total items to export")
