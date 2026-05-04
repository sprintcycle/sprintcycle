"""
基于 SQLite + SQLAlchemy 的执行状态存储（与 StateStore 方法签名对齐）。
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ..persistence.models import ExecutionRow
from ..persistence.session import create_engine_for_path, init_db
from .sprint_types import ExecutionStatus
from .state_store import ExecutionState

logger = logging.getLogger(__name__)


class SqliteExecutionStore:
    """与 ``StateStore`` 相同的对外 API，便于 ``get_state_store`` 切换后端。"""

    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser().resolve())
        self.engine = create_engine_for_path(self.db_path)
        init_db(self.engine)
        self._Session = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    def _session(self) -> Session:
        return self._Session()

    @staticmethod
    def _to_state(row: ExecutionRow) -> ExecutionState:
        return ExecutionState(
            execution_id=row.execution_id,
            prd_name=row.prd_name,
            mode=row.mode,
            status=ExecutionStatus(row.status),
            current_sprint=row.current_sprint,
            total_sprints=row.total_sprints,
            completed_tasks=row.completed_tasks,
            total_tasks=row.total_tasks,
            created_at=row.created_at,
            updated_at=row.updated_at,
            error=row.error,
            checkpoint=row.checkpoint,
            metadata=dict(row.execution_meta or {}),
        )

    def save(self, state: ExecutionState) -> None:
        state.updated_at = datetime.now().isoformat()
        payload = {
            "execution_id": state.execution_id,
            "prd_name": state.prd_name,
            "mode": state.mode,
            "status": state.status.value if hasattr(state.status, "value") else str(state.status),
            "current_sprint": state.current_sprint,
            "total_sprints": state.total_sprints,
            "completed_tasks": state.completed_tasks,
            "total_tasks": state.total_tasks,
            "created_at": state.created_at or datetime.now().isoformat(),
            "updated_at": state.updated_at,
            "error": state.error,
            "checkpoint": state.checkpoint,
            "execution_meta": dict(state.metadata or {}),
        }
        s = self._session()
        try:
            existing = s.scalars(
                select(ExecutionRow).where(ExecutionRow.execution_id == state.execution_id)
            ).first()
            if existing:
                for k, v in payload.items():
                    if k != "execution_id":
                        setattr(existing, k, v)
            else:
                s.add(ExecutionRow(**payload))
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def load(self, execution_id: str) -> Optional[ExecutionState]:
        s = self._session()
        try:
            row = s.scalars(select(ExecutionRow).where(ExecutionRow.execution_id == execution_id)).first()
            if row is None:
                return None
            return self._to_state(row)
        finally:
            s.close()

    def delete(self, execution_id: str) -> bool:
        s = self._session()
        try:
            r = s.execute(delete(ExecutionRow).where(ExecutionRow.execution_id == execution_id))
            n = r.rowcount or 0
            s.commit()
            return n > 0
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def list_executions(
        self, status: Optional[ExecutionStatus] = None, limit: int = 50
    ) -> List[ExecutionState]:
        s = self._session()
        try:
            q = select(ExecutionRow).order_by(ExecutionRow.updated_at.desc()).limit(limit)
            if status is not None:
                q = q.where(ExecutionRow.status == status.value)
            rows = list(s.scalars(q).all())
            return [self._to_state(r) for r in rows]
        finally:
            s.close()

    def create_checkpoint(
        self,
        execution_id: str,
        sprint_idx: int,
        sprint_name: str,
        task_results: List[Dict[str, Any]],
        prd_yaml: Optional[str] = None,
    ) -> bool:
        state = self.load(execution_id)
        if state is None:
            logger.warning("Cannot create checkpoint: state %s not found", execution_id)
            return False
        state.checkpoint = {
            "sprint_idx": sprint_idx,
            "sprint_name": sprint_name,
            "task_results": task_results,
            "timestamp": datetime.now().isoformat(),
            "prd_yaml": prd_yaml,
        }
        self.save(state)
        return True

    def can_resume(self, execution_id: str) -> bool:
        state = self.load(execution_id)
        return (
            state is not None
            and state.status
            in (ExecutionStatus.PAUSED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED)
            and state.checkpoint is not None
        )

    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        state = self.load(execution_id)
        if state and state.checkpoint:
            return {
                "current_sprint": state.checkpoint.get("sprint_idx", 0),
                "sprint_name": state.checkpoint.get("sprint_name", ""),
                "task_results": state.checkpoint.get("task_results", []),
                "prd_yaml": state.checkpoint.get("prd_yaml"),
            }
        return None

    def update_status(self, execution_id: str, status: ExecutionStatus, error: Optional[str] = None) -> bool:
        state = self.load(execution_id)
        if state is None:
            return False
        state.status = status
        if error:
            state.error = error
        self.save(state)
        return True

    def increment_progress(
        self, execution_id: str, completed_tasks: int = 1, completed_sprints: int = 0
    ) -> bool:
        state = self.load(execution_id)
        if state is None:
            return False
        state.completed_tasks += completed_tasks
        state.current_sprint += completed_sprints
        self.save(state)
        return True
