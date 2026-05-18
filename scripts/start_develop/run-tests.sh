#!/bin/bash
# SprintCycle 测试运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

echo "运行 SprintCycle 测试..."
echo ""

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

PYTHON_BIN=".venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

# 运行测试
exec "$PYTHON_BIN" -m pytest tests/ -v --tb=short "$@"
