"""
基于 SQLite + SQLAlchemy 的执行状态存储（与 StateStore 方法签名对齐）。

迁移到 BaseSqliteStore：统一路径规范化、连接生命周期、schema 初始化。
ORM 操作使用 SQLAlchemy AsyncSession。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sprintcycle.domain.generic.models.release_plan.payload_keys import checkpoint_plan_yaml
from sprintcycle.domain.generic.interfaces import ExecutionStatus
from sprintcycle.infrastructure.shared.persistence.base import BaseSqliteStore
from sprintcycle.infrastructure.shared.persistence.models import Base, ExecutionRow
from sprintcycle.domain.core.execution.core.lifecycle_transitions import validate_transition
from .state_store import ExecutionState


class SqliteExecutionStore(BaseSqliteStore):
    """与 ``StateStore`` 相同的对外 API，便于 ``get_state_store`` 切换后端。

    使用 SQLAlchemy AsyncSession 进行 ORM 操作，连接由 BaseSqliteStore 管理。
    """

    def __init__(self, db_path: str) -> None:
        super().__init__(db_path)
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    # ─────────────────────────────────────────────────────────────────
    # BaseSqliteStore 模板方法实现
    # ─────────────────────────────────────────────────────────────────

    def _define_schema(self, conn: Any) -> None:
        """通过 ORM Base 创建所有表。

        注意：此方法在 connect() 上下文中被调用，
        可直接使用 conn.run_sync() 执行同步 DDL。
        """
        conn.run_sync(Base.metadata.create_all)

    async def _ensure_session(self) -> async_sessionmaker[AsyncSession]:
        """延迟创建 AsyncSession 工厂。"""
        if self._session_factory is None:
            engine = await self._get_engine()
            self._session_factory = async_sessionmaker(engine, expire_on_commit=False)
        return self._session_factory

    # ─────────────────────────────────────────────────────────────────
    # 公开 API（与 StateStore 对齐）
    # ─────────────────────────────────────────────────────────────────

    async def save(self, state: ExecutionState) -> None:
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

    async def load(self, execution_id: str) -> Optional[ExecutionState]:
        session_factory = await self._ensure_session()
        async with session_factory() as session:
            stmt = select(ExecutionRow).where(ExecutionRow.execution_id == execution_id)
            row = await session.scalar(stmt)
            if row is None:
                return None
            return self._to_state(row)

    async def delete(self, execution_id: str) -> bool:
        session_factory = await self._ensure_session()
        async with session_factory() as session:
            result = await session.execute(
                delete(ExecutionRow).where(ExecutionRow.execution_id == execution_id)
            )
            await session.commit()
            return (result.rowcount or 0) > 0

    async def list_executions(
        self,
        status: Optional[ExecutionStatus] = None,
        limit: int = 50,
    ) -> List[ExecutionState]:
        session_factory = await self._ensure_session()
        async with session_factory() as session:
            stmt = select(ExecutionRow)
            if status is not None:
                stmt = stmt.where(ExecutionRow.status == status.value)
            stmt = stmt.order_by(ExecutionRow.updated_at.desc()).limit(limit)
            rows = await session.scalars(stmt)
            return [self._to_state(r) for r in rows.all()]

    async def create_checkpoint(
        self,
        execution_id: str,
        sprint_idx: int,
        sprint_name: str,
        task_results: List[Dict[str, Any]],
        release_plan_yaml: Optional[str] = None,
        last_stable_state: Optional[Dict[str, Any]] = None,
        event_cursor: Optional[int] = None,
    ) -> bool:
        state = await self.load(execution_id)
        if state is None:
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
        await self.save(state)
        return True

    async def can_resume(self, execution_id: str) -> bool:
        state = await self.load(execution_id)
        return (
            state is not None
            and state.status in (ExecutionStatus.PAUSED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED)
            and state.checkpoint is not None
        )

    async def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        state = await self.load(execution_id)
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

    async def update_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error: Optional[str] = None,
        last_stable_state: Optional[Dict[str, Any]] = None,
        event_cursor: Optional[int] = None,
    ) -> bool:
        state = await self.load(execution_id)
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
        await self.save(state)
        return True

    async def increment_progress(
        self,
        execution_id: str,
        completed_tasks: int = 1,
        completed_sprints: int = 0,
    ) -> bool:
        state = await self.load(execution_id)
        if state is None:
            return False
        state.completed_tasks += completed_tasks
        state.current_sprint += completed_sprints
        await self.save(state)
        return True

    # ─────────────────────────────────────────────────────────────────
    # 内部工具
    # ─────────────────────────────────────────────────────────────────

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
