#!/bin/bash
# SprintCycle MCP Server 启动脚本

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "启动 SprintCycle MCP Server (stdio 模式)..."
echo "   按 Ctrl+C 停止"
echo ""

exec sprintcycle mcp