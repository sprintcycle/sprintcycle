"""
chorus.progress - 进度和结果数据类
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .enums import TaskStatus
from .utils import normalize_files_changed, extract_files_list, has_changes, get_change_summary


@dataclass
class ExecutionResult:
    """执行结果 v4.10 - 增强 files_changed 处理"""
    success: bool
    output: str
    duration: float
    tool: str
    files_changed: Dict = field(default_factory=lambda: {"added": [], "modified": [], "deleted": [], "screenshots": []})
    retries: int = 0
    error: Optional[str] = None
    error_reason: Optional[str] = None  # v4.10 新增: 精确错误原因
    split_suggestion: List[str] = field(default_factory=list)
    validation: Dict = field(default_factory=dict)
    # v4.10 新增: 审查相关属性
    review: Optional[Dict] = None
    needs_fix: bool = False
    fix_suggestions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """v4.10: 自动规范化 files_changed 类型"""
        self.files_changed = normalize_files_changed(self.files_changed)
    
    @property
    def files_list(self) -> List[str]:
        """v4.10: 获取所有变更文件的列表"""
        return extract_files_list(self.files_changed)
    
    @property
    def has_changes(self) -> bool:
        """v4.10: 是否有变更"""
        return has_changes(self.files_changed)
    
    @property
    def change_summary(self) -> str:
        """v4.10: 获取变更摘要"""
        return get_change_summary(self.files_changed)
    
    def to_dict(self) -> Dict:
        """v4.10: 转换为字典格式"""
        return {
            "success": self.success,
            "output": self.output,
            "duration": self.duration,
            "tool": self.tool,
            "files_changed": self.files_changed,
            "files_list": self.files_list,
            "has_changes": self.has_changes,
            "retries": self.retries,
            "error": self.error,
            "error_reason": self.error_reason,
            "split_suggestion": self.split_suggestion,
            "validation": self.validation
        }


@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    status: TaskStatus
    progress: int
    message: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
