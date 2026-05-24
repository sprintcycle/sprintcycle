"""ArchGuard 侧的 Compose 轻量门禁。"""

from __future__ import annotations

from typing import List

from .model import GuardFinding


def check_compose_hints(cfile: str, text: str) -> List[GuardFinding]:
    """检查 compose 提示"""
    return []


def check_compose_supply_chain_hints(cfile: str, text: str) -> List[GuardFinding]:
    """检查 compose 供应链提示"""
    return []


__all__ = ["check_compose_hints", "check_compose_supply_chain_hints"]
