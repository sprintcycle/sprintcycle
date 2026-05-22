"""Internal HTTP routes for Dashboard control surfaces."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.application.sprint_orchestrator import SprintOrchestrator
from sprintcycle.governance.runner import run_governance_check_and_persist
from sprintcycle.infrastructure.integrations.audit import record_audit_event
from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.config.rate_limit import check_rate_limit


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


class _InternalRouteDeps:
    def __init__(self, services: HTTPServices, project_path: str):
        self.services = services
        self.project_path = project_path
        self.config_history: List[Dict[str, Any]] = []
        self.runtime_yaml = Path(project_path) / "sprintcycle.runtime.yaml"
        self.orchestrator = SprintOrchestrator(project_path=project_path, config=RuntimeConfig.from_project(project_path))

    def _load_config(self) -> Dict[str, Any]:
        try:
            cfg = RuntimeConfig.from_project(self.project_path)
            raw = cfg.to_dict()
            if isinstance(raw, dict) and "PROJECT" in raw and isinstance(raw["PROJECT"], dict):
                flat = {k.lower(): v for k, v in raw["PROJECT"].items()}
                for k, v in raw.items():
                    if k != "PROJECT":
                        flat[k.lower()] = v
                return flat
            if isinstance(raw, dict):
                return {k.lower(): v for k, v in raw.items()}
            return raw
        except Exception:
            return {}

    def _save_config(self, data: Dict[str, Any]) -> None:
        try:
            self.runtime_yaml.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if self.runtime_yaml.exists():
                import yaml
                existing = yaml.safe_load(self.runtime_yaml.read_text()) or {}
            existing.update(data)
            import yaml
            self.runtime_yaml.write_text(yaml.dump(existing, default_flow_style=False), encoding="utf-8")
        except Exception:
            pass


def build_internal_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter()
    deps = _InternalRouteDeps(services, project_path)

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=deps.project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/governance/latest")
    async def governance_latest(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/latest", context=ctx)
        # 读取治理报告
        cfg = RuntimeConfig.from_project(deps.project_path)
        root = Path(deps.project_path).expanduser().resolve()
        rel = (cfg.governance_report_dir or ".sprintcycle").strip() or ".sprintcycle"
        out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        last = out_dir / "governance_last.json"
        planning = out_dir / "governance_planning_last.json"
        if not last.is_file() and not planning.is_file():
            raise FileNotFoundError("未找到治理报告")
        payload: dict = {}
        if planning.is_file():
            payload["planning"] = planning.read_text(encoding="utf-8")
        if last.is_file():
            payload["review"] = last.read_text(encoding="utf-8")
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_reports",
            resource="/api/governance/latest",
            outcome="success",
        )
        return payload

    @router.get("/api/governance/history")
    async def governance_history(request: Request, limit: int = 50) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/history", context=ctx)
        result = deps.services.governance_history(limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_history",
            resource="/api/governance/history",
            outcome="success",
        )
        return result

    @router.post("/api/governance/check")
    async def governance_check(request: Request, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/check", context=ctx)
        cfg = RuntimeConfig.from_project(deps.project_path)
        planning_report, review_report, fail = await asyncio.to_thread(
            run_governance_check_and_persist,
            deps.project_path,
            cfg,
            body.get("gate", "review"),
        )
        out = {"should_fail_ci": fail, "gate": body.get("gate", "review")}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_check",
            resource="/api/governance/check",
            outcome="success",
        )
        return out

    @router.get("/api/dashboard/governance")
    async def dashboard_governance(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/governance", context=ctx)
        result = deps.services.governance_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_view",
            resource="/api/dashboard/governance",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/platform")
    async def dashboard_platform(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/platform", context=ctx)
        result = deps.services.dashboard_platform_workspace()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.dashboard_platform_workspace",
            resource="/api/dashboard/platform",
            outcome="success",
        )
        return result

    @router.get("/api/platform/overview")
    async def platform_overview(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/platform/overview", context=ctx)
        result = deps.services.platform_overview()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.platform_overview",
            resource="/api/platform/overview",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/trace")
    async def dashboard_trace(request: Request, execution_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/trace", context=ctx)
        result = deps.services.observability_trace(execution_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.observability_trace",
            resource="/api/dashboard/trace",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/fitness")
    async def dashboard_fitness(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/fitness", context=ctx)
        result = deps.services.fitness_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.fitness_view",
            resource="/api/dashboard/fitness",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/deploy")
    async def dashboard_deploy(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/deploy", context=ctx)
        result = deps.services.deploy_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.deploy_view",
            resource="/api/dashboard/deploy",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/lifecycle-contract")
    async def dashboard_lifecycle_contract(request: Request, execution_id: str, limit: int = 200) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/lifecycle-contract", context=ctx)
        result = deps.services.lifecycle_contract(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract",
            resource="/api/dashboard/lifecycle-contract",
            outcome="success",
        )
        return result

    @router.post("/api/dashboard/lifecycle-contract/{execution_id}/review")
    async def dashboard_lifecycle_contract_review(request: Request, execution_id: str, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/lifecycle-contract/{execution_id}/review", context=ctx)
        contract = deps.services.lifecycle_contract(execution_id)
        payload = dict(body or {})
        payload.setdefault("contract", contract.get("data", {}))
        result = deps.services.evaluate_sprint_contract(payload)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract_review",
            resource="/api/dashboard/lifecycle-contract/{execution_id}/review",
            outcome="success",
        )
        return result

    @router.get("/api/console/overview")
    async def console_overview(request: Request, limit: int = 20) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/console/overview", context=ctx)
        result = deps.services.console_overview(limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.console_overview",
            resource="/api/console/overview",
            outcome="success",
        )
        return result

    @router.get("/api/execution/{execution_id}/detail")
    async def execution_detail(request: Request, execution_id: str, limit: int = 200) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/{execution_id}/detail", context=ctx)
        result = deps.services.execution_detail(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_detail",
            resource="/api/execution/{execution_id}/detail",
            outcome="success",
        )
        return result

    # ── Config endpoints (merged from dashboard_server.py) ──────────────────

    @router.get("/api/config")
    async def get_config(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config", context=ctx)
        result = {"success": True, "data": deps._load_config()}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config",
            resource="/api/config",
            outcome="success",
        )
        return result

    @router.put("/api/config")
    async def put_config(request: Request, body: ConfigUpdateRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config", context=ctx)
        cfg = deps._load_config()
        cfg.update(body.updates)
        deps._save_config(cfg)
        deps.config_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "api_put",
                "updates": body.updates,
            }
        )
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.put_config",
            resource="/api/config",
            outcome="success",
        )
        return {"success": True, "data": cfg}

    @router.get("/api/config/schema")
    async def get_config_schema(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/schema", context=ctx)
        result = {
            "success": True,
            "data": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "quality_level": {"type": "string"},
                    "parallel_tasks": {"type": "integer"},
                    "max_sprints": {"type": "integer"},
                },
            },
        }
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config_schema",
            resource="/api/config/schema",
            outcome="success",
        )
        return result

    @router.get("/api/config/history")
    async def get_config_history(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/history", context=ctx)
        result = {"success": True, "data": list(deps.config_history)}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config_history",
            resource="/api/config/history",
            outcome="success",
        )
        return result

    @router.post("/api/config/reload")
    async def reload_config(request: Request, _body: ReloadRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/reload", context=ctx)
        result = {"success": True, "data": deps._load_config()}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.reload_config",
            resource="/api/config/reload",
            outcome="success",
        )
        return result

    @router.post("/api/config/import")
    async def import_config(request: Request, body: ConfigImportRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/import", context=ctx)
        cfg = deps._load_config()
        cfg.update(body.config)
        deps._save_config(cfg)
        deps.config_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "api_import",
                "updates": body.config,
            }
        )
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.import_config",
            resource="/api/config/import",
            outcome="success",
        )
        return {"success": True, "data": cfg}

    # ── Dashboard home (merged from dashboard_server.py) ────────────────────

    @router.get("/")
    async def dashboard_home(request: Request) -> Response:
        from fastapi.responses import HTMLResponse

        html = """<!DOCTYPE html>
<html>
<head><title>SprintCycle Dashboard</title></head>
<body><h1>SprintCycle Dashboard</h1></body>
</html>"""
        return HTMLResponse(content=html, media_type="text/html")

    # ── Additional endpoints (merged from dashboard_server.py) ───────────────

    @router.get("/api/diagnose")
    async def api_diagnose(request: Request) -> Any:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/diagnose", context=ctx)
        result = deps.services.diagnose()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.diagnose",
            resource="/api/diagnose",
            outcome="success",
        )
        return result

    @router.get("/api/clients")
    async def api_clients(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/clients", context=ctx)
        try:
            from sprintcycle.infrastructure.observability.hooks import get_client_manager
            count = get_client_manager().get_client_count()
        except Exception:
            count = 0
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.clients",
            resource="/api/clients",
            outcome="success",
        )
        return {"success": True, "client_count": count}

    @router.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        async def event_generator():
            while True:
                yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
                await asyncio.sleep(15)
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/api/events")
    async def api_events_legacy(request: Request) -> Dict[str, Any]:
        return {"success": True, "events": []}

    @router.get("/api/events/legacy")
    async def api_events_legacy_path(request: Request) -> Dict[str, Any]:
        return {"success": True, "events": []}

    return router
