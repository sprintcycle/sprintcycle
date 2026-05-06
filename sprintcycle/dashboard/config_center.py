"""
Dashboard 配置中心：REST 读写、sprintcycle.runtime.yaml 持久化、SSE 广播、可选文件监视。

远程 Redis/Etcd 等由 Dynaconf 官方 loader 扩展，不在此模块重复抽象策略层。
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

import yaml
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel, ValidationError

from sprintcycle.config.dynaconf_app import RUNTIME_YAML_NAME
from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.execution.events import Event, EventType


class ConfigUpdatePayload(BaseModel):
    updates: Dict[str, Any]


class ConfigImportPayload(BaseModel):
    config: Dict[str, Any]


_CONFIG_HISTORY: Deque[Dict[str, Any]] = deque(maxlen=50)
_reload_loop: Optional[asyncio.AbstractEventLoop] = None
_debounce_task: Optional[asyncio.Task[None]] = None


def set_reload_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _reload_loop
    _reload_loop = loop


def runtime_yaml_path(project_path: str) -> Path:
    return Path(project_path).resolve() / RUNTIME_YAML_NAME


def mask_secrets(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)
    if out.get("api_key"):
        out["api_key"] = "***"
    return out


def _record_history(source: str, keys: List[str], detail: str = "") -> None:
    _CONFIG_HISTORY.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "keys": keys,
            "detail": detail,
        }
    )


def merge_updates(project_path: str, updates: Dict[str, Any]) -> RuntimeConfig:
    allowed = set(RuntimeConfig.model_fields)
    bad = [k for k in updates if k not in allowed]
    if bad:
        raise HTTPException(status_code=400, detail=f"Unknown config keys: {bad[:20]}")
    current = RuntimeConfig.from_project(project_path).model_dump()
    current.update(updates)
    try:
        return RuntimeConfig.model_validate(current)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors()) from e


def persist_runtime_config(project_path: str, cfg: RuntimeConfig) -> None:
    path = runtime_yaml_path(project_path)
    payload = cfg.model_dump(mode="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


async def broadcast_config_changed(client_manager: Any, source: str) -> None:
    ev = Event(
        type=EventType.CONFIG_CHANGED,
        data={
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    await client_manager.broadcast(ev)


def _schedule_hot_reload(sc: Any, client_manager: Any) -> None:
    global _debounce_task
    loop = _reload_loop
    if loop is None:
        return

    async def _run() -> None:
        await asyncio.sleep(0.45)
        try:
            sc.reload_runtime_config()
            _record_history("file_watch", [], detail="toml or runtime yaml")
            await broadcast_config_changed(client_manager, "file_watch")
        except Exception as e:
            logger.warning("config hot reload failed: {}", e)

    def _kick() -> None:
        global _debounce_task
        if _debounce_task and not _debounce_task.done():
            _debounce_task.cancel()
        _debounce_task = loop.create_task(_run())

    try:
        loop.call_soon_threadsafe(_kick)
    except RuntimeError:
        logger.warning("could not schedule config hot reload on loop")


def attach_config_routes(app: Any, sc: Any, client_manager: Any) -> None:
    project_path = sc.project_path

    @app.get("/api/config")
    async def api_config_get() -> Dict[str, Any]:
        cfg = RuntimeConfig.from_project(project_path)
        return {"success": True, "data": mask_secrets(cfg.model_dump(mode="json"))}

    @app.get("/api/config/schema")
    async def api_config_schema() -> Dict[str, Any]:
        return {"success": True, "data": RuntimeConfig.model_json_schema()}

    @app.get("/api/config/history")
    async def api_config_history() -> Dict[str, Any]:
        return {"success": True, "data": list(_CONFIG_HISTORY)}

    @app.put("/api/config")
    async def api_config_put(payload: ConfigUpdatePayload) -> Dict[str, Any]:
        if not payload.updates:
            raise HTTPException(status_code=400, detail="updates must be non-empty")
        cfg = merge_updates(project_path, payload.updates)
        persist_runtime_config(project_path, cfg)
        sc.reload_runtime_config()
        _record_history("api_put", sorted(payload.updates.keys()))
        await broadcast_config_changed(client_manager, "api_put")
        return {"success": True, "data": mask_secrets(cfg.model_dump(mode="json"))}

    @app.post("/api/config/import")
    async def api_config_import(payload: ConfigImportPayload) -> Dict[str, Any]:
        if not payload.config:
            raise HTTPException(status_code=400, detail="config must be non-empty")
        cfg = merge_updates(project_path, payload.config)
        persist_runtime_config(project_path, cfg)
        sc.reload_runtime_config()
        _record_history("import", sorted(payload.config.keys()))
        await broadcast_config_changed(client_manager, "import")
        return {"success": True, "data": mask_secrets(cfg.model_dump(mode="json"))}

    @app.post("/api/config/reload")
    async def api_config_reload() -> Dict[str, Any]:
        sc.reload_runtime_config()
        cfg = RuntimeConfig.from_project(project_path)
        _record_history("manual_reload", [])
        await broadcast_config_changed(client_manager, "manual_reload")
        return {"success": True, "data": mask_secrets(cfg.model_dump(mode="json"))}


def start_config_file_watcher(project_path: str, sc: Any, client_manager: Any) -> Optional[Callable[[], None]]:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers.polling import PollingObserver
    except ImportError:
        logger.info("watchdog not installed; config file hot-reload disabled")
        return None

    root = Path(project_path).resolve()

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event: Any) -> None:
            if getattr(event, "is_directory", False):
                return
            name = Path(str(event.src_path)).name
            if name not in ("sprintcycle.toml", RUNTIME_YAML_NAME):
                return
            _schedule_hot_reload(sc, client_manager)

        def on_created(self, event: Any) -> None:
            self.on_modified(event)

    # PollingObserver：避免 macOS FSEvents 在部分环境（沙箱/子进程）下 SystemError
    observer = PollingObserver(timeout=1.5)
    observer.schedule(_Handler(), str(root), recursive=False)
    observer.start()
    logger.info("config file watcher started on {}", root)

    def stop() -> None:
        observer.stop()
        observer.join(timeout=5.0)

    return stop
