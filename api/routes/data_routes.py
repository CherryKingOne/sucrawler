from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.data_schema import (
    DataExportResponse,
    DataListResponse,
    DataQueryRequest,
    DataStatsResponse,
)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("", response_model=DataListResponse)
async def query_data(
    platform: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> DataListResponse:
    return DataListResponse(
        total=0,
        page=page,
        page_size=page_size,
        items=[],
    )


@router.post("/query", response_model=DataListResponse)
async def query_data_post(request: DataQueryRequest) -> DataListResponse:
    return DataListResponse(
        total=0,
        page=request.page,
        page_size=request.page_size,
        items=[],
    )


@router.get("/stats", response_model=DataStatsResponse)
async def get_stats(platform: str | None = None) -> DataStatsResponse:
    return DataStatsResponse(
        platform=platform,
        total_items=0,
        today_items=0,
        last_crawled_at=None,
    )


@router.post("/export", response_model=DataExportResponse)
async def export_data(
    platform: str | None = None,
    format: str = "csv",
) -> DataExportResponse:
    if format not in {"csv", "json", "xlsx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return DataExportResponse(
        export_id=f"export-{platform or 'all'}-{format}",
        status="pending",
        format=format,
        total_items=0,
    )
