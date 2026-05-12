#!/bin/bash
# SprintCycle Dashboard 启动脚本

set -e

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "启动 SprintCycle Dashboard..."
echo "   地址: http://localhost:8000"
echo "   按 Ctrl+C 停止"
echo ""

exec sprintcycle dashboard
