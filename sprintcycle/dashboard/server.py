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

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from sprintcycle.api import SprintCycle
from sprintcycle.config.runtime_config import DashboardPortDefaults
from sprintcycle.execution.events import Event, EventType, get_execution_event_backend

from . import config_center
from . import platform_state
from .workbench import DashboardWorkbenchService

# ─── SSE 客户端管理 ───

class SSEClient:
    """SSE 客户端"""
    def __init__(self, client_id: str, queue: asyncio.Queue):
        self.client_id = client_id
        self.queue = queue

    async def send(self, event: Event) -> None:
        """发送事件到客户端"""
        message = event.to_sse_message()
        await self.queue.put(message)

    async def send_raw(self, message: str) -> None:
        """发送原始消息到客户端"""
        await self.queue.put(message)


class SSEClientManager:
    """SSE 客户端管理器"""
    def __init__(self):
        self._clients: Dict[str, SSEClient] = {}
        self._lock = asyncio.Lock()

    async def create_client(self) -> SSEClient:
        """创建新的客户端"""
        client_id = str(uuid.uuid4())
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        client = SSEClient(client_id, queue)
        async with self._lock:
            self._clients[client_id] = client
        logger.info(f"SSE client connected: {client_id}")
        return client

    async def remove_client(self, client_id: str) -> None:
        """移除客户端"""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"SSE client disconnected: {client_id}")

    async def broadcast(self, event: Event) -> None:
        """广播事件到所有客户端"""
        async with self._lock:
            clients = list(self._clients.values())

        if not clients:
            return

        message = event.to_sse_message()
        disconnected = []

        for client in clients:
            try:
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"SSE client queue full: {client.client_id}")
                disconnected.append(client.client_id)

        for client_id in disconnected:
            await self.remove_client(client_id)

    def get_client_count(self) -> int:
        """获取当前客户端数量"""
        return len(self._clients)


_client_manager: Optional[SSEClientManager] = None

STATIC_DIR = Path(__file__).resolve().parent / "static"
_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"

_NO_STATIC_BODY = """<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"><title>SprintCycle Dashboard</title></head>
<body style="font-family:system-ui;padding:2rem;background:#0f172a;color:#e2e8f0">
<h1>SprintCycle Dashboard</h1>
<p>未找到前端构建产物（<code>static/index.html</code>）。请在仓库根目录执行：</p>
<pre style="background:#1e293b;padding:1rem;border-radius:8px">cd frontend && npm install && npm run build</pre>
</body>
</html>"""


def get_client_manager() -> SSEClientManager:
    global _client_manager
    if _client_manager is None:
        _client_manager = SSEClientManager()
    return _client_manager


async def _build_platform_summary(sc: SprintCycle, client_manager: SSEClientManager) -> Dict[str, Any]:
    st = sc.status()
    raw = st.to_dict() if hasattr(st, "to_dict") else {}
    executions: list = []
    if raw.get("success") and isinstance(raw.get("executions"), list):
        executions = raw["executions"]
    snap = platform_state.get_platform_snapshot(
        project_path=sc.project_path,
        sse_client_count=client_manager.get_client_count(),
        executions=executions,
    )
    snap["status_query_ms"] = round(float(raw.get("duration", 0) or 0) * 1000.0, 2)
    hitl = await sc.hitl_pending()
    pend = hitl.get("data") if isinstance(hitl, dict) else []
    snap["hitl"] = {"open_requests": len(pend) if isinstance(pend, list) else 0}
    try:
        console = sc.console_overview(limit=20)
        snap["console"] = console.get("data", {}) if isinstance(console, dict) else {}
    except Exception:
        snap["console"] = {}
    return snap


async def _read_governance_reports(sc: SprintCycle) -> Dict[str, Any]:
    from sprintcycle.config.runtime_config import RuntimeConfig

    cfg = RuntimeConfig.from_project(sc.project_path)
    root = Path(sc.project_path).expanduser().resolve()
    rel = (cfg.governance_report_dir or ".sprintcycle").strip() or ".sprintcycle"
    out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    last = out_dir / "governance_last.json"
    planning = out_dir / "governance_planning_last.json"
    if not last.is_file() and not planning.is_file():
        raise HTTPException(status_code=404, detail="未找到治理报告，请先运行 governance check 或 Sprint 门禁")
    payload: Dict[str, Any] = {}
    if planning.is_file():
        payload["planning"] = json.loads(planning.read_text(encoding="utf-8"))
    if last.is_file():
        payload["review"] = json.loads(last.read_text(encoding="utf-8"))
    return payload


class SSEEventHandler:
    def __init__(self, client_manager: SSEClientManager):
        self._client_manager = client_manager
        self._is_running = False

    async def handle_event(self, event: Event) -> None:
        if self._is_running:
            await self._client_manager.broadcast(event)

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False


class PlanRequest(BaseModel):
    intent: str = ""
    mode: str = "auto"
    target: Optional[str] = None
    release_plan_yaml: Optional[str] = None
    release_plan_path: Optional[str] = None
    product: Optional[str] = None
    reference_paths: Optional[List[str]] = None
    write_policy: str = "auto"


class RunRequest(BaseModel):
    intent: Optional[str] = None
    mode: str = "auto"
    target: Optional[str] = None
    release_plan_yaml: Optional[str] = None
    release_plan_path: Optional[str] = None
    product: Optional[str] = None
    execution_id: Optional[str] = None
    resume: bool = False
    reference_paths: Optional[List[str]] = None
    write_policy: str = "auto"


class StopRequest(BaseModel):
    execution_id: str


class RollbackRequest(BaseModel):
    execution_id: str


class StatusRequest(BaseModel):
    execution_id: Optional[str] = None


class HitlDecisionBody(BaseModel):
    decision: str
    note: Optional[str] = None


class GovernanceCheckBody(BaseModel):
    gate: Literal["review", "planning", "both"] = "review"


class SuggestionPromoteBody(BaseModel):
    gate: str = "review"
    title: str = ""
    summary: str = ""
    approver: str = ""


class SuggestionReviewBody(BaseModel):
    reviewer: str = ""
    notes: str = ""


class SuggestionRejectBody(BaseModel):
    rejected_by: str = ""
    notes: str = ""


_event_handler: Optional[SSEEventHandler] = None


async def _on_event(event: Any) -> None:
    global _event_handler
    try:
        et = getattr(getattr(event, "type", None), "value", None) or str(getattr(event, "type", ""))
        if et:
            platform_state.record_sse_event_type(et)
    except Exception:
        pass
    if _event_handler:
        await _event_handler.handle_event(event)


def create_app(project_path: str = ".") -> FastAPI:
    sc = SprintCycle(project_path=project_path)
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

    @app.middleware("http")
    async def _platform_http_metrics(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        method = request.method.upper()
        t0 = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 200)
            return response
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            platform_state.record_http_request(route=path, method=method, status_code=status_code, duration_ms=elapsed_ms)
            if path not in ("/api/events/stream", "/api/events", "/api/events/legacy"):
                logger.info("dashboard_http method={} path={} status={} duration_ms={:.2f}", method, path, status_code, elapsed_ms)

    client_manager = get_client_manager()
    dashboard_workbench = DashboardWorkbenchService()

    global _event_handler
    _event_handler = SSEEventHandler(client_manager)
    _event_handler.start()

    for event_type in EventType:
        if event_type is EventType.CONFIG_CHANGED:
            continue
        event_bus.on(event_type, _on_event)

    @app.post("/api/plan")
    async def api_plan(req: PlanRequest) -> Dict[str, Any]:
        result = sc.plan(intent=req.intent, mode=req.mode, target=req.target, release_plan_yaml=req.release_plan_yaml, release_plan_path=req.release_plan_path, product=req.product, reference_paths=req.reference_paths, write_policy=req.write_policy)
        return result.to_dict()

    @app.post("/api/run")
    async def api_run(req: RunRequest) -> Dict[str, Any]:
        result = sc.run(intent=req.intent, mode=req.mode, target=req.target, release_plan_yaml=req.release_plan_yaml, release_plan_path=req.release_plan_path, product=req.product, execution_id=req.execution_id, resume=req.resume, reference_paths=req.reference_paths, write_policy=req.write_policy)
        return result.to_dict()

    @app.get("/api/governance/latest")
    async def api_governance_latest() -> Dict[str, Any]:
        return await _read_governance_reports(sc)

    @app.get("/api/governance/history")
    async def api_governance_history(limit: int = 50) -> Dict[str, Any]:
        return sc.governance_history(limit=limit)

    @app.post("/api/governance/check")
    async def api_governance_check(body: GovernanceCheckBody) -> Dict[str, Any]:
        from sprintcycle.config.runtime_config import RuntimeConfig
        from sprintcycle.governance.runner import run_governance_check_and_persist

        cfg = RuntimeConfig.from_project(sc.project_path)
        planning_report, review_report, fail = await asyncio.to_thread(run_governance_check_and_persist, sc.project_path, cfg, body.gate)
        out: Dict[str, Any] = {"should_fail_ci": fail, "gate": body.gate}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        return out

    @app.get("/api/diagnose")
    async def api_diagnose() -> Dict[str, Any]:
        result = sc.diagnose()
        return result.to_dict()

    @app.post("/api/status")
    async def api_status(req: StatusRequest) -> Dict[str, Any]:
        result = sc.status(execution_id=req.execution_id)
        payload = result.to_dict()
        if req.execution_id:
            try:
                latest = sc.status(execution_id=req.execution_id)
                payload["release_finalization"] = getattr(latest, "release_finalization", {})
            except Exception:
                payload["release_finalization"] = {}
        return payload

    @app.post("/api/rollback")
    async def api_rollback(req: RollbackRequest) -> Dict[str, Any]:
        result = sc.rollback(execution_id=req.execution_id)
        return result.to_dict()

    @app.post("/api/stop")
    async def api_stop(req: StopRequest) -> Dict[str, Any]:
        result = sc.stop(execution_id=req.execution_id)
        return result.to_dict()

    @app.get("/api/hitl/pending")
    async def api_hitl_pending(execution_id: Optional[str] = None) -> Dict[str, Any]:
        return await sc.hitl_pending(execution_id=execution_id)

    @app.post("/api/hitl/{request_id}/decision")
    async def api_hitl_decision(request_id: str, payload: HitlDecisionBody) -> Dict[str, Any]:
        return await sc.hitl_submit(request_id, payload.decision, payload.note)

    @app.get("/api/hitl/history")
    async def api_hitl_history(execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await sc.hitl_history(execution_id=execution_id, limit=limit)

    @app.get("/api/hitl/requests/{request_id}")
    async def api_hitl_request_detail(request_id: str) -> Dict[str, Any]:
        return await sc.hitl_show(request_id)

    @app.get("/api/console/overview")
    async def api_console_overview(limit: int = 20) -> Dict[str, Any]:
        return sc.console_overview(limit=limit)

    @app.get("/api/execution/{execution_id}/detail")
    async def api_execution_detail(execution_id: str, limit: int = 200) -> Dict[str, Any]:
        return sc.execution_detail(execution_id, limit=limit)

    @app.get("/api/dashboard/governance")
    async def api_dashboard_governance() -> Dict[str, Any]:
        return sc.governance_view()

    @app.get("/api/dashboard/suggestions")
    async def api_dashboard_suggestions(execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        return dashboard_workbench.suggestion_board(sc, execution_id=execution_id, limit=limit)

    @app.get("/api/dashboard/board")
    async def api_dashboard_board(execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        return await dashboard_workbench.suggestion_and_hitl_panel(sc, execution_id=execution_id, limit=limit)

    @app.get("/api/dashboard/workspace/{execution_id}")
    async def api_dashboard_workspace(execution_id: str, limit: int = 200) -> Dict[str, Any]:
        return dashboard_workbench.execution_workspace(sc, execution_id=execution_id, limit=limit)

    @app.get("/api/dashboard/platform")
    async def api_dashboard_platform() -> Dict[str, Any]:
        return dashboard_workbench.platform_workspace(sc)

    @app.get("/api/platform/overview")
    async def api_platform_overview() -> Dict[str, Any]:
        return sc.platform_overview()

    @app.get("/api/dashboard/trace")
    async def api_dashboard_trace(execution_id: str) -> Dict[str, Any]:
        return sc.observability_trace(execution_id)

    @app.post("/api/dashboard/suggestions/{suggestion_id}/review")
    async def api_dashboard_suggestion_review(suggestion_id: str, body: SuggestionReviewBody) -> Dict[str, Any]:
        return await sc.review_suggestion("", suggestion_id, reviewer=body.reviewer, notes=body.notes)

    @app.post("/api/dashboard/suggestions/{suggestion_id}/approve")
    async def api_dashboard_suggestion_approve(suggestion_id: str, body: SuggestionPromoteBody) -> Dict[str, Any]:
        return await sc.approve_suggestion("", suggestion_id, approver=body.approver, notes=body.summary)

    @app.post("/api/dashboard/suggestions/{suggestion_id}/reject")
    async def api_dashboard_suggestion_reject(suggestion_id: str, body: SuggestionRejectBody) -> Dict[str, Any]:
        return await sc.reject_suggestion("", suggestion_id, rejected_by=body.rejected_by, notes=body.notes)

    @app.post("/api/dashboard/suggestions/{suggestion_id}/promote")
    async def api_dashboard_suggestion_promote(suggestion_id: str, body: SuggestionPromoteBody) -> Dict[str, Any]:
        return await sc.promote_suggestion_to_hitl(
            suggestion_id,
            gate=body.gate,
            title=body.title,
            summary=body.summary,
            context={"approver": body.approver, "source": "dashboard"},
        )

    @app.post("/api/dashboard/suggestions/{suggestion_id}/replay")
    async def api_dashboard_suggestion_replay(suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        return await sc.attach_suggestion_replay(suggestion_id, replay)

    return app
