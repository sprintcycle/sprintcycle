"""FastAPI application factory for SprintCycle HTTP serving."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sprintcycle.api import SprintCycle
from sprintcycle.application.internal_api_service import InternalAPIService
from sprintcycle.application.public_api_service import PublicAPIService
from sprintcycle.infrastructure.config.runtime_config import DashboardPortDefaults

from .internal import build_internal_router
from .public import build_public_router

_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"


def create_app(project_path: str = ".") -> FastAPI:
    sc = SprintCycle(project_path=project_path)
    internal_api = InternalAPIService(sc)
    public_api = PublicAPIService(sc)
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

    app.include_router(build_public_router(public_api, project_path))
    app.include_router(build_internal_router(internal_api, project_path))

    return app
