"""
SprintCycle Chorus 模块 v4.10
包含 Agent 协调、工具路由、知识库管理

v4.10 改进:
- Sprint 1: files_changed 类型处理 bug 修复 - 统一处理 dict/list/None 类型
- Sprint 2: 失败原因精准归因 - 扩展 ErrorHelper 类
- Sprint 3: 超时处理增强 - 完善 TimeoutHandler
- Sprint 4: UI_VERIFY Agent 完善 - 增强验证方法
- Sprint 5: 任务回滚机制 - 完善 RollbackManager

文件拆分说明 (Phase 2):
- chorus/enums.py: 枚举定义
- chorus/progress.py: 进度和结果数据类
- chorus/config.py: 配置管理
- chorus/knowledge.py: 知识库
- chorus/execution.py: 执行层
- chorus/adapter.py: 工具路由适配器
- chorus/orchestrator.py: Agent 协调层
- chorus/utils.py: 工具函数
"""

# 延迟导入优化模块以避免循环依赖
_imported_optimizations = False


def _get_optimizations():
    global _imported_optimizations
    if not _imported_optimizations:
        from .. import optimizations
        globals().update({
            'FileTracker': getattr(optimizations, 'FileTracker', None),
            'TaskSplitter': getattr(optimizations, 'TaskSplitter', None),
            'SplitConfig': getattr(optimizations, 'SplitConfig', None),
            'ExecutionLog': getattr(optimizations, 'ExecutionLog', None),
            'DependencyManager': getattr(optimizations, 'DependencyManager', None),
            'ResultValidator': getattr(optimizations, 'ResultValidator', None),
            'FiveSourceVerifier': getattr(optimizations, 'FiveSourceVerifier', None),
            'EvolutionEngine': getattr(optimizations, 'EvolutionEngine', None),
            'RollbackManager': getattr(optimizations, 'RollbackManager', None),
            'TimeoutHandler': getattr(optimizations, 'TimeoutHandler', None),
            'ErrorHelper': getattr(optimizations, 'ErrorHelper', None),
        })
        _imported_optimizations = True
    return globals()


# 从各子模块导入
from .enums import ToolType, AgentType, TaskStatus
from .progress import ExecutionResult, TaskProgress
from .config import Config, get_credential_manager_wrapper
from .knowledge import KnowledgeBase
from .execution import ExecutionLayer
from .adapter import ChorusAdapter
from .orchestrator import Chorus, ChorusOrchestrator
from .utils import (
    normalize_files_changed,
    extract_files_list,
    has_changes,
    get_change_summary
)

# 凭证管理
_credential_manager_wrapper = None


def get_credential_manager(project_path="."):
    """凭证管理器获取"""
    global _credential_manager_wrapper
    if _credential_manager_wrapper is None:
        _credential_manager_wrapper = get_credential_manager_wrapper(project_path)
    return _credential_manager_wrapper


# 导出公共接口
__all__ = [
    # 枚举
    "ToolType",
    "AgentType",
    "TaskStatus",
    # 数据类
    "ExecutionResult",
    "TaskProgress",
    # 核心类
    "Config",
    "KnowledgeBase",
    "ExecutionLayer",
    "ChorusAdapter",
    "Chorus",
    "ChorusOrchestrator",  # 向后兼容别名
    # 工具函数
    "normalize_files_changed",
    "extract_files_list",
    "has_changes",
    "get_change_summary",
    # 凭证管理
    "get_credential_manager",
]
