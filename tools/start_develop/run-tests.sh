#!/bin/bash
# SprintCycle 测试运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "运行 SprintCycle 测试..."
echo ""

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

# 运行测试
exec python -m pytest tests/ -v --tb=short "$@"