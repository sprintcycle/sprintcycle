#!/bin/bash
# SprintCycle 开发环境激活脚本
# 使用方法: source activate.sh

# 获取项目根目录（脚本在 tools/start_develop/ 下）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "错误: .venv 目录不存在，请先运行 dev-setup.sh"
    return 1 2>/dev/null || exit 1
fi

# 加载环境变量
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SprintCycle 开发环境已激活                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  工作目录: $(pwd)"
echo "  Python: $(python --version)"
echo ""
echo "📋 可用命令:"
echo "  sprintcycle --help    - 查看 CLI 帮助"
echo "  sprintcycle init      - 初始化项目"
echo "  sprintcycle run       - 运行任务"
echo ""
echo "📝 便捷脚本:"
echo "  ./run-dashboard.sh    - 启动 Dashboard"
echo "  ./run-mcp.sh          - 启动 MCP Server"
echo "  ./run-tests.sh        - 运行测试"
echo "  ./run-lint.sh         - 代码检查"
echo ""
echo "  deactivate            - 退出虚拟环境"
echo ""
