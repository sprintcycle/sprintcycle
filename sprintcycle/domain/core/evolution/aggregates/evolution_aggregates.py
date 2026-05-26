"""Evolution subdomain aggregates.

This module provides DDD aggregates for the Evolution subdomain:
- EvolutionRequest: Manages evolution lifecycle
- SandboxSession: Manages sandbox environment lifecycle
- VersionArtifact: Value object for version artifacts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4


# =============================================================================
# Enums
# =============================================================================


class EvolutionTarget(Enum):
    """Evolution target type."""

    CODE = "code"
    REQUIREMENT = "requirement"


class EvolutionMode(Enum):
    """Evolution execution mode."""

    MULTI_SPRINT = "multi_sprint"
    SINGLE_SPRINT = "single_sprint"


class EvolutionStage(Enum):
    """Evolution lifecycle stage."""

    PENDING = "pending"
    SANDBOXING = "sandboxing"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class SandboxBackend(Enum):
    """Sandbox backend type."""

    WORKTREE = "worktree"
    DOCKER = "docker"
    HYBRID = "hybrid"


class SandboxStatus(Enum):
    """Sandbox session status."""

    CREATING = "creating"
    READY = "ready"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    CLEANED_UP = "cleaned_up"


# =============================================================================
# Value Objects
# =============================================================================


@dataclass(frozen=True)
class VersionArtifact:
    """
    Version artifact value object.

    Represents a versioned code/release artifact.
    """

    version_id: str
    commit_hash: str
    tag: str = ""
    branch: str = ""
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "commit_hash": self.commit_hash,
            "tag": self.tag,
            "branch": self.branch,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ValidationCheck:
    """Validation check result."""

    name: str
    passed: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class SandboxSpec:
    """Sandbox specification."""

    root_dir: str
    worktree_path: str
    backend: SandboxBackend
    read_only_paths: Tuple[str, ...] = ()
    env: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "worktree_path": self.worktree_path,
            "backend": self.backend.value,
            "read_only_paths": list(self.read_only_paths),
            "env": dict(self.env),
        }


# =============================================================================
# Cross-Subdomain References
# =============================================================================


@dataclass(frozen=True)
class GovernanceRef:
    """Reference to a governance session."""

    governance_session_id: str = ""
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_session_id": self.governance_session_id,
            "approved": self.approved,
        }


@dataclass(frozen=True)
class SandboxRef:
    """Reference to a sandbox session."""

    sandbox_id: str = ""
    created: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "created": self.created,
        }


@dataclass(frozen=True)
class VersionRef:
    """Reference to a version."""

    version_id: str = ""
    versioned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "versioned": self.versioned,
        }


# =============================================================================
# SandboxSession Aggregate
# =============================================================================


class SandboxSession:
    """
    Sandbox session aggregate root.

    Manages the lifecycle of a sandbox environment for evolution.

    **Immutable Updates:**
    All state-modifying methods return new instances.
    """

    def __init__(
        self,
        sandbox_id: str,
        spec: SandboxSpec,
        status: SandboxStatus = SandboxStatus.CREATING,
        validation_checks: Tuple[ValidationCheck, ...] = (),
        created_at: Optional[datetime] = None,
        validated_at: Optional[datetime] = None,
        cleaned_up_at: Optional[datetime] = None,
        error_message: str = "",
    ):
        self._sandbox_id = sandbox_id
        self._spec = spec
        self._status = status
        self._validation_checks = validation_checks
        self._created_at = created_at
        self._validated_at = validated_at
        self._cleaned_up_at = cleaned_up_at
        self._error_message = error_message

    @property
    def sandbox_id(self) -> str:
        return self._sandbox_id

    @property
    def spec(self) -> SandboxSpec:
        return self._spec

    @property
    def status(self) -> SandboxStatus:
        return self._status

    @property
    def is_terminal(self) -> bool:
        return self._status in (
            SandboxStatus.VALIDATED,
            SandboxStatus.FAILED,
            SandboxStatus.CLEANED_UP,
        )

    @property
    def is_valid(self) -> bool:
        return self._status == SandboxStatus.VALIDATED and all(
            check.passed for check in self._validation_checks
        )

    def ready(self) -> "SandboxSession":
        """Mark sandbox as ready."""
        if self._status != SandboxStatus.CREATING:
            raise ValueError(f"Cannot ready from status: {self._status}")
        return SandboxSession(
            sandbox_id=self._sandbox_id,
            spec=self._spec,
            status=SandboxStatus.READY,
            validation_checks=self._validation_checks,
            created_at=self._created_at,
            validated_at=None,
            cleaned_up_at=None,
            error_message=self._error_message,
        )

    def add_validation_check(self, check: ValidationCheck) -> "SandboxSession":
        """Add a validation check result."""
        return SandboxSession(
            sandbox_id=self._sandbox_id,
            spec=self._spec,
            status=SandboxStatus.VALIDATING,
            validation_checks=self._validation_checks + (check,),
            created_at=self._created_at,
            validated_at=None,
            cleaned_up_at=None,
            error_message=self._error_message,
        )

    def complete_validation(self) -> "SandboxSession":
        """Complete validation."""
        all_passed = all(check.passed for check in self._validation_checks)
        new_status = SandboxStatus.VALIDATED if all_passed else SandboxStatus.FAILED
        return SandboxSession(
            sandbox_id=self._sandbox_id,
            spec=self._spec,
            status=new_status,
            validation_checks=self._validation_checks,
            created_at=self._created_at,
            validated_at=datetime.now() if all_passed else None,
            cleaned_up_at=None,
            error_message=self._error_message,
        )

    def cleanup(self) -> "SandboxSession":
        """Clean up the sandbox."""
        return SandboxSession(
            sandbox_id=self._sandbox_id,
            spec=self._spec,
            status=SandboxStatus.CLEANED_UP,
            validation_checks=self._validation_checks,
            created_at=self._created_at,
            validated_at=self._validated_at,
            cleaned_up_at=datetime.now(),
            error_message=self._error_message,
        )

    def mark_failed(self, error: str) -> "SandboxSession":
        """Mark sandbox as failed."""
        return SandboxSession(
            sandbox_id=self._sandbox_id,
            spec=self._spec,
            status=SandboxStatus.FAILED,
            validation_checks=self._validation_checks,
            created_at=self._created_at,
            validated_at=None,
            cleaned_up_at=None,
            error_message=error,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self._sandbox_id,
            "spec": self._spec.to_dict(),
            "status": self._status.value,
            "is_terminal": self.is_terminal,
            "is_valid": self.is_valid,
        }


# =============================================================================
# EvolutionRequest Aggregate
# =============================================================================


class EvolutionRequest:
    """
    Evolution request aggregate root.

    Manages the complete lifecycle of an evolution request:
    - Sandbox creation
    - Version creation
    - Validation
    - Promotion

    **Immutable Updates:**
    All state-modifying methods return new instances.
    """

    def __init__(
        self,
        request_id: str,
        target: EvolutionTarget,
        project_path: str,
        mode: EvolutionMode = EvolutionMode.SINGLE_SPRINT,
        stage: EvolutionStage = EvolutionStage.PENDING,
        governance_ref: Optional[GovernanceRef] = None,
        sandbox_ref: Optional[SandboxRef] = None,
        version_ref: Optional[VersionRef] = None,
        version_artifacts: Tuple[VersionArtifact, ...] = (),
        current_version_index: int = 0,
        intent: str = "",
        context: Dict[str, Any] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._request_id = request_id
        self._target = target
        self._project_path = project_path
        self._mode = mode
        self._stage = stage
        self._governance_ref = governance_ref
        self._sandbox_ref = sandbox_ref
        self._version_ref = version_ref
        self._version_artifacts = version_artifacts
        self._current_version_index = current_version_index
        self._intent = intent
        self._context = context or {}
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def target(self) -> EvolutionTarget:
        return self._target

    @property
    def project_path(self) -> str:
        return self._project_path

    @property
    def mode(self) -> EvolutionMode:
        return self._mode

    @property
    def stage(self) -> EvolutionStage:
        return self._stage

    @property
    def is_terminal(self) -> bool:
        return self._stage in (
            EvolutionStage.PROMOTED,
            EvolutionStage.REJECTED,
            EvolutionStage.ROLLED_BACK,
            EvolutionStage.FAILED,
        )

    @property
    def current_version(self) -> Optional[VersionArtifact]:
        if 0 <= self._current_version_index < len(self._version_artifacts):
            return self._version_artifacts[self._current_version_index]
        return None

    def attach_governance(
        self,
        governance_session_id: str,
        approved: bool = False,
    ) -> "EvolutionRequest":
        """Attach governance reference."""
        ref = GovernanceRef(
            governance_session_id=governance_session_id,
            approved=approved,
        )
        return EvolutionRequest(
            request_id=self._request_id,
            target=self._target,
            project_path=self._project_path,
            mode=self._mode,
            stage=self._stage,
            governance_ref=ref,
            sandbox_ref=self._sandbox_ref,
            version_ref=self._version_ref,
            version_artifacts=self._version_artifacts,
            current_version_index=self._current_version_index,
            intent=self._intent,
            context=dict(self._context),
            created_at=self._created_at,
            updated_at=datetime.now(),
        )

    def create_sandbox(self, sandbox_id: str) -> "EvolutionRequest":
        """Create a sandbox reference."""
        ref = SandboxRef(
            sandbox_id=sandbox_id,
            created=True,
        )
        return EvolutionRequest(
            request_id=self._request_id,
            target=self._target,
            project_path=self._project_path,
            mode=self._mode,
            stage=EvolutionStage.SANDBOXING,
            governance_ref=self._governance_ref,
            sandbox_ref=ref,
            version_ref=self._version_ref,
            version_artifacts=self._version_artifacts,
            current_version_index=self._current_version_index,
            intent=self._intent,
            context=dict(self._context),
            created_at=self._created_at,
            updated_at=datetime.now(),
        )

    def add_version(self, artifact: VersionArtifact) -> "EvolutionRequest":
        """Add a version artifact."""
        new_artifacts = self._version_artifacts + (artifact,)
        new_index = len(new_artifacts) - 1
        return EvolutionRequest(
            request_id=self._request_id,
            target=self._target,
            project_path=self._project_path,
            mode=self._mode,
            stage=EvolutionStage.VALIDATING,
            governance_ref=self._governance_ref,
            sandbox_ref=self._sandbox_ref,
            version_ref=VersionRef(version_id=artifact.version_id, versioned=True),
            version_artifacts=new_artifacts,
            current_version_index=new_index,
            intent=self._intent,
            context=dict(self._context),
            created_at=self._created_at,
            updated_at=datetime.now(),
        )

    def validate(self) -> "EvolutionRequest":
        """Mark as validated."""
        return EvolutionRequest(
            request_id=self._request_id,
            target=self._target,
            project_path=self._project_path,
            mode=self._mode,
            stage=EvolutionStage.VALIDATED,
            governance_ref=self._governance_ref,
            sandbox_ref=self._sandbox_ref,
            version_ref=self._version_ref,
            version_artifacts=self._version_artifacts,
            current_version_index=self._current_version_index,
            intent=self._intent,
            context=dict(self._context),
            created_at=self._created_at,
            updated_at=datetime.now(),
        )

    def promote(self) -> "EvolutionRequest":
        """Promote to production."""
        if self._stage != EvolutionStage.VALIDATED:
            raise ValueError(f"Cannot promote from stage: {self._stage}")
        if self._governance_ref and not self._governance_ref.approved:
            raise ValueError("Governance approval required")

        return EvolutionRequest(
            request_id=self._request_id,
            target=self._target,
            project_path=self._project_path,
            mode=self._mode,
            stage=EvolutionStage.PROMOTED,
            governance_ref=self._governance_ref,
            sandbox_ref=self._sandbox_ref,
            version_ref=self._version_ref,
            version_artifacts=self._version_artifacts,
            current_version_index=self._current_version_index,
            intent=self._intent,
            context=dict(self._context),
            created_at=self._created_at,
            updated_at=datetime.now(),
        )

    def rollback_to(self, version_id: str) -> "EvolutionRequest":
        """Rollback to specified version."""
        for i, artifact in enumerate(self._version_artifacts):
            if artifact.version_id == version_id:
                return EvolutionRequest(
                    request_id=self._request_id,
                    target=self._target,
                    project_path=self._project_path,
                    mode=self._mode,
                    stage=EvolutionStage.ROLLED_BACK,
                    governance_ref=self._governance_ref,
                    sandbox_ref=self._sandbox_ref,
                    version_ref=self._version_ref,
                    version_artifacts=self._version_artifacts,
                    current_version_index=i,
                    intent=self._intent,
                    context=dict(self._context),
                    created_at=self._created_at,
                    updated_at=datetime.now(),
                )
        raise ValueError(f"Version not found: {version_id}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self._request_id,
            "target": self._target.value,
            "project_path": self._project_path,
            "mode": self._mode.value,
            "stage": self._stage.value,
            "is_terminal": self.is_terminal,
            "current_version": self.current_version.to_dict() if self.current_version else None,
            "version_count": len(self._version_artifacts),
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_evolution_request(
    project_path: str,
    target: str = "code",
    mode: str = "single_sprint",
    intent: str = "",
) -> EvolutionRequest:
    """Create a new evolution request."""
    return EvolutionRequest(
        request_id=f"evo-{uuid4()}",
        target=EvolutionTarget(target),
        project_path=project_path,
        mode=EvolutionMode(mode),
        intent=intent,
        created_at=datetime.now(),
    )


def create_sandbox_session(
    root_dir: str,
    worktree_path: str,
    backend: str = "worktree",
) -> SandboxSession:
    """Create a new sandbox session."""
    spec = SandboxSpec(
        root_dir=root_dir,
        worktree_path=worktree_path,
        backend=SandboxBackend(backend),
    )
    return SandboxSession(
        sandbox_id=f"sandbox-{uuid4()}",
        spec=spec,
        created_at=datetime.now(),
    )


__all__ = [
    # Enums
    "EvolutionTarget",
    "EvolutionMode",
    "EvolutionStage",
    "SandboxBackend",
    "SandboxStatus",
    # Value Objects
    "VersionArtifact",
    "ValidationCheck",
    "SandboxSpec",
    "GovernanceRef",
    "SandboxRef",
    "VersionRef",
    # Aggregates
    "SandboxSession",
    "EvolutionRequest",
    # Factory Functions
    "create_evolution_request",
    "create_sandbox_session",
]
