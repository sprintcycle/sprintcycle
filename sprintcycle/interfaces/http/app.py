"""FastAPI application factory for SprintCycle HTTP serving."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sprintcycle.application.http_factories import create_http_services
from sprintcycle.infrastructure.adapters.generic.config.runtime_config import DashboardPortDefaults

from .internal import build_internal_router
from .public import build_public_router

_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"


def create_app(project_path: str = ".") -> FastAPI:
    # 创建 HTTP 层服务实例
    http_services = create_http_services(project_path)
    app = FastAPI(title="SprintCycle Console", version="0.9.2")

    if _DASHBOARD_DEV:
        _p = DashboardPortDefaults.dev_port
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[f"http://127.0.0.1:{_p}", f"http://localhost:{_p}"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 注册路由
    app.include_router(build_public_router(http_services, project_path))
    app.include_router(build_internal_router(http_services, project_path))

    return app
