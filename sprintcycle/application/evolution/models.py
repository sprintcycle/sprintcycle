"""Evolution domain models for sandboxed multi-sprint evolution.

These models are intentionally lightweight and backend-agnostic.
They support both:
- code evolution (SprintCycle framework evolution)
- requirement evolution (user intent / release plan evolution)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional

EvolutionTarget = Literal["code", "requirement"]
EvolutionMode = Literal["multi_sprint", "single_sprint"]
EvolutionStage = Literal[
    "pending",
    "planning",
    "sandboxing",
    "validating",
    "validated",
    "promoted",
    "rejected",
    "rolled_back",
    "failed",
]
SandboxBackend = Literal["worktree", "docker", "hybrid"]
VersioningBackend = Literal["git", "sqlite", "hybrid"]


@dataclass(slots=True)
class EvolutionRequest:
    request_id: str
    target: EvolutionTarget
    project_path: str
    mode: EvolutionMode = "multi_sprint"
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvolutionPlan:
    request_id: str
    target: EvolutionTarget
    summary: str
    actions: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SandboxSpec:
    sandbox_id: str
    root_dir: str
    worktree_path: str
    backend: SandboxBackend = "worktree"
    read_only_paths: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationResult:
    success: bool
    checks: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VersionArtifact:
    version_id: str
    target: EvolutionTarget
    commit_hash: Optional[str] = None
    tag: Optional[str] = None
    branch: Optional[str] = None
    manifest_path: Optional[str] = None
    sandbox_id: Optional[str] = None
    source_suggestion_id: Optional[str] = None
    source_evolution_request_id: Optional[str] = None
    rollback_to: Optional[str] = None
    promotion_guard: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PromotionResult:
    success: bool
    artifact: Optional[VersionArtifact] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RollbackOutcome:
    success: bool
    version_id: Optional[str] = None
    restored_to: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
