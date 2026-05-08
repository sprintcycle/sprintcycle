"""Hook 共享上下文。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class HookChecklistItem:
    category: str
    title: str
    description: str = ""
    required: bool = False
    source: str = ""
    status: str = "open"
    evidence: List[str] = field(default_factory=list)


@dataclass
class HookReviewContext:
    sprint_name: str
    task_name: str
    execution_id: str
    checklists: List[HookChecklistItem] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = ["HookChecklistItem", "HookReviewContext"]
