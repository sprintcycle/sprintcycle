"""
SprintCycle Dashboard — FastAPI 应用

REST API + SSE 实时事件流，调用 SprintCycle API。
默认 ``ExecutionEventBackend`` 为 ``SQLiteMQEventBackend``（按项目落库）；SSE 仍按各 ``EventType``
逐一 ``on`` 订阅，``emit`` 路径会 **await** 异步 handler，避免纯 MQ 同步派发丢协程。

职责上限
- 只保留路由、SSE、静态资源挂载和请求适配。
- 不承载业务裁决、状态推进、评分实现或观测投影组装。
- 复杂 payload 应交给 ``SprintCycle`` 或各层 facade/view 构造。
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sprintcycle.api import SprintCycle
from sprintcycle.application.internal_api_service import InternalAPIService
from sprintcycle.application.public_api_service import PublicAPIService
from sprintcycle.infrastructure.config.runtime_config import DashboardPortDefaults
from sprintcycle.execution.events import EventType, get_execution_event_backend
from sprintcycle.interfaces.http import build_internal_router, build_public_router

from .sse import SSEEventHandler, get_client_manager


_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"
_event_handler: Optional[SSEEventHandler] = None


def create_app(project_path: str = ".") -> FastAPI:
    sc = SprintCycle(project_path=project_path)
    internal_api = InternalAPIService(sc)
    public_api = PublicAPIService(sc)
    event_bus = get_execution_event_backend()
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

    client_manager = get_client_manager()

    global _event_handler
    _event_handler = SSEEventHandler(client_manager)
    _event_handler.start()

    for event_type in EventType:
        if event_type is EventType.CONFIG_CHANGED:
            continue
        event_bus.on(event_type, lambda event: _event_handler.handle_event(event) if _event_handler else None)

    app.include_router(build_public_router(public_api, project_path))
    app.include_router(build_internal_router(internal_api, project_path))

    return app
