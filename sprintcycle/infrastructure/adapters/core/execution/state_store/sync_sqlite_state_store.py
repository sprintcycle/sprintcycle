"""同步版本的 SqliteExecutionStore（用于 CLI/脚本场景）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from sprintcycle.domain.generic.models.release_plan.payload_keys import checkpoint_plan_yaml
from sprintcycle.domain.generic.interfaces import ExecutionStatus
from sprintcycle.infrastructure.shared.persistence.base import SyncSqliteStore
from sprintcycle.infrastructure.shared.persistence.models import Base, ExecutionRow
from sprintcycle.domain.core.lifecycle import validate_transition
from sprintcycle.infrastructure.adapters.core.execution.state_store.state_store import ExecutionState


class SyncSqliteExecutionStore(SyncSqliteStore):
    """同步版本的执行状态存储（继承 SyncSqliteStore）。

    用于 CLI 命令、脚本等同步场景。
    """

    def __init__(self, db_path: str) -> None:
        super().__init__(db_path)
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def _define_schema(self, conn: AsyncConnection) -> None:
        conn.run_sync(Base.metadata.create_all)

    def _ensure_session(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            engine = self._run_sync(self._get_engine())
            self._session_factory = async_sessionmaker(engine, expire_on_commit=False)
        return self._session_factory

    def save(self, state: ExecutionState) -> None:
        state.updated_at = datetime.now().isoformat()
        payload = {
            "execution_id": state.execution_id,
            "release_plan_name": state.release_plan_name,
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
            "last_stable_state": state.last_stable_state,
            "event_cursor": state.event_cursor,
            "replay_version": state.replay_version,
            "execution_meta": dict(state.metadata or {}),
        }

        async def _save():
            session_factory = await self._ensure_session()
            async with session_factory() as session:
                stmt = select(ExecutionRow).where(ExecutionRow.execution_id == state.execution_id)
                existing = await session.scalar(stmt)
                if existing:
                    for k, v in payload.items():
                        if k != "execution_id":
                            setattr(existing, k, v)
                else:
                    session.add(ExecutionRow(**payload))
                await session.commit()

        self._run_sync(_save())

    def load(self, execution_id: str) -> Optional[ExecutionState]:
        async def _load():
            session_factory = await self._ensure_session()
            async with session_factory() as session:
                stmt = select(ExecutionRow).where(ExecutionRow.execution_id == execution_id)
                row = await session.scalar(stmt)
                if row is None:
                    return None
                return self._to_state(row)

        return self._run_sync(_load())

    def delete(self, execution_id: str) -> bool:
        async def _delete():
            session_factory = await self._ensure_session()
            async with session_factory() as session:
                result = await session.execute(
                    delete(ExecutionRow).where(ExecutionRow.execution_id == execution_id)
                )
                await session.commit()
                return (result.rowcount or 0) > 0

        return self._run_sync(_delete())

    def list_executions(self, status: Optional[ExecutionStatus] = None, limit: int = 50) -> List[ExecutionState]:
        async def _list():
            session_factory = await self._ensure_session()
            async with session_factory() as session:
                stmt = select(ExecutionRow)
                if status is not None:
                    stmt = stmt.where(ExecutionRow.status == status.value)
                stmt = stmt.order_by(ExecutionRow.updated_at.desc()).limit(limit)
                rows = await session.scalars(stmt)
                return [self._to_state(r) for r in rows.all()]

        return self._run_sync(_list())

    def create_checkpoint(
        self,
        execution_id: str,
        sprint_idx: int,
        sprint_name: str,
        task_results: List[Dict[str, Any]],
        release_plan_yaml: Optional[str] = None,
        last_stable_state: Optional[Dict[str, Any]] = None,
        event_cursor: Optional[int] = None,
    ) -> bool:
        state = self.load(execution_id)
        if state is None:
            from loguru import logger
            logger.warning("Cannot create checkpoint: state {} not found", execution_id)
            return False
        state.checkpoint = {
            "sprint_idx": sprint_idx,
            "sprint_name": sprint_name,
            "task_results": task_results,
            "timestamp": datetime.now().isoformat(),
            "release_plan_yaml": release_plan_yaml,
        }
        state.last_stable_state = last_stable_state or {
            "sprint_idx": sprint_idx,
            "sprint_name": sprint_name,
            "status": "stable",
            "task_count": len(task_results),
        }
        if event_cursor is not None:
            state.event_cursor = event_cursor
        self.save(state)
        return True

    def can_resume(self, execution_id: str) -> bool:
        state = self.load(execution_id)
        return (
            state is not None
            and state.status in (ExecutionStatus.PAUSED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED)
            and state.checkpoint is not None
        )

    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        state = self.load(execution_id)
        if state and state.checkpoint:
            cp = state.checkpoint
            yml = checkpoint_plan_yaml(cp)
            return {
                "current_sprint": cp.get("sprint_idx", 0),
                "sprint_name": cp.get("sprint_name", ""),
                "task_results": cp.get("task_results", []),
                "release_plan_yaml": yml,
                "last_stable_state": state.last_stable_state,
                "event_cursor": state.event_cursor,
                "replay_version": state.replay_version,
            }
        return None

    def update_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error: Optional[str] = None,
        last_stable_state: Optional[Dict[str, Any]] = None,
        event_cursor: Optional[int] = None,
    ) -> bool:
        from loguru import logger

        state = self.load(execution_id)
        if state is None:
            return False
        err = validate_transition("execution", state.status, status)
        if err:
            logger.warning(err)
        state.status = status
        if error:
            state.error = error
        if last_stable_state is not None:
            state.last_stable_state = last_stable_state
        if event_cursor is not None:
            state.event_cursor = event_cursor
        self.save(state)
        return True

    def increment_progress(self, execution_id: str, completed_tasks: int = 1, completed_sprints: int = 0) -> bool:
        state = self.load(execution_id)
        if state is None:
            return False
        state.completed_tasks += completed_tasks
        state.current_sprint += completed_sprints
        self.save(state)
        return True

    @staticmethod
    def _to_state(row: ExecutionRow) -> ExecutionState:
        return ExecutionState(
            execution_id=row.execution_id,
            release_plan_name=row.release_plan_name,
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
            last_stable_state=row.last_stable_state,
            event_cursor=row.event_cursor,
            replay_version=getattr(row, "replay_version", 1) or 1,
        )
