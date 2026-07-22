from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.schemas.task_schema import (
    TaskCancelResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    if not request.url and not request.keyword:
        raise HTTPException(status_code=400, detail="Either url or keyword must be provided")

    task_id = f"{request.platform}-{request.spider_type}-{datetime.now().timestamp()}"
    now = datetime.now().isoformat()

    return TaskResponse(
        task_id=task_id,
        platform=request.platform,
        spider_type=request.spider_type,
        status="pending",
        progress=0.0,
        items_count=0,
        created_at=now,
        updated_at=now,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    platform: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> TaskListResponse:
    return TaskListResponse(
        total=0,
        page=page,
        page_size=page_size,
        items=[],
    )


@router.post("/{task_id}/cancel", response_model=TaskCancelResponse)
async def cancel_task(task_id: str) -> TaskCancelResponse:
    return TaskCancelResponse(
        task_id=task_id,
        success=True,
        message="Task cancellation requested",
    )
