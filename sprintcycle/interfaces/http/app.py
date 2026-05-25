"""FastAPI application factory for SprintCycle HTTP serving."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sprintcycle.application.http_factories import create_http_services

from .dashboard import (
    build_governance_router,
    build_execution_router,
    build_platform_router,
    build_config_router,
    build_overview_router,
)
from .public.execution import build_public_execution_router
from .public.health import build_health_router

_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"


def create_app(project_path: str = ".") -> FastAPI:
    # 创建 HTTP 层服务实例
    http_services = create_http_services(project_path)
    app = FastAPI(title="SprintCycle Console", version="0.9.2")

    if _DASHBOARD_DEV:
        # 常见的前端开发端口
        _p = 5173
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[f"http://127.0.0.1:{_p}", f"http://localhost:{_p}"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 注册路由 - 先注册 health 检查
    app.include_router(build_health_router())
    # 然后注册 public API
    app.include_router(build_public_execution_router(http_services, project_path))
    # 最后注册 dashboard 路由
    app.include_router(build_governance_router(http_services, project_path))
    app.include_router(build_execution_router(http_services, project_path))
    app.include_router(build_platform_router(http_services, project_path))
    app.include_router(build_config_router(http_services, project_path))
    app.include_router(build_overview_router(http_services, project_path))

    return app
