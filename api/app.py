from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from api.routes import data_router, task_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sucrawler API",
        description="Enterprise-level multi-platform crawler framework API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(task_router, prefix="/api/v1")
    app.include_router(data_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {"status": "healthy"}

    return app


app = create_app()
