# mypy: disable-error-code=attr-defined
"""
Checkpoint Mixin - 断点续传功能

为 SprintExecutor 提供检查点保存和恢复能力。
"""

import logging
import uuid
from typing import Dict, Any, Optional

from ..prd.models import PRD
from .state_store import ExecutionState, ExecutionStateStatus
from .sprint_types import SprintResult

logger = logging.getLogger(__name__)


class CheckpointMixin:  # type: ignore[misc]
    """断点续传 Mixin，需与拥有 state_store / _execution_id / _prd 属性的类配合使用"""

    def _init_execution_state(self, prd: Optional[PRD] = None) -> str:
        if self._execution_id is None:
            self._execution_id: str = f"exec_{uuid.uuid4().hex[:8]}"
        
        total_sprints = len(prd.sprints) if prd else (len(self._prd.sprints) if self._prd else 0)
        total_tasks = prd.total_tasks if prd else (self._prd.total_tasks if self._prd else 0)
        
        state = ExecutionState(
            execution_id=self._execution_id,
            prd_name=prd.project.name if prd and prd.project else (self._prd.project.name if self._prd else "unknown"),
            mode="normal",
            status=ExecutionStateStatus.RUNNING,
            total_sprints=total_sprints,
            total_tasks=total_tasks,
        )
        
        self.state_store.save(state)
        logger.info(f"执行状态已初始化: {self._execution_id}")
        return self._execution_id
    
    def _save_checkpoint(
        self, 
        sprint_idx: int, 
        sprint_name: str, 
        sprint_result: SprintResult
    ) -> None:
        if not self._execution_id:
            return
        
        task_results = [r.to_dict() for r in sprint_result.task_results]
        
        # 获取 PRD YAML 用于恢复
        prd_yaml = None
        if self._prd:
            try:
                prd_yaml = self._prd.to_yaml()
            except Exception as e:
                logger.warning(f"无法序列化 PRD 为 YAML: {e}")
        
        success = self.state_store.create_checkpoint(
            execution_id=self._execution_id,
            sprint_idx=sprint_idx,
            sprint_name=sprint_name,
            task_results=task_results,
            prd_yaml=prd_yaml,
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
            status=ExecutionStateStatus.PAUSED,
        )
    
    def resume_execution(self, execution_id: str) -> bool:
        state = self.load_execution_state(execution_id)
        if not state or state.status != ExecutionStateStatus.PAUSED:
            return False
        self._execution_id = execution_id
        return self.state_store.update_status(
            execution_id=execution_id,
            status=ExecutionStateStatus.RUNNING,
        )
