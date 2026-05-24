"""Domain Governance Core - 治理核心领域逻辑"""

from .constants import *
from .model_compare import run_model_compare
from .plugin_host import merge_argv_via_plugin
from .yaml_merge import (
    load_merged_governance_data,
    merge_governance_documents,
    resolve_governance_file,
)

__all__ = [
    # constants
    "LINT_IMPORTS",
    "PYPROJECT_TOML",
    "DOCKER_COMPOSE_YML",
    "COMPOSE_YAML",
    "ADR_DIR",
    "REPORT_DIR_DEFAULT",
    "REPORT_FILE_LAST",
    "REPORT_FILE_PLANNING_LAST",
    "GATE_PLANNING",
    "GATE_REVIEW",
    "GOVERNANCE_SPEC_GLOB",
    "GOVERNANCE_SPEC_MARKER",
    "GOVERNANCE_ACCEPTANCE_GLOB",
    "GOVERNANCE_PLANNING_VALIDATE_RELEASE_PLAN",
    "GOVERNANCE_REVIEW_STATIC",
    "GOVERNANCE_REVIEW_IMPORT_LINTER",
    "GOVERNANCE_CHECK_ADR",
    "GOVERNANCE_ADR_GLOB",
    "GOVERNANCE_CHECK_COMPOSE",
    "GOVERNANCE_COMPOSE_SUPPLY_CHAIN",
    "GOVERNANCE_DOWNGRADE_ERRORS_TO_WARNINGS",
    "GOVERNANCE_REPORT_DIR",
    "GOVERNANCE_CLI_EMIT_EVENTS",
    "GOVERNANCE_BLOCK_ON",
    "HITL_ENABLED",
    "HITL_DEFAULT_RISK_LEVEL",
    "RULE_PLANNING_PREFIX",
    "RULE_STATIC_PREFIX",
    "RULE_STATIC_TRUNCATED",
    "RULE_STATIC_ANALYZER",
    "RULE_IMPORT_LINTER_PREFIX",
    "RULE_IMPORT_LINTER_MISSING",
    "RULE_IMPORT_LINTER_CONTRACTS",
    "RULE_IMPORT_LINTER_ERROR",
    "RULE_ADR_PREFIX",
    "RULE_ADR_EMPTY",
    "RULE_COMPOSE_PREFIX",
    "RULE_COMPOSE_MISSING",
    "RULE_QUALITY_SPEC_PREFIX",
    "RULE_QUALITY_SPEC_DEAL",
    "RULE_QUALITY_SPEC_BANDIT",
    "RULE_QUALITY_SPEC_ARCH",
    "STATIC_MAX_RESULTS",
    "STATIC_MAX_DISPLAY",
    "LINT_IMPORTS_TIMEOUT",
    "MESSAGE_MAX_LENGTH",
    "TRUNCATED_SUFFIX",
    "DEFAULT_HITL_RISK_LEVEL",
    "DEFAULT_GOVERNANCE_REPORT_DIR",
    "DEFAULT_EXECUTION_ID",
    "STEP_YAML_REVIEW_CHECKS",
    "STEP_STATIC_ANALYZER",
    "STEP_STATIC_SKIPPED",
    "STEP_IMPORT_LINTER",
    "STEP_IMPORT_LINTER_SKIPPED_NO_BINARY",
    "STEP_IMPORT_LINTER_SKIPPED_NO_PYPROJECT",
    "STEP_IMPORT_LINTER_DISABLED",
    "STEP_ADR_SCAN",
    "STEP_ADR_SCAN_STRICT_GLOB",
    "STEP_ADR_DIR_MISSING",
    "STEP_COMPOSE_HINT",
    "STEP_COMPOSE_SUPPLY_CHAIN",
    "STEP_QUALITY_SPEC_DEAL",
    "STEP_QUALITY_SPEC_BANDIT",
    "STEP_QUALITY_SPEC_ARCH",
    # model_compare
    "run_model_compare",
    # plugin_host
    "merge_argv_via_plugin",
    # yaml_merge
    "load_merged_governance_data",
    "merge_governance_documents",
    "resolve_governance_file",
]


def __getattr__(name):
    if name in ("GovernanceReport", "GovernanceViolation"):
        from .report import GovernanceReport, GovernanceViolation
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
