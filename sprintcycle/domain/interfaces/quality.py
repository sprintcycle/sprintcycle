"""
Domain 层质量档位定义 — 纯函数，无外部依赖

从 infrastructure/config/quality.py 迁移而来。
用于 Domain 层判断质量档位，不依赖任何外层。
"""

from typing import Literal

QualityLevel = Literal["L0", "L1", "L2", "L3"]
QualityProfile = Literal["default", "off", "fast", "strict"]

QUALITY_LEVELS = frozenset({"L0", "L1", "L2", "L3"})
QUALITY_PROFILES = frozenset({"default", "off", "fast", "strict"})


def normalize_quality_level(level: str) -> str:
    """标准化质量档位"""
    u = (level or "L2").strip().upper()
    return u if u in QUALITY_LEVELS else "L2"


def normalize_quality_profile(profile: str) -> str:
    """标准化质量配置档位"""
    p = (profile or "default").strip().lower()
    return p if p in QUALITY_PROFILES else "default"


def runs_pytest(level: str) -> bool:
    """是否运行 pytest（L2/L3）"""
    return normalize_quality_level(level) in ("L2", "L3")


def runs_static_gate(level: str) -> bool:
    """是否运行静态检查（非 L0）"""
    return normalize_quality_level(level) != "L0"


def runs_coverage_gate(level: str) -> bool:
    """是否运行覆盖率门禁（L2/L3）"""
    return normalize_quality_level(level) in ("L2", "L3")


def runs_architecture_guard(level: str) -> bool:
    """是否运行架构守护（L3）"""
    return normalize_quality_level(level) == "L3"


__all__ = [
    "QualityLevel",
    "QualityProfile",
    "normalize_quality_level",
    "normalize_quality_profile",
    "runs_pytest",
    "runs_static_gate",
    "runs_coverage_gate",
    "runs_architecture_guard",
]
