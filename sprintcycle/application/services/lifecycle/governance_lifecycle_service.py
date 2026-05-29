"""Governance lifecycle management service.

**职责边界**：
- 治理生命周期管理
- 治理摘要、待办、历史
- 治理健康状态

**DDD Architecture**：
- 应用层服务，只做编排
- 依赖通过构造函数注入
- 保持接口与原 LifecycleDeliveryService 兼容
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from sprintcycle.application.services.governance.governance_orchestration_service import GovernanceOrchestrationService


@dataclass
class GovernanceLifecycleService:
    project_path: str
    governance_orchestration: GovernanceOrchestrationService

    async def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        summary = await self.governance_orchestration.summary(execution_id=execution_id, limit=50)
        pending = await self.governance_orchestration.pending(execution_id=execution_id)
        history = await self.governance_orchestration.history(execution_id=execution_id, limit=50)
        summary_data = summary.get("data", {}) if isinstance(summary, dict) else {}
        pending_data = pending.get("data", []) if isinstance(pending, dict) else []
        history_data = history.get("data", []) if isinstance(history, dict) else []
        closure_score = 100.0 if summary.get("success", False) and not pending_data else 0.0
        return {
            "success": True,
            "data": {
                "summary": summary_data,
                "pending": pending_data,
                "history": history_data,
                "lifecycle": {
                    "stage": "governing",
                    "status": "success" if summary.get("success", False) else "failed",
                    "execution_id": execution_id,
                    "pending_count": len(pending_data),
                    "history_count": len(history_data),
                    "summary_count": int(summary_data.get("history_count", 0) if isinstance(summary_data, dict) else 0),
                    "closure_score": closure_score,
                },
                "health": {"closure_score": closure_score, "is_healthy": closure_score > 0},
            },
        }


__all__ = ["GovernanceLifecycleService"]
