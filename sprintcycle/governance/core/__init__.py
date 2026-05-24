"""Governance core."""

from .facade import GovernanceFacade, create_governance_facade
from .history import append_history_snapshot, list_history_entries
from .model_compare import run_model_compare
from .plugin_host import merge_argv_via_plugin
from .report import GovernanceReport, GovernanceViolation
from .runner import (
    GovernanceRunner,
    persist_planning_report,
    persist_report,
    run_governance_check_and_persist,
    run_planning_gate_sync,
    run_review_gate_sync,
)
from .yaml_merge import load_merged_governance_data

__all__ = [
    "GovernanceFacade",
    "create_governance_facade",
    "append_history_snapshot",
    "list_history_entries",
    "run_model_compare",
    "merge_argv_via_plugin",
    "GovernanceReport",
    "GovernanceViolation",
    "GovernanceRunner",
    "persist_planning_report",
    "persist_report",
    "run_governance_check_and_persist",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "load_merged_governance_data",
]
