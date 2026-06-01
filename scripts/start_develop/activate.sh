#!/bin/bash
# SprintCycle 开发环境激活脚本
# 使用方法: source activate.sh 或 . activate.sh

# 获取脚本所在目录（支持各种调用方式）
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "$0" ]; then
    SCRIPT_PATH="$0"
else
    echo "错误: 无法确定脚本路径"
    return 1 2>/dev/null || exit 1
fi

# 获取绝对路径
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 切换到项目根目录
cd "${PROJECT_ROOT}" || {
    echo "错误: 无法切换到项目根目录: ${PROJECT_ROOT}"
    return 1 2>/dev/null || exit 1
}

# 检查虚拟环境是否存在
VENV_DIR="${PROJECT_ROOT}/.venv"
if [ -d "${VENV_DIR}" ]; then
    # 激活虚拟环境
    source "${VENV_DIR}/bin/activate"
else
    echo "错误: .venv 目录不存在 (${VENV_DIR})"
    echo "请先运行: cd ${PROJECT_ROOT} && bash scripts/start_develop/dev-setup.sh"
    return 1 2>/dev/null || exit 1
fi

# 加载环境变量
ENV_FILE="${PROJECT_ROOT}/.env"
if [ -f "${ENV_FILE}" ]; then
    set -a
    source "${ENV_FILE}"
    set +a
else
    echo "提示: .env 文件不存在，跳过环境变量加载"
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
echo "  ./scripts/start_develop/run-dashboard.sh    - 启动 Dashboard"
echo "  ./scripts/start_develop/run-mcp.sh          - 启动 MCP Server"
echo "  ./scripts/start_develop/run-tests.sh        - 运行测试"
echo "  ./scripts/start_develop/run-lint.sh         - 代码检查"
echo ""
echo "  deactivate            - 退出虚拟环境"
echo ""