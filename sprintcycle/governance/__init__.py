"""Governance domain package."""

from .core.facade import GovernanceFacade, create_governance_facade
from .core.history import append_history_snapshot, list_history_entries
from .core.model_compare import run_model_compare
from .core.plugin_host import merge_argv_via_plugin
from .core.report import GovernanceReport, GovernanceViolation
from .core.runner import (
    GovernanceRunner,
    persist_planning_report,
    persist_report,
    run_governance_check_and_persist,
    run_planning_gate_sync,
    run_review_gate_sync,
)
from .core.yaml_merge import load_merged_governance_data
from .hitl.facade import HitlFacade, create_hitl_facade
from .hooks.sprint_hooks import GovernanceSprintHooks
from .hooks.task_hooks import GovernanceTaskLifecycleHooks
from .suggestion import (
    Suggestion,
    SuggestionApprovalRecord,
    SuggestionFacade,
    SuggestionImpactScope,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionReviewRecord,
    SuggestionSeverity,
    SuggestionSourceType,
    SuggestionStatus,
    create_suggestion_facade,
)
from .suggestion.analyzer import SuggestionAnalyzer

__all__ = [
    "GovernanceFacade",
    "create_governance_facade",
    "HitlFacade",
    "create_hitl_facade",
    "SuggestionFacade",
    "create_suggestion_facade",
    "SuggestionAnalyzer",
    "Suggestion",
    "SuggestionApprovalRecord",
    "SuggestionImpactScope",
    "SuggestionOverviewResult",
    "SuggestionReviewContext",
    "SuggestionReviewRecord",
    "SuggestionSeverity",
    "SuggestionSourceType",
    "SuggestionStatus",
    "GovernanceReport",
    "GovernanceViolation",
    "GovernanceRunner",
    "persist_report",
    "persist_planning_report",
    "run_governance_check_and_persist",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "append_history_snapshot",
    "list_history_entries",
    "run_model_compare",
    "merge_argv_via_plugin",
    "load_merged_governance_data",
    "GovernanceSprintHooks",
    "GovernanceTaskLifecycleHooks",
]
