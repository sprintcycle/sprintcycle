"""Runtime lifecycle management service.

**职责边界**：
- 运行时生命周期管理
- 运行时注册查询
- 运行时健康状态

**DDD Architecture**：
- 应用层服务，只做编排
- 依赖通过构造函数注入
- 保持接口与原 LifecycleDeliveryService 兼容
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from sprintcycle.domain.ports.registry import RuntimeRegistryProtocol


@dataclass
class RuntimeLifecycleService:
    project_path: str
    runtime_registry: RuntimeRegistryProtocol
    runtime_latest: Callable[[], Dict[str, Any]]

    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        latest = self.runtime_latest()
        data = latest.get("data", {}) if isinstance(latest, dict) else {}
        if runtime_id:
            payload = self.runtime_registry.get(runtime_id)
            data = payload if isinstance(payload, dict) else {"runtime_id": runtime_id, "success": bool(payload)}
        has_runtime = bool(data)
        closure_score = 100.0 if has_runtime else 0.0
        lifecycle = {
            "stage": "runtime_linked" if data else "delivering",
            "status": str(data.get("status") or "unknown") if isinstance(data, dict) else "unknown",
            "runtime_id": runtime_id or data.get("runtime_id") or data.get("id") or "",
            "has_runtime": has_runtime,
            "closure_score": closure_score,
        }
        return {
            "success": True,
            "data": {
                "runtime": data,
                "lifecycle": lifecycle,
                "health": {"closure_score": closure_score, "is_healthy": has_runtime},
            },
        }


__all__ = ["RuntimeLifecycleService"]
