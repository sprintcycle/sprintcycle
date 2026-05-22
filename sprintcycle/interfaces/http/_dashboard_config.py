"""Dashboard 路由 - 配置相关。"""

from typing import Any, Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


def create_config_router(config_store: Any, config_loader: Any) -> APIRouter:
    """创建配置相关路由。"""
    router = APIRouter()

    async def get_config() -> Dict[str, Any]:
        return _load_config(config_store)

    async def put_config(body: ConfigUpdateRequest) -> Dict[str, Any]:
        data = _load_config(config_store)
        data.update(body.updates)
        _save_config(config_store, data)
        return {"status": "ok", "updated": body.updates}

    async def get_config_schema() -> Dict[str, Any]:
        schema_path = config_store / ".sprintcycle" / "config.schema.json"
        if schema_path.exists():
            import json
            return json.loads(schema_path.read_text())
        return {"type": "object", "properties": {}}

    async def get_config_history() -> Dict[str, Any]:
        history_path = config_store / ".sprintcycle" / "config.history.json"
        if history_path.exists():
            import json
            return {"history": json.loads(history_path.read_text())}
        return {"history": []}

    async def reload_config(_body: ReloadRequest) -> Dict[str, Any]:
        config_loader.reload()
        return {"status": "reloaded"}

    async def import_config(body: ConfigImportRequest) -> Dict[str, Any]:
        _save_config(config_store, body.config)
        return {"status": "imported"}

    # 注册路由
    router.add_api_route("/config", get_config, methods=["GET"])
    router.add_api_route("/config", put_config, methods=["PUT"])
    router.add_api_route("/config/schema", get_config_schema, methods=["GET"])
    router.add_api_route("/config/history", get_config_history, methods=["GET"])
    router.add_api_route("/config/reload", reload_config, methods=["POST"])
    router.add_api_route("/config/import", import_config, methods=["POST"])

    return router


def _load_config(config_store: Any) -> Dict[str, Any]:
    """加载配置。"""
    import yaml
    config_path = config_store / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(config_store: Any, data: Dict[str, Any]) -> None:
    """保存配置。"""
    import yaml
    config_path = config_store / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(data, f)
