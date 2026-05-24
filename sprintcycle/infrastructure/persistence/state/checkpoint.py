"""
Checkpoint Mixin - 断点续传功能

为 SprintExecutor 提供检查点保存和恢复能力。
"""

import uuid
from typing import Any, Dict, Optional

from loguru import logger

from sprintcycle.domain.models import ReleasePlan
from sprintcycle.domain.interfaces import ExecutionStatus, SprintResult
from .state_store import ExecutionState, StateStore


class CheckpointMixin:
    """断点续传 Mixin，需与拥有 state_store / _execution_id / _release_plan 属性的类配合使用"""

    _execution_id: str
    _release_plan: Optional["ReleasePlan"]
    _event_cursor: Optional[int]

    @property
    def state_store(self) -> "StateStore":
        raise NotImplementedError  # provided by SprintExecutor

    def _init_execution_state(self, release_plan: Optional[ReleasePlan] = None) -> str:
        if self._execution_id is None:
            self._execution_id: str = f"exec_{uuid.uuid4().hex[:8]}"

        total_sprints = (
            len(release_plan.sprints)
            if release_plan
            else (len(self._release_plan.sprints) if self._release_plan else 0)
        )
        total_tasks = (
            release_plan.total_tasks if release_plan else (self._release_plan.total_tasks if self._release_plan else 0)
        )

        state = ExecutionState(
            execution_id=self._execution_id,
            release_plan_name=release_plan.project.name
            if release_plan and release_plan.project
            else (self._release_plan.project.name if self._release_plan else "unknown"),
            mode="normal",
            status=ExecutionStatus.RUNNING,
            total_sprints=total_sprints,
            total_tasks=total_tasks,
        )

        self.state_store.save(state)
        logger.info(f"执行状态已初始化: {self._execution_id}")
        return self._execution_id

    def _save_checkpoint(self, sprint_idx: int, sprint_name: str, sprint_result: SprintResult) -> None:
        if not self._execution_id:
            return

        task_results = [r.to_dict() for r in sprint_result.task_results]

        # 获取执行计划 YAML 用于恢复
        release_plan_yaml = None
        if self._release_plan:
            try:
                release_plan_yaml = self._release_plan.to_yaml()
            except Exception as e:
                logger.warning(f"无法序列化执行计划为 YAML: {e}")

        last_stable_state = {
            "execution_id": self._execution_id,
            "sprint_idx": sprint_idx,
            "sprint_name": sprint_name,
            "status": ExecutionStatus.RUNNING.value,
            "task_count": len(task_results),
        }
        success = self.state_store.create_checkpoint(
            execution_id=self._execution_id,
            sprint_idx=sprint_idx,
            sprint_name=sprint_name,
            task_results=task_results,
            release_plan_yaml=release_plan_yaml,
            last_stable_state=last_stable_state,
            event_cursor=getattr(self, "_event_cursor", None),
        )

        if success:
            self.state_store.increment_progress(
                execution_id=self._execution_id,
                completed_tasks=sprint_result.success_count,
                completed_sprints=1,
            )
            logger.debug(f"检查点已保存: {sprint_name}")

    def can_resume(self, execution_id: str) -> bool:
        return self.state_store.can_resume(execution_id)

    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return self.state_store.get_resume_point(execution_id)

    def load_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        return self.state_store.load(execution_id)

    def pause_execution(self) -> bool:
        if not self._execution_id:
            return False
        return self.state_store.update_status(
            execution_id=self._execution_id,
            status=ExecutionStatus.PAUSED,
        )

    def resume_execution(self, execution_id: str) -> bool:
        state = self.load_execution_state(execution_id)
        if not state or state.status != ExecutionStatus.PAUSED:
            return False
        self._execution_id = execution_id
        return self.state_store.update_status(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
        )
