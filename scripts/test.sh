#!/bin/bash
# SprintCycle 统一测试入口

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN=".venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    echo "未找到 .venv/bin/python，请先创建虚拟环境后再运行测试。" >&2
    exit 1
fi

exec "$PYTHON_BIN" -m pytest tests/ -v --tb=short "$@"
