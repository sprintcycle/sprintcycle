"""Governance core - Domain layer."""

from .facade import GovernanceFacade, create_governance_facade
from .history import append_history_snapshot, list_history_entries
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
    "GovernanceRunner",
    "persist_report",
    "persist_planning_report",
    "run_governance_check_and_persist",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "append_history_snapshot",
    "list_history_entries",
    "load_merged_governance_data",
]
