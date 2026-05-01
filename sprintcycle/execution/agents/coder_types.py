"""
Coder Agent Types - 数据类型定义
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from .base import AgentContext

@dataclass
class BatchTask:
    """批量任务条目"""
    task: str
    context: "AgentContext"
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchConfig:
    """批量处理配置"""
    enabled: bool = True
    max_batch_size: int = 10
    similarity_threshold: float = 0.7
    merge_similar: bool = True
    parallel_llm_calls: bool = False


@dataclass
class CodeRequirements:
    """代码需求"""
    language: str = "python"
    file_path: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class CodeResult:
    """代码生成结果"""
    success: bool
    code: str = ""
    file_path: Optional[str] = None
    quality_score: float = 0.0
    feedback: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
