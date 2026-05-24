"""Constants for sprint orchestration."""

# Task splitting
TASK_SPLIT_THRESHOLD = 500
MAX_SUBTASKS = 5

# Dependency keyword pairs
DEPENDENCY_KEYWORDS = [
    ("测试", "实现"),
    ("test", "implement"),
    ("verify", "build"),
    ("build", "compile"),
    ("集成", "单元"),
    ("integration", "unit"),
    ("端到端", "模块"),
    ("e2e", "module"),
    ("部署", "构建"),
    ("deploy", "build"),
]

# Action patterns for task splitting
ACTION_PATTERNS = [
    r"实现[^\s，,。]+",
    r"添加[^\s，,。]+",
    r"修改[^\s，,。]+",
    r"修复[^\s，,。]+",
    r"优化[^\s，,。]+",
    r"创建[^\s，,。]+",
]

# Default values
DEFAULT_MAX_PARALLEL = 3
DEFAULT_MAX_VERIFY_FIX_ROUNDS = 3
DEFAULT_CHECKPOINT_INTERVAL = 1

# Agent types
AGENT_TYPE_CODER = "coder"
AGENT_TYPE_IMPLEMENT = "implement"
AGENT_TYPE_TESTER = "tester"
AGENT_TYPE_ARCHITECT = "architect"
AGENT_TYPE_REGRESSION_TESTER = "regression_tester"

# Dry run messages
DRY_RUN_CODER_TEMPLATE = "[dry_run] 完成: {desc}"
DRY_RUN_TESTER_TEMPLATE = "[dry_run] 测试完成: {desc}"
DRY_RUN_ARCHITECT_TEMPLATE = "[dry_run] 架构设计: {desc}"
DRY_RUN_REGRESSION_TESTER_TEMPLATE = "[dry_run] 回归测试完成: {desc}"
