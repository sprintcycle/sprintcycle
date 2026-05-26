"""Governance subdomain aggregates.

This module provides DDD aggregates for the Governance subdomain:
- GovernanceSession: Manages governance check lifecycle
- RuleSetAggregate: Manages rule collections
- Rule: Value object for governance rules
- Finding: Value object for governance findings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# =============================================================================
# Enums
# =============================================================================


class GovernanceGate(Enum):
    """Governance gate types."""

    PLANNING = "planning"
    REVIEW = "review"
    PRODUCTION = "production"
    PROMOTION = "promotion"


class GovernanceStatus(Enum):
    """Governance session status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


# =============================================================================
# Value Objects
# =============================================================================


@dataclass(frozen=True)
class GovernanceRule:
    """Governance rule definition."""

    id: str
    name: str
    category: str
    severity: str = "error"  # "error", "warning", "info"
    enabled: bool = True
    thresholds: Dict[str, Any] = field(default_factory=dict)
    applies_to: tuple = field(default_factory=lambda: ())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "severity": self.severity,
            "enabled": self.enabled,
            "thresholds": dict(self.thresholds),
            "applies_to": list(self.applies_to),
        }


@dataclass(frozen=True)
class RuleEvaluation:
    """Result of evaluating a rule."""

    rule_id: str
    passed: bool
    severity: str
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class Finding:
    """A governance finding (issue discovered)."""

    rule_id: str
    severity: str  # "error", "warning", "info"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# GovernanceSession Aggregate
# =============================================================================


class GovernanceSession:
    """
    Governance session aggregate root.

    Manages the complete lifecycle of a governance check:
    - Rule evaluation
    - Finding collection
    - HITL coordination
    - Final status determination

    **Immutable Updates:**
    All state-modifying methods return new instances.
    """

    def __init__(
        self,
        session_id: str,
        gate: GovernanceGate,
        execution_id: str,
        project_path: str,
        status: GovernanceStatus = GovernanceStatus.PENDING,
        findings: tuple = (),
        rule_evaluations: tuple = (),
        hitl_required: bool = False,
        hitl_approved: bool = False,
        hitl_decision: Optional[str] = None,
        release_plan_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self._session_id = session_id
        self._gate = gate
        self._execution_id = execution_id
        self._project_path = project_path
        self._status = status
        self._findings = findings
        self._rule_evaluations = rule_evaluations
        self._hitl_required = hitl_required
        self._hitl_approved = hitl_approved
        self._hitl_decision = hitl_decision
        self._release_plan_id = release_plan_id
        self._started_at = started_at
        self._completed_at = completed_at

    # Identity
    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def gate(self) -> GovernanceGate:
        return self._gate

    @property
    def execution_id(self) -> str:
        return self._execution_id

    @property
    def project_path(self) -> str:
        return self._project_path

    # State
    @property
    def status(self) -> GovernanceStatus:
        return self._status

    @property
    def is_terminal(self) -> bool:
        return self._status in (
            GovernanceStatus.PASSED,
            GovernanceStatus.FAILED,
        )

    @property
    def is_blocking(self) -> bool:
        """Check if session has blocking issues."""
        if self._hitl_required and not self._hitl_approved:
            return True
        return self.error_count > 0

    # Findings
    @property
    def findings(self) -> tuple:
        return self._findings

    @property
    def error_count(self) -> int:
        return sum(1 for f in self._findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self._findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for f in self._findings if f.severity == "info")

    # Rule evaluations
    @property
    def rule_evaluations(self) -> tuple:
        return self._rule_evaluations

    @property
    def passed_rules(self) -> int:
        return sum(1 for r in self._rule_evaluations if r.passed)

    @property
    def failed_rules(self) -> int:
        return sum(1 for r in self._rule_evaluations if not r.passed)

    # HITL
    @property
    def hitl_required(self) -> bool:
        return self._hitl_required

    @property
    def hitl_approved(self) -> bool:
        return self._hitl_approved

    @property
    def hitl_decision(self) -> Optional[str]:
        return self._hitl_decision

    # Commands
    def start(self) -> "GovernanceSession":
        """Start the governance check."""
        if self._status != GovernanceStatus.PENDING:
            raise ValueError(f"Cannot start session in status: {self._status}")
        return GovernanceSession(
            session_id=self._session_id,
            gate=self._gate,
            execution_id=self._execution_id,
            project_path=self._project_path,
            status=GovernanceStatus.RUNNING,
            findings=self._findings,
            rule_evaluations=self._rule_evaluations,
            hitl_required=self._hitl_required,
            hitl_approved=self._hitl_approved,
            hitl_decision=self._hitl_decision,
            release_plan_id=self._release_plan_id,
            started_at=datetime.now(),
            completed_at=None,
        )

    def add_finding(self, finding: Finding) -> "GovernanceSession":
        """Add a finding to the session."""
        new_hitl_required = self._hitl_required or finding.severity == "error"
        return GovernanceSession(
            session_id=self._session_id,
            gate=self._gate,
            execution_id=self._execution_id,
            project_path=self._project_path,
            status=self._status,
            findings=self._findings + (finding,),
            rule_evaluations=self._rule_evaluations,
            hitl_required=new_hitl_required,
            hitl_approved=self._hitl_approved,
            hitl_decision=self._hitl_decision,
            release_plan_id=self._release_plan_id,
            started_at=self._started_at,
            completed_at=self._completed_at,
        )

    def add_rule_evaluation(self, evaluation: RuleEvaluation) -> "GovernanceSession":
        """Add a rule evaluation result."""
        return GovernanceSession(
            session_id=self._session_id,
            gate=self._gate,
            execution_id=self._execution_id,
            project_path=self._project_path,
            status=self._status,
            findings=self._findings,
            rule_evaluations=self._rule_evaluations + (evaluation,),
            hitl_required=self._hitl_required,
            hitl_approved=self._hitl_approved,
            hitl_decision=self._hitl_decision,
            release_plan_id=self._release_plan_id,
            started_at=self._started_at,
            completed_at=self._completed_at,
        )

    def approve_hitl(self, decision: str) -> "GovernanceSession":
        """Approve via HITL."""
        if not self._hitl_required:
            raise ValueError("HITL not required")
        return GovernanceSession(
            session_id=self._session_id,
            gate=self._gate,
            execution_id=self._execution_id,
            project_path=self._project_path,
            status=self._status,
            findings=self._findings,
            rule_evaluations=self._rule_evaluations,
            hitl_required=True,
            hitl_approved=True,
            hitl_decision=decision,
            release_plan_id=self._release_plan_id,
            started_at=self._started_at,
            completed_at=self._completed_at,
        )

    def complete(self) -> "GovernanceSession":
        """Complete the governance check and determine final status."""
        if self._status != GovernanceStatus.RUNNING:
            raise ValueError(f"Cannot complete session in status: {self._status}")

        # Determine final status
        if self._hitl_required and not self._hitl_approved:
            final_status = GovernanceStatus.BLOCKED
        elif self.error_count > 0:
            final_status = GovernanceStatus.FAILED
        else:
            final_status = GovernanceStatus.PASSED

        return GovernanceSession(
            session_id=self._session_id,
            gate=self._gate,
            execution_id=self._execution_id,
            project_path=self._project_path,
            status=final_status,
            findings=self._findings,
            rule_evaluations=self._rule_evaluations,
            hitl_required=self._hitl_required,
            hitl_approved=self._hitl_approved,
            hitl_decision=self._hitl_decision,
            release_plan_id=self._release_plan_id,
            started_at=self._started_at,
            completed_at=datetime.now(),
        )

    def to_promotion_input(self) -> Dict[str, Any]:
        """Convert to promotion decision input."""
        return {
            "session_id": self._session_id,
            "gate": self._gate.value,
            "execution_id": self._execution_id,
            "passed": self._status == GovernanceStatus.PASSED,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "hitl_required": self._hitl_required,
            "hitl_approved": self._hitl_approved,
            "release_plan_id": self._release_plan_id,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self._session_id,
            "gate": self._gate.value,
            "execution_id": self._execution_id,
            "project_path": self._project_path,
            "status": self._status.value,
            "findings": [f.to_dict() for f in self._findings],
            "rule_evaluations": [r.to_dict() for r in self._rule_evaluations],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "hitl_required": self._hitl_required,
            "hitl_approved": self._hitl_approved,
            "hitl_decision": self._hitl_decision,
            "is_terminal": self.is_terminal,
            "is_blocking": self.is_blocking,
        }


# =============================================================================
# RuleSet Aggregate
# =============================================================================


class RuleSetAggregate:
    """
    RuleSet aggregate root.

    Manages a collection of related governance rules:
    - Rule registration
    - Rule evaluation
    - Category grouping
    """

    def __init__(
        self,
        ruleset_id: str,
        name: str,
        gate_type: str,
        rules: Optional[tuple] = None,
    ):
        self._ruleset_id = ruleset_id
        self._name = name
        self._gate_type = gate_type
        self._rules = rules or ()
        self._rules_by_category: Dict[str, list] = {}
        for rule in rules:
            if rule.category not in self._rules_by_category:
                self._rules_by_category[rule.category] = []
            self._rules_by_category[rule.category].append(rule)

    # Identity
    @property
    def ruleset_id(self) -> str:
        return self._ruleset_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def gate_type(self) -> str:
        return self._gate_type

    # Rules
    @property
    def rules(self) -> tuple:
        return self._rules

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def get_rules_for_gate(self, gate: str) -> tuple:
        """Get rules applicable to a specific gate."""
        return tuple(
            rule for rule in self._rules
            if rule.enabled and (not rule.applies_to or gate in rule.applies_to)
        )

    def get_rules_by_category(self, category: str) -> tuple:
        """Get all rules in a category."""
        return tuple(self._rules_by_category.get(category, []))

    def check_passed(
        self,
        evaluations: tuple,
        strict: bool = True,
    ) -> bool:
        """
        Check if rule evaluations pass.

        strict=True: All error rules must pass
        strict=False: Allow some errors with HITL
        """
        for eval in evaluations:
            if eval.severity == "error" and not eval.passed:
                if strict:
                    return False
                # In non-strict mode, errors might be approved via HITL
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ruleset_id": self._ruleset_id,
            "name": self._name,
            "gate_type": self._gate_type,
            "rule_count": self.rule_count,
            "rules": [r.to_dict() for r in self._rules],
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_governance_session(
    gate: str,
    execution_id: str,
    project_path: str,
    release_plan_id: Optional[str] = None,
) -> GovernanceSession:
    """Create a new governance session."""
    return GovernanceSession(
        session_id=f"gov-{uuid4()}",
        gate=GovernanceGate(gate),
        execution_id=execution_id,
        project_path=project_path,
        release_plan_id=release_plan_id,
    )


# Default rulesets
def _create_default_planning_ruleset() -> RuleSetAggregate:
    """Factory to create default planning ruleset (avoids forward reference issues)."""
    return RuleSetAggregate(
        ruleset_id="planning-default",
        name="Default Planning Rules",
        gate_type="planning",
        rules=(
            GovernanceRule(id="plan-001", name="Task has description", category="planning", severity="error"),
            GovernanceRule(id="plan-002", name="Task has agent type", category="planning", severity="warning"),
            GovernanceRule(id="plan-003", name="Sprint has goals", category="planning", severity="error"),
        ),
    )


def _create_default_review_ruleset() -> RuleSetAggregate:
    """Factory to create default review ruleset (avoids forward reference issues)."""
    return RuleSetAggregate(
        ruleset_id="review-default",
        name="Default Review Rules",
        gate_type="review",
        rules=(
            GovernanceRule(id="review-001", name="No blocking errors", category="quality", severity="error"),
            GovernanceRule(id="review-002", name="Test coverage met", category="quality", severity="warning"),
        ),
    )


DEFAULT_PLANNING_RULESET = _create_default_planning_ruleset()
DEFAULT_REVIEW_RULESET = _create_default_review_ruleset()


# Alias for backward compatibility
Rule = GovernanceRule

__all__ = [
    "GovernanceGate",
    "GovernanceStatus",
    "GovernanceRule",
    "Rule",  # Backward compatibility alias
    "RuleEvaluation",
    "Finding",
    "GovernanceSession",
    "RuleSetAggregate",
    "create_governance_session",
    "DEFAULT_PLANNING_RULESET",
    "DEFAULT_REVIEW_RULESET",
]
