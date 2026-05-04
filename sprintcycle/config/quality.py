"""
质量档位 L0–L3（与产品方案 V4.0 对齐）

L0: 仅代码生成
L1: 静态检查（Ruff + Mypy）默认档
L2: L1 + 单元测试 + 覆盖率门禁
L3: L2 + 架构不变量 + 进化适应度（架构门禁在后续迭代完整落地）
"""

from __future__ import annotations

from typing import Literal

QualityLevel = Literal["L0", "L1", "L2", "L3"]

QUALITY_LEVELS = frozenset({"L0", "L1", "L2", "L3"})


def normalize_quality_level(level: str) -> str:
    u = (level or "L1").strip().upper()
    return u if u in QUALITY_LEVELS else "L1"


def runs_pytest(level: str) -> bool:
    return normalize_quality_level(level) in ("L2", "L3")


def runs_static_gate(level: str) -> bool:
    return normalize_quality_level(level) != "L0"


def runs_coverage_gate(level: str) -> bool:
    return normalize_quality_level(level) in ("L2", "L3")


def runs_architecture_guard(level: str) -> bool:
    return normalize_quality_level(level) == "L3"
