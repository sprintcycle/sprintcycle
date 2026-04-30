"""
SprintCycle Evolution Configuration

v0.9.0: EvolutionEngineConfig 已废弃，统一使用 RuntimeConfig。
本模块保留仅为向后兼容导出。
"""

import warnings

from sprintcycle.config.manager import RuntimeConfig  # noqa: F401


def __getattr__(name):
    """兼容别名：访问 EvolutionEngineConfig 时发出弃用警告"""
    if name == "EvolutionEngineConfig":
        warnings.warn(
            "EvolutionEngineConfig is deprecated, use RuntimeConfig instead",
            DeprecationWarning,
            stacklevel=2,
        )
        # 返回 RuntimeConfig 作为兼容替代
        return RuntimeConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
