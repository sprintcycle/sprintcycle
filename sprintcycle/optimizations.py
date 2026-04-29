"""
SprintCycle 优化功能聚合模块

功能已拆分到独立模块，本文件作为向后兼容的导入聚合器：
- rollback.py - RollbackManager (文件回滚)
- timeout.py - TimeoutHandler (超时处理)
- error_helper.py - ErrorHelper, ErrorCategory, FailureRecord (错误处理)
- evolution.py - EvolutionEngine (进化引擎)
- five_source.py - FiveSourceVerifier (五源验证)

请直接从子模块导入以获得更好的代码组织。
"""

# 向后兼容：从子模块导入所有功能
from .rollback import RollbackManager
from .timeout import TimeoutHandler, TimeoutResult
from .error_helper import ErrorHelper, ErrorCategory, FailureRecord
from .evolution import EvolutionEngine
from .five_source import FiveSourceVerifier

__all__ = [
    # 回滚管理
    "RollbackManager",
    # 超时处理
    "TimeoutHandler",
    "TimeoutResult",
    # 错误处理
    "ErrorHelper",
    "ErrorCategory",
    "FailureRecord",
    # 进化引擎
    "EvolutionEngine",
    # 五源验证
    "FiveSourceVerifier",
]

# 版本信息
__version__ = "4.10.0"
