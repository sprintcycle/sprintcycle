"""
SprintCycle Dashboard — FastAPI 应用

REST API + SSE 实时事件流，调用 SprintCycle API。
默认 ``ExecutionEventBackend`` 为 ``SQLiteMQEventBackend``（按项目落库）；SSE 仍按各 ``EventType``
逐一 ``on`` 订阅，``emit`` 路径会 **await** 异步 handler，避免纯 MQ 同步派发丢协程。
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Literal, Optional

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

        # 清理断开的客户端
        for client_id in disconnected:
            await self.remove_client(client_id)

    def get_client_count(self) -> int:
        """获取当前客户端数量"""
        return len(self._clients)


# 全局客户端管理器
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
    """获取客户端管理器"""
    global _client_manager
    if _client_manager is None:
        _client_manager = SSEClientManager()
    return _client_manager


# ─── 全局事件处理器 ───

class SSEEventHandler:
    """SSE 事件处理器 - 将执行事件后端的事件转发到 SSE 客户端"""

    def __init__(self, client_manager: SSEClientManager):
        self._client_manager = client_manager
        self._is_running = False

    async def handle_event(self, event: Event) -> None:
        """处理事件并广播到所有 SSE 客户端"""
        if self._is_running:
            await self._client_manager.broadcast(event)

    def start(self) -> None:
        """启动处理器"""
        self._is_running = True

    def stop(self) -> None:
        """停止处理器"""
        self._is_running = False


# ─── 请求模型 ───


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
    """HTTP 触发治理门禁（与 ``sprintcycle governance check`` 对齐）。"""

    gate: Literal["review", "planning", "both"] = "review"


# ─── 全局状态 ───

_event_handler: Optional[SSEEventHandler] = None


async def _on_event(event: Any) -> None:
    """执行事件后端回调"""
    global _event_handler
    try:
        et = getattr(getattr(event, "type", None), "value", None) or str(
            getattr(event, "type", "")
        )
        if et:
            platform_state.record_sse_event_type(et)
    except Exception:
        pass
    if _event_handler:
        await _event_handler.handle_event(event)


# ─── App 工厂 ───


def create_app(project_path: str = ".") -> FastAPI:
    """创建 FastAPI 应用"""
    sc = SprintCycle(project_path=project_path)
    event_bus = get_execution_event_backend()

    app = FastAPI(title="SprintCycle Console", version="0.9.2")

    if _DASHBOARD_DEV:
        _p = DashboardPortDefaults.dev_port
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                f"http://127.0.0.1:{_p}",
                f"http://localhost:{_p}",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def _platform_http_metrics(
        request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        """管理平台：HTTP 延迟、状态码、按路由计数；结构化日志便于外接采集。"""
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
            platform_state.record_http_request(
                route=path,
                method=method,
                status_code=status_code,
                duration_ms=elapsed_ms,
            )
            if path not in ("/api/events/stream", "/api/events", "/api/events/legacy"):
                logger.info(
                    "dashboard_http method={} path={} status={} duration_ms={:.2f}",
                    method,
                    path,
                    status_code,
                    elapsed_ms,
                )

    # 初始化 SSE 客户端管理器
    client_manager = get_client_manager()

    # 初始化并启动 SSE 事件处理器
    global _event_handler
    _event_handler = SSEEventHandler(client_manager)
    _event_handler.start()

    # 注册全局事件处理器：与 EventBus 相同的一类型一 handler；后端为 SQLite 时仍适用
    # config_changed 仅由配置 API / 文件监视直接 SSE 广播，不经执行事件后端持久化
    for event_type in EventType:
        if event_type is EventType.CONFIG_CHANGED:
            continue
        event_bus.on(event_type, _on_event)

    # ─── API 路由 ───

    @app.post("/api/plan")
    async def api_plan(req: PlanRequest) -> Dict[str, Any]:
        result = sc.plan(
            intent=req.intent,
            mode=req.mode,
            target=req.target,
            release_plan_yaml=req.release_plan_yaml,
            release_plan_path=req.release_plan_path,
            product=req.product,
            reference_paths=req.reference_paths,
            write_policy=req.write_policy,
        )
        return result.to_dict()

    @app.post("/api/run")
    async def api_run(req: RunRequest) -> Dict[str, Any]:
        result = sc.run(
            intent=req.intent, mode=req.mode, target=req.target,
            release_plan_yaml=req.release_plan_yaml,
            release_plan_path=req.release_plan_path,
            product=req.product,
            execution_id=req.execution_id, resume=req.resume,
            reference_paths=req.reference_paths,
            write_policy=req.write_policy,
        )
        return result.to_dict()

    @app.get("/api/governance/latest")
    async def api_governance_latest() -> Dict[str, Any]:
        """只读返回最近一次落盘的 Planning / Review 治理报告（v4.0 观测面）。"""
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

    @app.get("/api/governance/history")
    async def api_governance_history(limit: int = 50) -> Dict[str, Any]:
        """治理报告历史快照列表（新→旧），见 ``governance_history`` 目录。"""
        from sprintcycle.config.runtime_config import RuntimeConfig
        from sprintcycle.governance.history import list_history_entries

        cfg = RuntimeConfig.from_project(sc.project_path)
        lim = min(200, max(1, int(limit)))
        entries = list_history_entries(sc.project_path, cfg, limit=lim)
        return {"entries": entries}

    @app.post("/api/governance/check")
    async def api_governance_check(body: GovernanceCheckBody) -> Dict[str, Any]:
        """执行 Planning/Review 门禁并落盘（与 CLI / validate 对齐）。"""
        from sprintcycle.config.runtime_config import RuntimeConfig
        from sprintcycle.governance.runner import run_governance_check_and_persist

        cfg = RuntimeConfig.from_project(sc.project_path)
        # 门禁内部使用 ``asyncio.run``；在 ASGI 事件循环中须放到线程执行，避免嵌套 loop。
        planning_report, review_report, fail = await asyncio.to_thread(
            run_governance_check_and_persist,
            sc.project_path,
            cfg,
            body.gate,
        )
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

    @app.get("/api/execution/{execution_id}/events")
    async def api_execution_events(execution_id: str, limit: int = 200) -> Dict[str, Any]:
        return sc.execution_events(execution_id, limit=limit)

    config_center.attach_config_routes(app, sc, client_manager)

    @app.on_event("startup")
    async def _config_center_startup() -> None:
        config_center.set_reload_loop(asyncio.get_running_loop())
        stop = config_center.start_config_file_watcher(sc.project_path, sc, client_manager)
        app.state._config_watcher_stop = stop

    @app.on_event("shutdown")
    async def _config_center_shutdown() -> None:
        stop = getattr(app.state, "_config_watcher_stop", None)
        if callable(stop):
            stop()

    # ─── SSE 事件流 ───

    @app.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        """
        SSE 实时事件流端点

        推送 Sprint 执行相关的实时事件：
        - execution_start: 执行开始
        - sprint_start: Sprint 开始
        - sprint_complete: Sprint 完成
        - sprint_failed: Sprint 失败
        - task_start: 任务开始
        - task_complete: 任务完成
        - task_failed: 任务失败
        - governance_task_check: 任务级治理 task_after 检查
        - governance_gate: Planning/Review 门摘要（含 compose:* 规则）
        - execution_complete: 执行完成
        - execution_failed: 执行失败
        - hitl_request_open / hitl_request_resolved: 人机卡点待决策 / 已决策
        - config_changed: 运行时配置已更新（API 保存、手动 reload 或文件热重载）

        最近一次落盘治理报告（不含 SSE）：``GET /api/governance/latest``（见 docs/GOVERNANCE_HEAVY_CHECKS.md）。
        """
        client = await client_manager.create_client()
        client_id = client.client_id

        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                # 发送连接成功消息
                yield f"event: connected\ndata: {json.dumps({'client_id': client_id, 'message': 'SSE connected'})}\n\n"

                # 持续发送事件直到客户端断开
                while True:
                    try:
                        # 等待消息，15秒超时以发送心跳
                        message = await asyncio.wait_for(
                            client.queue.get(),
                            timeout=15.0
                        )
                        yield message
                    except asyncio.TimeoutError:
                        # 发送心跳保活
                        yield f"event: heartbeat\ndata: {json.dumps({'type': 'heartbeat', 'client_id': client_id})}\n\n"
                    except asyncio.CancelledError:
                        break
            finally:
                await client_manager.remove_client(client_id)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    @app.get("/api/events")
    @app.get("/api/events/legacy")
    async def api_events_legacy() -> StreamingResponse:
        """向后兼容的 SSE 端点 - 重定向到 /api/events/stream"""
        return StreamingResponse(
            _legacy_heartbeat_stream(),
            media_type="text/event-stream"
        )

    async def _legacy_heartbeat_stream() -> AsyncGenerator[str, None]:
        """传统的心跳流（保持向后兼容）"""
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(15)

    @app.get("/api/clients")
    async def api_clients() -> Dict[str, Any]:
        """获取当前 SSE 客户端数量"""
        return {
            "client_count": client_manager.get_client_count(),
        }

    @app.get("/api/platform/summary")
    async def api_platform_summary() -> Dict[str, Any]:
        """管理平台总览：HTTP/SSE 指标、执行阶段聚合、最近审计（进程内）。"""
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
        snap["hitl"] = {
            "open_requests": len(pend) if isinstance(pend, list) else 0,
        }
        return snap

    _mount_dashboard_frontend(app)
    return app


def _mount_dashboard_frontend(app: FastAPI) -> None:
    """挂载 Vue 构建产物；无 index.html 时返回降级说明页。"""
    index_html = STATIC_DIR / "index.html"

    if not index_html.is_file():

        @app.get("/")
        async def _dashboard_missing_static() -> HTMLResponse:
            return HTMLResponse(_NO_STATIC_BODY)

        return

    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="dashboard_assets",
        )

    static_root = STATIC_DIR.resolve()

    @app.get("/")
    async def _spa_index() -> FileResponse:
        return FileResponse(str(index_html))

    @app.get("/{full_path:path}")
    async def _spa_or_file(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (STATIC_DIR / full_path).resolve()
        try:
            candidate.relative_to(static_root)
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found") from None
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(index_html))


__all__ = ["create_app"]
