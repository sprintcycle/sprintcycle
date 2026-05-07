#!/bin/bash
# ==============================================================================
# SprintCycle 开发环境部署脚本 v2.0
# 支持: macOS / Linux (Ubuntu/Debian/CentOS/Fedora/Arch)
# ==============================================================================

set -euo pipefail

# ==============================================================================
# 全局配置
# ==============================================================================

VERSION="2.0.0"
PYTHON_MIN_VERSION="3.11"

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# 命令行参数
SKIP_SYSTEM_DEPS=false
FORCE_REINSTALL=false

# ==============================================================================
# 颜色输出
# ==============================================================================

if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4); CYAN=$(tput setaf 6); BOLD=$(tput bold); RESET=$(tput sgr0)
else
    RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; BOLD=""; RESET=""
fi

log_info() { echo "${BLUE}[INFO]${RESET} $1"; }
log_ok() { echo "${GREEN}[OK]${RESET} $1"; }
log_warn() { echo "${YELLOW}[WARN]${RESET} $1"; }
log_fail() { echo "${RED}[FAIL]${RESET} $1"; }
section() { echo ""; echo "${BOLD}${BLUE}==== $1 ====${RESET}"; }

# ==============================================================================
# 辅助函数
# ==============================================================================

command_exists() { command -v "$1" >/dev/null 2>&1; }

# ==============================================================================
# 阶段 1: 系统检测
# ==============================================================================

phase_system_detection() {
    section "阶段 1: 系统检测"
    
    OS_TYPE=$(uname -s)
    case "${OS_TYPE}" in
        Linux*)  OS_TYPE="linux" ;;
        Darwin*) OS_TYPE="mac" ;;
        *)       log_fail "不支持的操作系统: ${OS_TYPE}"; exit 1 ;;
    esac
    log_info "操作系统: ${OS_TYPE} ($(uname -m))"
    
    # 检测包管理器
    if [ "${OS_TYPE}" = "mac" ]; then
        if command_exists brew; then
            PKG_MANAGER="brew"
            log_info "包管理器: Homebrew"
        else
            log_fail "请先安装 Homebrew: https://brew.sh"
            exit 1
        fi
    else
        if command_exists apt-get; then
            PKG_MANAGER="apt"
        elif command_exists dnf; then
            PKG_MANAGER="dnf"
        elif command_exists yum; then
            PKG_MANAGER="yum"
        elif command_exists pacman; then
            PKG_MANAGER="pacman"
        else
            PKG_MANAGER="none"
        fi
        log_info "包管理器: ${PKG_MANAGER:-none}"
    fi
    
    # 检查 Python 版本
    if command_exists python3; then
        local py_ver
        py_ver=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Python: ${py_ver}"
        if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
            log_warn "Python >= 3.11 是必需的，当前 ${py_ver}"
        fi
    else
        log_warn "Python3 未安装"
    fi
}

# ==============================================================================
# 阶段 2: 安装系统依赖
# ==============================================================================

phase_install_system_deps() {
    if [ "${SKIP_SYSTEM_DEPS}" = true ]; then
        log_info "跳过系统依赖安装 (--skip-system-deps)"
        return 0
    fi
    
    section "阶段 2: 安装系统依赖"
    
    local -a deps=()
    
    if [ "${OS_TYPE}" = "mac" ]; then
        if ! command_exists git; then deps+=("git"); fi
        if ! command_exists python3@3.12 2>/dev/null && ! command_exists python3; then
            deps+=("python@3.12")
        fi
        if [ ${#deps[@]} -gt 0 ]; then
            log_info "安装: ${deps[*]}"
            brew install "${deps[@]}"
        fi
    else
        case "${PKG_MANAGER}" in
            apt)
                if ! command_exists git; then deps+=("git"); fi
                if ! command_exists python3; then deps+=("python3"); fi
                if ! command_exists python3-venv; then deps+=("python3-venv"); fi
                if ! command_exists build-essential; then deps+=("build-essential"); fi
                if [ ${#deps[@]} -gt 0 ]; then
                    log_info "安装: ${deps[*]}"
                    sudo apt-get update
                    sudo apt-get install -y "${deps[@]}"
                fi
                ;;
            dnf)
                if ! command_exists git; then deps+=("git"); fi
                if ! command_exists python3; then deps+=("python3"); fi
                if ! command_exists python3-pip; then deps+=("python3-pip"); fi
                if ! command_exists python3-devel; then deps+=("python3-devel"); fi
                if [ ${#deps[@]} -gt 0 ]; then
                    sudo dnf install -y "${deps[@]}"
                fi
                ;;
            yum)
                if ! command_exists git; then deps+=("git"); fi
                if ! command_exists python3; then deps+=("python3"); fi
                if ! command_exists python3-pip; then deps+=("python3-pip"); fi
                if ! command_exists python3-devel; then deps+=("python3-devel"); fi
                if [ ${#deps[@]} -gt 0 ]; then
                    sudo yum install -y "${deps[@]}"
                fi
                ;;
            pacman)
                if ! command_exists git; then deps+=("git"); fi
                if ! command_exists python; then deps+=("python"); fi
                if ! command_exists base-devel; then deps+=("base-devel"); fi
                if [ ${#deps[@]} -gt 0 ]; then
                    sudo pacman -Sy --noconfirm "${deps[@]}"
                fi
                ;;
        esac
    fi
    
    log_ok "系统依赖安装完成"
}

# ==============================================================================
# 阶段 3: Python 环境
# ==============================================================================

phase_python_env() {
    section "阶段 3: Python 环境"
    
    if [ -d ".venv" ] && [ "${FORCE_REINSTALL}" != true ]; then
        log_info ".venv 已存在，使用现有环境"
    else
        log_info "创建虚拟环境..."
        rm -rf .venv
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    log_info "升级 pip..."
    pip install --upgrade pip setuptools wheel -q
    
    log_ok "Python 环境就绪"
}

# ==============================================================================
# 阶段 4: 安装 Python 依赖
# ==============================================================================

phase_install_python_deps() {
    section "阶段 4: 安装 Python 依赖"
    
    source .venv/bin/activate
    
    log_info "安装 SprintCycle (开发模式)..."
    pip install -e ".[full,dev,mcp-sse,mutation]" -q
    
    log_ok "Python 依赖安装完成"
}

# ==============================================================================
# 阶段 5: 环境变量配置
# ==============================================================================

phase_env_config() {
    section "阶段 5: 配置环境变量"
    
    if [ -f ".env" ] && [ "${FORCE_REINSTALL}" != true ]; then
        log_info ".env 文件已存在"
    else
        cat > ".env" << 'ENVEOF'
# ==============================================================================
# SprintCycle 环境配置
# ==============================================================================

# ===== LLM API 配置 =====
# 支持: OpenAI, Anthropic, DeepSeek, 豆包, 通义千问 等

# OpenAI (推荐)
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# DeepSeek
# DEEPSEEK_API_KEY=
# DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# ===== SprintCycle 运行时配置 =====
SPRINTCYCLE_WORKSPACE=./workspace
SPRINTCYCLE_LOG_LEVEL=INFO
SPRINTCYCLE_MAX_ITERATIONS=10
SPRINTCYCLE_CACHE_DIR=./cache

# ===== MCP Server 配置 =====
MCP_TRANSPORT=stdio

# ===== LLM 回退配置 =====
LLM_FALLBACK_ENABLED=true
LLM_PRIMARY_PROVIDER=openai
ENVEOF
        log_warn "请编辑 .env 文件，填入你的 API Key"
    fi
    
    log_ok "环境变量配置完成"
}

# ==============================================================================
# 阶段 6: 创建便捷脚本
# ==============================================================================

phase_create_scripts() {
    section "阶段 6: 创建便捷脚本"
    
    local tools_dir="${PROJECT_ROOT}/tools/start_develop"
    
    # Dashboard 启动脚本
    cat > "${tools_dir}/run-dashboard.sh" << 'SCRIPT1'
#!/bin/bash
# SprintCycle Dashboard 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "启动 SprintCycle Dashboard..."
echo "   地址: http://localhost:8000"
echo "   按 Ctrl+C 停止"
echo ""

exec sprintcycle dashboard
SCRIPT1
    chmod +x "${tools_dir}/run-dashboard.sh"
    log_ok "创建 run-dashboard.sh"
    
    # MCP Server 启动脚本
    cat > "${tools_dir}/run-mcp.sh" << 'SCRIPT2'
#!/bin/bash
# SprintCycle MCP Server 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "启动 SprintCycle MCP Server..."
echo "   模式: stdio (默认)"
echo "   按 Ctrl+C 停止"
echo ""

exec sprintcycle serve
SCRIPT2
    chmod +x "${tools_dir}/run-mcp.sh"
    log_ok "创建 run-mcp.sh"
    
    # 测试运行脚本
    cat > "${tools_dir}/run-tests.sh" << 'SCRIPT3'
#!/bin/bash
# SprintCycle 测试运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "运行 SprintCycle 测试..."
echo ""

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs 2>/dev/null || true)
fi

exec python -m pytest tests/ -v --tb=short "$@"
SCRIPT3
    chmod +x "${tools_dir}/run-tests.sh"
    log_ok "创建 run-tests.sh"
    
    # Lint 运行脚本
    cat > "${tools_dir}/run-lint.sh" << 'SCRIPT4'
#!/bin/bash
# SprintCycle 代码质量检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "运行 SprintCycle 代码质量检查..."
echo ""

echo ">>> Ruff (Linting)..."
ruff check sprintcycle/ || true

echo ""

echo ">>> MyPy (Type Checking)..."
mypy sprintcycle/ --ignore-missing-imports || true

echo ""
echo "代码检查完成"
SCRIPT4
    chmod +x "${tools_dir}/run-lint.sh"
    log_ok "创建 run-lint.sh"
    
    # 环境激活脚本
    cat > "${tools_dir}/activate.sh" << 'SCRIPT5'
#!/bin/bash
# SprintCycle 开发环境激活脚本
# 使用方法: source activate.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "错误: .venv 目录不存在，请先运行 dev-setup.sh"
    return 1 2>/dev/null || exit 1
fi

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
SCRIPT5
    chmod +x "${tools_dir}/activate.sh"
    log_ok "创建 activate.sh"
    
    log_ok "便捷脚本创建完成"
}

# ==============================================================================
# 阶段 7: 验证安装
# ==============================================================================

phase_verify() {
    section "阶段 7: 验证安装"
    
    source .venv/bin/activate
    
    echo -n "  Python: "
    if python --version >/dev/null 2>&1; then
        log_ok "$(python --version)"
    else
        log_fail "Python 不可用"
    fi
    
    echo "  检查关键依赖..."
    local deps=("pydantic" "litellm" "pytest" "ruff" "mypy")
    for dep in "${deps[@]}"; do
        echo -n "    ${dep}: "
        if python -c "import ${dep}" 2>/dev/null; then
            log_ok "已安装"
        else
            log_fail "未安装"
        fi
    done
    
    echo -n "  sprintcycle CLI: "
    if command -v sprintcycle >/dev/null 2>&1; then
        log_ok "可用"
    else
        log_fail "不可用"
    fi
    
    log_ok "验证完成"
}

# ==============================================================================
# 帮助信息
# ==============================================================================

show_help() {
    cat << HELP
SprintCycle 开发环境部署脚本 v${VERSION}

用法: ./dev-setup.sh [选项]

选项:
  --skip-system-deps     跳过系统依赖安装
  --force                强制重新安装
  -h, --help             显示此帮助

示例:
  ./dev-setup.sh                    # 完整安装
  ./dev-setup.sh --skip-system-deps
HELP
}

# ==============================================================================
# 参数解析
# ==============================================================================

while [ $# -gt 0 ]; do
    case "$1" in
        --skip-system-deps) SKIP_SYSTEM_DEPS=true; shift ;;
        --force|-f) FORCE_REINSTALL=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) log_fail "未知参数: $1"; show_help; exit 1 ;;
    esac
done

# ==============================================================================
# 主函数
# ==============================================================================

main() {
    echo ""
    echo "    _____ _____ _____ _____ _____ _____ _____ _____ _____ "
    echo "   |   __|   __|     |  _  |  _  |   __| __  |  _  |   __|"
    echo "   |__   |   __| | | |   __|   __|   __|    -|     |   __|"
    echo "   |_____|_____|_|_|_|__|  |__|  |_____|__|__|__|__|_____|"
    echo ""
    echo "                开发环境部署脚本 v${VERSION}"
    echo ""
    
    phase_system_detection
    phase_install_system_deps
    phase_python_env
    phase_install_python_deps
    phase_env_config
    phase_create_scripts
    phase_verify
    
    echo ""
    echo "${GREEN}╔══════════════════════════════════════════════════════════════╗${RESET}"
    echo "${GREEN}║                  部署完成！                                ║${RESET}"
    echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo "${CYAN}🚀 下一步:${RESET}"
    echo "  1. ${YELLOW}编辑 .env 文件，填入你的 API Key${RESET}"
    echo "  2. ${GREEN}source activate.sh${RESET} 激活开发环境"
    echo "  3. ${CYAN}sprintcycle --help${RESET} 查看所有命令"
    echo ""
    echo "${BOLD}📋 便捷脚本:${RESET}"
    echo "  ./run-dashboard.sh   - 启动 Dashboard"
    echo "  ./run-mcp.sh        - 启动 MCP Server"
    echo "  ./run-tests.sh      - 运行测试"
    echo "  ./run-lint.sh       - 代码检查"
    echo ""
    echo "${BOLD}📚 文档:${RESET}"
    echo "  DEVELOPMENT_GUIDE.md - 完整开发指南"
    echo "  DEPLOY_CHECKLIST.md  - 部署检查清单"
    echo ""
}

main "$@"
