"""Execution context for a single task run."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class ExecutionContext:
    run_id: str
    task_id: str
    project_path: str
    suggestion_id: str = ""
    evolution_id: str = ""
    stage: str = "created"
    step: str = ""
    status: str = "created"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None

    @classmethod
    def create(cls, task_id: str, project_path: str, **kwargs: Any) -> "ExecutionContext":
        run_id = str(kwargs.get("run_id") or task_id or uuid4())
        return cls(
            run_id=run_id,
            task_id=task_id,
            project_path=project_path,
            suggestion_id=str(kwargs.get("suggestion_id") or ""),
            evolution_id=str(kwargs.get("evolution_id") or ""),
            stage=str(kwargs.get("stage") or "created"),
            step=str(kwargs.get("step") or ""),
            status=str(kwargs.get("status") or "created"),
            metadata=dict(kwargs.get("metadata") or {}),
        )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "project_path": self.project_path,
            "suggestion_id": self.suggestion_id,
            "evolution_id": self.evolution_id,
            "stage": self.stage,
            "step": self.step,
            "status": self.status,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
