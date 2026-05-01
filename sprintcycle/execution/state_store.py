"""
执行状态持久化

支持：
- 断点续传
- 执行历史查询
- 状态恢复
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .sprint_types import ExecutionStatus
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskCheckpoint:
    """任务断点数据"""
    task_id: str
    task_name: str
    agent: str
    status: str
    completed_at: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SprintCheckpoint:
    """Sprint 断点数据"""
    sprint_idx: int
    sprint_name: str
    tasks: List[TaskCheckpoint] = field(default_factory=list)


@dataclass
class ExecutionState:
    """
    执行状态
    
    记录完整的执行上下文，支持断点续传。
    """
    execution_id: str
    prd_name: str
    mode: str
    status: ExecutionStatus
    current_sprint: int = 0
    total_sprints: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0
    created_at: str = ""
    updated_at: str = ""
    error: Optional[str] = None
    checkpoint: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_id": self.execution_id,
            "prd_name": self.prd_name,
            "mode": self.mode,
            "status": self.status.value,
            "current_sprint": self.current_sprint,
            "total_sprints": self.total_sprints,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "checkpoint": self.checkpoint,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """从字典创建"""
        data = data.copy()
        data['status'] = ExecutionStatus(data['status'])
        return cls(**data)


class StateStore:
    """
    状态存储
    
    提供执行状态的持久化和查询功能。
    使用 JSON 文件存储，每个 execution_id 对应一个文件。
    """
    
    def __init__(self, store_dir: Optional[str] = None):
        """
        初始化状态存储
        
        Args:
            store_dir: 存储目录路径，默认使用 .sprintcycle/state
        """
        self.store_dir = Path(store_dir) if store_dir else Path(".sprintcycle/state")
        self.store_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_path(self, execution_id: str) -> Path:
        """获取状态文件路径"""
        # 清理 execution_id 中的非法字符
        safe_id = execution_id.replace("/", "_").replace("\\", "_")
        return self.store_dir / f"{safe_id}.json"
    
    def save(self, state: ExecutionState) -> None:
        """
        保存执行状态
        
        Args:
            state: 执行状态对象
        """
        state.updated_at = datetime.now().isoformat()
        path = self._get_state_path(state.execution_id)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"State saved: {state.execution_id}")
        except Exception as e:
            logger.error(f"Failed to save state {state.execution_id}: {e}")
            raise
    
    def load(self, execution_id: str) -> Optional[ExecutionState]:
        """
        加载执行状态
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            ExecutionState 或 None（如果不存在）
        """
        path = self._get_state_path(execution_id)
        if not path.exists():
            return None
        
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            return ExecutionState.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load state {execution_id}: {e}")
            return None
    
    def delete(self, execution_id: str) -> bool:
        """
        删除执行状态
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            是否成功删除
        """
        path = self._get_state_path(execution_id)
        if path.exists():
            try:
                path.unlink()
                logger.debug(f"State deleted: {execution_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete state {execution_id}: {e}")
        return False
    
    def list_executions(
        self, 
        status: Optional[ExecutionStatus] = None,
        limit: int = 50
    ) -> List[ExecutionState]:
        """
        列出所有执行记录
        
        Args:
            status: 可选的状态过滤
            limit: 最大返回数量
            
        Returns:
            按时间倒序排列的执行状态列表
        """
        states = []
        for path in self.store_dir.glob("*.json"):
            try:
                state = self.load(path.stem)
                if state and (status is None or state.status == status):
                    states.append(state)
            except Exception as e:
                logger.warning(f"Failed to load state file {path}: {e}")
        
        # 按时间倒序排列
        states.sort(key=lambda s: s.created_at, reverse=True)
        return states[:limit]
    
    def create_checkpoint(
        self, 
        execution_id: str, 
        sprint_idx: int,
        sprint_name: str,
        task_results: List[Dict[str, Any]],
        prd_yaml: Optional[str] = None
    ) -> bool:
        """
        创建断点
        
        Args:
            execution_id: 执行 ID
            sprint_idx: 当前 Sprint 索引
            sprint_name: Sprint 名称
            task_results: 任务结果列表
            prd_yaml: PRD YAML 字符串（用于恢复）
            
        Returns:
            是否成功创建
        """
        state = self.load(execution_id)
        if state is None:
            logger.warning(f"Cannot create checkpoint: state {execution_id} not found")
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
        """
        检查是否可以恢复
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            是否可以恢复执行
        """
        state = self.load(execution_id)
        return (
            state is not None and 
            state.status in (ExecutionStatus.PAUSED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED) and
            state.checkpoint is not None
        )
    
    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        获取恢复点信息
        
        Args:
            execution_id: 执行 ID
            
        Returns:
            断点数据或 None
        """
        state = self.load(execution_id)
        if state and state.checkpoint:
            return {
                "current_sprint": state.checkpoint.get("sprint_idx", 0),
                "sprint_name": state.checkpoint.get("sprint_name", ""),
                "task_results": state.checkpoint.get("task_results", []),
                "prd_yaml": state.checkpoint.get("prd_yaml"),
            }
        return None
    
    def update_status(
        self, 
        execution_id: str, 
        status: ExecutionStatus,
        error: Optional[str] = None
    ) -> bool:
        """
        更新执行状态
        
        Args:
            execution_id: 执行 ID
            status: 新状态
            error: 可选的错误信息
            
        Returns:
            是否成功更新
        """
        state = self.load(execution_id)
        if state is None:
            return False
        
        state.status = status
        if error:
            state.error = error
        self.save(state)
        return True
    
    def increment_progress(
        self, 
        execution_id: str, 
        completed_tasks: int = 1,
        completed_sprints: int = 0
    ) -> bool:
        """
        更新执行进度
        
        Args:
            execution_id: 执行 ID
            completed_tasks: 完成的任务数
            completed_sprints: 完成的 Sprint 数
            
        Returns:
            是否成功更新
        """
        state = self.load(execution_id)
        if state is None:
            return False
        
        state.completed_tasks += completed_tasks
        state.current_sprint += completed_sprints
        self.save(state)
        return True


# 全局默认状态存储实例
_default_store: Optional[StateStore] = None


def get_state_store(store_dir: Optional[str] = None) -> StateStore:
    """获取默认状态存储实例"""
    global _default_store
    if _default_store is None:
        _default_store = StateStore(store_dir)
    return _default_store
