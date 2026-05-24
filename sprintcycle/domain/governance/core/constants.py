"""治理模块常量配置。"""

# 工具名称
LINT_IMPORTS = "lint-imports"

# 文件相关
PYPROJECT_TOML = "pyproject.toml"
DOCKER_COMPOSE_YML = "docker-compose.yml"
COMPOSE_YAML = "compose.yaml"
ADR_DIR = "docs/adr"
REPORT_DIR_DEFAULT = ".sprintcycle"
REPORT_FILE_LAST = "governance_last.json"
REPORT_FILE_PLANNING_LAST = "governance_planning_last.json"

# 门禁名称
GATE_PLANNING = "planning"
GATE_REVIEW = "review"

# 治理配置键名
GOVERNANCE_SPEC_GLOB = "governance_spec_glob"
GOVERNANCE_SPEC_MARKER = "governance_spec_marker"
GOVERNANCE_ACCEPTANCE_GLOB = "governance_acceptance_glob"
GOVERNANCE_PLANNING_VALIDATE_RELEASE_PLAN = "governance_planning_validate_release_plan"
GOVERNANCE_REVIEW_STATIC = "governance_review_static"
GOVERNANCE_REVIEW_IMPORT_LINTER = "governance_review_import_linter"
GOVERNANCE_CHECK_ADR = "governance_check_adr"
GOVERNANCE_ADR_GLOB = "governance_adr_glob"
GOVERNANCE_CHECK_COMPOSE = "governance_check_compose"
GOVERNANCE_COMPOSE_SUPPLY_CHAIN = "governance_compose_supply_chain"
GOVERNANCE_DOWNGRADE_ERRORS_TO_WARNINGS = "governance_downgrade_errors_to_warnings"
GOVERNANCE_REPORT_DIR = "governance_report_dir"
GOVERNANCE_CLI_EMIT_EVENTS = "governance_cli_emit_events"
GOVERNANCE_BLOCK_ON = "governance_block_on"
HITL_ENABLED = "hitl_enabled"
HITL_DEFAULT_RISK_LEVEL = "hitl_default_risk_level"

# 规则 ID 前缀
RULE_PLANNING_PREFIX = "planning:"
RULE_STATIC_PREFIX = "static:"
RULE_STATIC_TRUNCATED = "static:truncated"
RULE_STATIC_ANALYZER = "static:analyzer"
RULE_IMPORT_LINTER_PREFIX = "import_linter:"
RULE_IMPORT_LINTER_MISSING = "import_linter:missing"
RULE_IMPORT_LINTER_CONTRACTS = "import_linter:contracts"
RULE_IMPORT_LINTER_ERROR = "import_linter:error"
RULE_ADR_PREFIX = "adr:"
RULE_ADR_EMPTY = "adr:empty"
RULE_COMPOSE_PREFIX = "compose:"
RULE_COMPOSE_MISSING = "compose:missing"
RULE_QUALITY_SPEC_PREFIX = "quality_spec:"
RULE_QUALITY_SPEC_DEAL = "quality_spec:deal"
RULE_QUALITY_SPEC_BANDIT = "quality_spec:bandit"
RULE_QUALITY_SPEC_ARCH = "quality_spec:arch"

# 静态分析配置
STATIC_MAX_RESULTS = 80
STATIC_MAX_DISPLAY = 50

# 超时设置
LINT_IMPORTS_TIMEOUT = 180

# 截断配置
MESSAGE_MAX_LENGTH = 4000
TRUNCATED_SUFFIX = "\n... [truncated]"

# 默认值
DEFAULT_HITL_RISK_LEVEL = "medium"
DEFAULT_GOVERNANCE_REPORT_DIR = ".sprintcycle"

# 执行 ID 默认值
DEFAULT_EXECUTION_ID = "__governance__"

# 步骤名称
STEP_YAML_REVIEW_CHECKS = "yaml_review_checks"
STEP_STATIC_ANALYZER = "static_analyzer"
STEP_STATIC_SKIPPED = "static_skipped"
STEP_IMPORT_LINTER = "import_linter"
STEP_IMPORT_LINTER_SKIPPED_NO_BINARY = "import_linter_skipped_no_binary"
STEP_IMPORT_LINTER_SKIPPED_NO_PYPROJECT = "import_linter_skipped_no_pyproject"
STEP_IMPORT_LINTER_DISABLED = "import_linter_disabled"
STEP_ADR_SCAN = "adr_scan"
STEP_ADR_SCAN_STRICT_GLOB = "adr_scan_strict_glob"
STEP_ADR_DIR_MISSING = "adr_dir_missing"
STEP_COMPOSE_HINT = "compose_hint"
STEP_COMPOSE_SUPPLY_CHAIN = "compose_supply_chain"
STEP_QUALITY_SPEC_DEAL = "quality_spec_deal"
STEP_QUALITY_SPEC_BANDIT = "quality_spec_bandit"
STEP_QUALITY_SPEC_ARCH = "quality_spec_arch"
