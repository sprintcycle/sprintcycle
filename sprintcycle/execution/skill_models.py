"""Skill 全链路数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SkillArtifact:
    skill_id: str
    version: str
    path: str
    content_hash: str = ""
    installed_at: str = ""
    source: str = "openclaw"
    status: str = "installed"


@dataclass
class SkillInjectionState:
    skill_id: str
    scene: str
    status: str = "pending_injection"
    injected_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    retro_at: Optional[str] = None
    injection_source: str = ""
    prompt_fragments: List[str] = field(default_factory=list)
    review_checklist: List[Any] = field(default_factory=list)
    retro_metrics: Dict[str, Any] = field(default_factory=dict)
    review_notes: List[str] = field(default_factory=list)

    def mark_injected(self) -> None:
        self.status = "injected"
        self.injected_at = datetime.now().isoformat()

    def mark_reviewed(self) -> None:
        self.status = "reviewed"
        self.reviewed_at = datetime.now().isoformat()

    def mark_retro(self) -> None:
        self.status = "retired"
        self.retro_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillExecutionRecord:
    execution_id: str
    sprint_name: str
    task_name: str
    scene: str
    skill_id: str
    state: SkillInjectionState
    market_source: str = "openclaw"
    market_version: str = "latest"


@dataclass
class TaskSkillTrace:
    execution_id: str
    sprint_name: str
    task_name: str
    scene: str
    matched_skills: List[str] = field(default_factory=list)
    injected_skills: List[str] = field(default_factory=list)
    review_checklist: List[Any] = field(default_factory=list)
    review_status: str = "pending"
    review_score: float = 0.0
    retro_metrics: Dict[str, Any] = field(default_factory=dict)


__all__ = ["SkillArtifact", "SkillInjectionState", "SkillExecutionRecord", "TaskSkillTrace"]
