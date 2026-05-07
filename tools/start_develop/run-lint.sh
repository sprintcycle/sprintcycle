#!/bin/bash
# SprintCycle 代码质量检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "运行 SprintCycle 代码质量检查..."
echo ""

# Ruff lint
echo ">>> Ruff (Linting)..."
ruff check sprintcycle/ || true

echo ""

# MyPy 类型检查
echo ">>> MyPy (Type Checking)..."
mypy sprintcycle/ --ignore-missing-imports || true

echo ""
echo "代码检查完成"