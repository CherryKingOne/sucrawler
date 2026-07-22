from __future__ import annotations

from api.routes.data_routes import router as data_router
from api.routes.task_routes import router as task_router

__all__ = ["task_router", "data_router"]
