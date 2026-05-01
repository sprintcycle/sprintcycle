"""
SprintCycle Dashboard — FastAPI 应用

REST API + SSE 实时事件流，调用 SprintCycle API。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from sprintcycle.api import SprintCycle
from sprintcycle.execution.events import EventBus, EventType

logger = logging.getLogger(__name__)


# ─── 请求模型 ───


class PlanRequest(BaseModel):
    intent: str
    mode: str = "auto"
    target: Optional[str] = None
    prd_path: Optional[str] = None


class RunRequest(BaseModel):
    intent: Optional[str] = None
    mode: str = "auto"
    target: Optional[str] = None
    prd_yaml: Optional[str] = None
    prd_path: Optional[str] = None
    execution_id: Optional[str] = None
    resume: bool = False


class StopRequest(BaseModel):
    execution_id: str


class RollbackRequest(BaseModel):
    execution_id: str


class StatusRequest(BaseModel):
    execution_id: Optional[str] = None


# ─── App 工厂 ───


def create_app(project_path: str = ".") -> FastAPI:
    """创建 FastAPI 应用"""
    sc = SprintCycle(project_path=project_path)
    event_bus = EventBus()

    app = FastAPI(title="SprintCycle Dashboard", version="0.9.1")

    # ─── API 路由 ───

    @app.post("/api/plan")
    async def api_plan(req: PlanRequest) -> Dict[str, Any]:
        result = sc.plan(intent=req.intent, mode=req.mode, target=req.target, prd_path=req.prd_path)
        return result.to_dict()

    @app.post("/api/run")
    async def api_run(req: RunRequest) -> Dict[str, Any]:
        result = sc.run(
            intent=req.intent, mode=req.mode, target=req.target,
            prd_yaml=req.prd_yaml, prd_path=req.prd_path,
            execution_id=req.execution_id, resume=req.resume,
        )
        return result.to_dict()

    @app.get("/api/diagnose")
    async def api_diagnose() -> Dict[str, Any]:
        result = sc.diagnose()
        return result.to_dict()

    @app.post("/api/status")
    async def api_status(req: StatusRequest) -> Dict[str, Any]:
        result = sc.status(execution_id=req.execution_id)
        return result.to_dict()

    @app.post("/api/rollback")
    async def api_rollback(req: RollbackRequest) -> Dict[str, Any]:
        result = sc.rollback(execution_id=req.execution_id)
        return result.to_dict()

    @app.post("/api/stop")
    async def api_stop(req: StopRequest) -> Dict[str, Any]:
        result = sc.stop(execution_id=req.execution_id)
        return result.to_dict()

    # ─── SSE 事件流 ───

    @app.get("/api/events")
    async def api_events() -> StreamingResponse:
        async def event_stream():
            # 发送心跳，保持连接
            while True:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                await asyncio.sleep(15)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ─── Dashboard 首页 ───

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _render_dashboard_html()

    return app


def _render_dashboard_html() -> str:
    """渲染 Dashboard 首页 HTML"""
    return """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SprintCycle Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
.container { max-width: 960px; margin: 0 auto; padding: 24px; }
h1 { font-size: 24px; margin-bottom: 20px; color: #38bdf8; }
.input-bar { display: flex; gap: 8px; margin-bottom: 24px; }
.input-bar input { flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; font-size: 14px; }
.input-bar input:focus { outline: none; border-color: #38bdf8; }
.btn { padding: 12px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-run { background: #22c55e; color: #fff; }
.btn-plan { background: #3b82f6; color: #fff; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.section { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.section h2 { font-size: 16px; color: #94a3b8; margin-bottom: 12px; }
.output { white-space: pre-wrap; font-family: 'Fira Code', monospace; font-size: 13px; line-height: 1.6; color: #cbd5e1; }
.output .ok { color: #22c55e; }
.output .err { color: #ef4444; }
.actions { display: flex; gap: 8px; margin-top: 12px; }
.btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #94a3b8; cursor: pointer; }
.btn-sm:hover { border-color: #38bdf8; color: #38bdf8; }
</style>
</head>
<body>
<div class="container">
  <h1>🚀 SprintCycle Dashboard</h1>
  <div class="input-bar">
    <input id="intent" placeholder="描述你的意图..." autofocus />
    <button class="btn btn-plan" onclick="doPlan()">📋 Plan</button>
    <button class="btn btn-run" onclick="doRun()">▶ Run</button>
  </div>
  <div class="section">
    <h2>输出</h2>
    <div class="output" id="output">等待输入...</div>
    <div class="actions">
      <button class="btn-sm" onclick="doDiagnose()">🏥 诊断</button>
      <button class="btn-sm" onclick="doStatus()">📜 历史</button>
    </div>
  </div>
</div>
<script>
const $ = id => document.getElementById(id);
async function api(path, body) {
  const r = await fetch('/api/' + path, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  });
  return r.json();
}
function show(data) {
  $('output').textContent = JSON.stringify(data, null, 2);
}
async function doPlan() {
  const intent = $('intent').value; if (!intent) return;
  show({status: 'planning...'});
  const r = await api('plan', {intent});
  show(r);
}
async function doRun() {
  const intent = $('intent').value; if (!intent) return;
  show({status: 'running...'});
  const r = await api('run', {intent});
  show(r);
}
async function doDiagnose() {
  show({status: 'diagnosing...'});
  const r = await fetch('/api/diagnose').then(r => r.json());
  show(r);
}
async function doStatus() {
  show({status: 'loading...'});
  const r = await api('status', {});
  show(r);
}
$('intent').addEventListener('keydown', e => { if (e.key === 'Enter') doRun(); });
</script>
</body>
</html>"""


__all__ = ["create_app"]
