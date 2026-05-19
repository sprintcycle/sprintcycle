#!/bin/bash
# SprintCycle Frontend 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}/frontend"

if [ -f "../.env" ]; then
    set -a
    . "../.env"
    set +a
fi

if [ -d "../.venv" ]; then
    source "../.venv/bin/activate"
fi

echo "启动 SprintCycle Frontend..."
echo "   地址: http://localhost:5173"
echo "   按 Ctrl+C 停止"
echo ""

exec npm run dev
