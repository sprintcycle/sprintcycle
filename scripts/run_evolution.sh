#!/bin/bash
# SprintCycle 自动化进化脚本

set -e

echo "===== SprintCycle 自动化进化 ====="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 请在 SprintCycle 项目根目录运行此脚本"
    exit 1
fi

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 运行进化引擎
echo "🚀 启动进化引擎..."
echo ""

python .cursor/skills/sprint-evolve/evolve.py "$@"

echo ""
echo "===== 进化完成 ====="