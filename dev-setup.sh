#!/bin/bash
# ==============================================================================
# SprintCycle 一键开发环境部署脚本 v2.0
# 支持: macOS (Intel/Apple Silicon) / Linux (Ubuntu/Debian/CentOS/Fedora/Arch)
# 远程一键部署: curl -fsSL https://raw.githubusercontent.com/sprintcycle/sprintcycle/main/dev-setup.sh | bash
# ==============================================================================

set -euo pipefail
# 兼容 bash 3.2+ (macOS 默认)
if [ -n "${BASH_VERSION:-}" ]; then
    set +o posix
fi

# ==============================================================================
# 全局配置与变量
# ==============================================================================

VERSION="2.0.0"
PROJECT_NAME="SprintCycle"
REPO_URL="git@github.com:sprintcycle/sprintcycle.git"
REPO_HTTPS_URL="https://github.com/sprintcycle/sprintcycle.git"
PYTHON_MIN_VERSION="3.10"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 命令行参数默认值
SKIP_SYSTEM_DEPS=false
SKIP_NODE=false
PYTHON_VERSION=""
GIT_BRANCH="main"
FORCE_REINSTALL=false
DRY_RUN=false

# 检测到的环境信息
OS_TYPE=""
OS_ARCH=""
DISTRO=""
DISTRO_VERSION=""
PKG_MANAGER=""
SUDO_CMD=""

# 状态跟踪
declare -a FAILED_STEPS=()
declare -a WARNED_STEPS=()
STEP_STATUS="OK"

# ==============================================================================
# 颜色输出定义 (兼容不支持颜色的终端)
# ==============================================================================

# 检测终端是否支持颜色
if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    COLOR_RED=$(tput setaf 1)
    COLOR_GREEN=$(tput setaf 2)
    COLOR_YELLOW=$(tput setaf 3)
    COLOR_BLUE=$(tput setaf 4)
    COLOR_CYAN=$(tput setaf 6)
    COLOR_BOLD=$(tput bold)
    COLOR_RESET=$(tput sgr0)
else
    COLOR_RED=""
    COLOR_GREEN=""
    COLOR_YELLOW=""
    COLOR_BLUE=""
    COLOR_CYAN=""
    COLOR_BOLD=""
    COLOR_RESET=""
fi

# ==============================================================================
# 辅助函数
# ==============================================================================

# 打印消息
log_info() { echo "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"; }
log_success() { echo "${COLOR_GREEN}[OK]${COLOR_RESET} $1"; }
log_warning() { echo "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"; WARNED_STEPS+=("$1"); }
log_error() { echo "${COLOR_RED}[FAIL]${COLOR_RESET} $1"; FAILED_STEPS+=("$1"); STEP_STATUS="FAIL"; }
log_skip() { echo "${COLOR_CYAN}[SKIP]${COLOR_RESET} $1"; }
log_section() { echo ""; echo "${COLOR_BOLD}${COLOR_BLUE}==== $1 ====${COLOR_RESET}"; }

# 打印 ASCII Art Banner
print_banner() {
    cat << 'EOF'

${COLOR_BOLD}${COLOR_GREEN}
    _____ _____ _____ _____ _____ _____ _____ _____ _____ 
   |   __|   __|     |  _  |  _  |   __| __  |  _  |   __|
   |__   |   __| | | |   __|   __|   __|    -|     |   __|
   |_____|_____|_|_|_|__|  |__|  |_____|__|__|__|__|_____|
${COLOR_RESET}
${COLOR_CYAN}                开发环境一键部署脚本 v${VERSION}
${COLOR_RESET}
EOF
}

# 检查命令是否存在
command_exists() {
    command -v "$1" &>/dev/null
}

# 版本比较 (返回 0 表示 $1 >= $2)
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# 获取命令版本
get_version() {
    if [ $# -eq 1 ]; then
        case "$1" in
            python3|python)
                "$1" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "未找到"
                ;;
            git|node|npm)
                "$1" --version 2>&1 | head -n1 | sed 's/.*\([0-9]\+\(\.[0-9]\+\)*\).*/\1/'
                ;;
            *)
                "$1" --version 2>&1 | head -n1
                ;;
        esac
    fi
}

# 确认操作
confirm() {
    local prompt="${1:-确认继续？}"
    local default="${2:-N}"
    
    if [ "${FORCE_REINSTALL}" = true ]; then
        return 0
    fi
    
    if [ "${DRY_RUN}" = true ]; then
        log_info "[DRY-RUN] 会执行: $prompt"
        return 0
    fi
    
    local yn
    read -r -p "${prompt} [${default}/y/N] " yn || return 1
    case "${yn}" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# ==============================================================================
# 阶段 1: 系统检测与准备
# ==============================================================================

phase_system_detection() {
    log_section "阶段 1: 系统检测与准备"
    
    # 检测操作系统
    local os
    os="$(uname -s)"
    case "${os}" in
        Linux*)     OS_TYPE="linux" ;;
        Darwin*)    OS_TYPE="mac" ;;
        *)          OS_TYPE="unknown" ;;
    esac
    log_info "操作系统: ${os} ($(uname -m))"
    OS_ARCH="$(uname -m)"
    
    # 检测 Linux 发行版
    if [ "${OS_TYPE}" = "linux" ]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO="${ID:-unknown}"
            DISTRO_VERSION="${VERSION_ID:-}"
            log_info "Linux 发行版: ${DISTRO} ${DISTRO_VERSION}"
        elif command_exists lsb_release; then
            DISTRO="$(lsb_release -si 2>/dev/null | tr '[:upper:]' '[:lower:]')" || DISTRO="unknown"
            log_info "Linux 发行版: ${DISTRO}"
        else
            DISTRO="unknown"
            log_warning "无法检测 Linux 发行版"
        fi
    fi
    
    # 检测是否需要 sudo
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        SUDO_CMD=""
        log_info "已以 root 权限运行"
    elif command_exists sudo && sudo -n true 2>/dev/null; then
        SUDO_CMD="sudo"
        log_info "将使用 sudo 安装系统依赖"
    else
        SUDO_CMD=""
        log_info "当前用户无需 sudo 或 sudo 不可用"
    fi
    
    # 检测包管理器
    if [ "${OS_TYPE}" = "mac" ]; then
        if command_exists brew; then
            PKG_MANAGER="brew"
            log_info "包管理器: Homebrew ($(brew --version | head -n1))"
        else
            PKG_MANAGER="none"
            log_warning "未检测到 Homebrew"
        fi
    elif [ "${OS_TYPE}" = "linux" ]; then
        if command_exists apt-get; then
            PKG_MANAGER="apt"
            log_info "包管理器: apt"
        elif command_exists dnf; then
            PKG_MANAGER="dnf"
            log_info "包管理器: dnf"
        elif command_exists yum; then
            PKG_MANAGER="yum"
            log_info "包管理器: yum"
        elif command_exists pacman; then
            PKG_MANAGER="pacman"
            log_info "包管理器: pacman (Arch)"
        else
            PKG_MANAGER="none"
            log_warning "未检测到包管理器"
        fi
    fi
    
    # 检测已有工具版本
    log_info "检测已有工具版本..."
    if command_exists git; then
        log_info "  Git: $(get_version git)"
    else
        log_warning "  Git: 未安装"
    fi
    
    if command_exists python3; then
        local py_ver
        py_ver="$(get_version python3)"
        log_info "  Python3: ${py_ver}"
        if ! version_ge "${py_ver}" "${PYTHON_MIN_VERSION}"; then
            log_warning "Python3 版本低于 ${PYTHON_MIN_VERSION}，需要升级"
        fi
    else
        log_warning "  Python3: 未安装"
    fi
    
    if command_exists node; then
        log_info "  Node.js: $(get_version node)"
    else
        log_info "  Node.js: 未安装 (可选)"
    fi
}

# ==============================================================================
# 阶段 2: 系统依赖安装
# ==============================================================================

phase_install_system_deps() {
    if [ "${SKIP_SYSTEM_DEPS}" = true ]; then
        log_skip "跳过系统依赖安装 (--skip-system-deps)"
        return 0
    fi
    
    log_section "阶段 2: 安装系统依赖"
    
    local install_status=0
    
    # macOS
    if [ "${OS_TYPE}" = "mac" ]; then
        if [ "${PKG_MANAGER}" != "brew" ]; then
            echo ""
            echo "========================================"
            echo "  Homebrew 未安装，请先安装："
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "========================================"
            log_error "Homebrew 未安装"
            return 1
        fi
        
        log_info "通过 Homebrew 安装系统依赖..."
        
        if ! command_exists git; then
            log_info "安装 Git..."
            brew install git || { log_error "Git 安装失败"; return 1; }
        else
            log_skip "Git 已安装"
        fi
        
        local py_ver
        py_ver="$(get_version python3 2>/dev/null || echo "0")"
        if ! version_ge "${py_ver}" "${PYTHON_MIN_VERSION}"; then
            log_info "安装 Python 3.12..."
            brew install python@3.12 || { log_error "Python 安装失败"; return 1; }
        else
            log_skip "Python ${py_ver} 已安装"
        fi
    
    # Linux
    elif [ "${OS_TYPE}" = "linux" ]; then
        case "${DISTRO}" in
            ubuntu|debian|linuxmint|pop)
                log_info "通过 apt 安装系统依赖..."
                ${SUDO_CMD} apt-get update -qq || log_warning "apt-get update 失败"
                
                local packages=("git" "curl" "build-essential" "libssl-dev" "zlib1g-dev")
                
                if ! command_exists python3; then
                    packages+=("python3" "python3-pip" "python3-venv")
                else
                    local py_ver
                    py_ver="$(get_version python3)"
                    if ! version_ge "${py_ver}" "${PYTHON_MIN_VERSION}"; then
                        log_info "系统 Python 版本过低，添加 deadsnakes PPA..."
                        ${SUDO_CMD} apt-get install -y -qq software-properties-common
                        ${SUDO_CMD} add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
                        packages+=("python3.12" "python3.12-venv" "python3.12-dev")
                    fi
                fi
                
                log_info "安装包: ${packages[*]}"
                ${SUDO_CMD} apt-get install -y -qq "${packages[@]}" || { log_error "apt-get install 失败"; return 1; }
                ;;
                
            centos|rhel|rocky|almalinux)
                log_info "通过 yum 安装系统依赖..."
                ${SUDO_CMD} yum install -y -q epel-release || true
                ${SUDO_CMD} yum groupinstall -y -q "Development Tools" || true
                
                local packages=("git" "curl" "openssl-devel" "zlib-devel")
                
                if ! command_exists python3; then
                    packages+=("python3" "python3-pip" "python3-devel")
                fi
                
                log_info "安装包: ${packages[*]}"
                ${SUDO_CMD} yum install -y -q "${packages[@]}" || { log_error "yum install 失败"; return 1; }
                ;;
                
            fedora)
                log_info "通过 dnf 安装系统依赖..."
                local packages=("git" "curl" "openssl-devel" "zlib-devel" "python3" "python3-pip" "python3-devel")
                log_info "安装包: ${packages[*]}"
                ${SUDO_CMD} dnf install -y -q "${packages[@]}" || { log_error "dnf install 失败"; return 1; }
                ;;
                
            arch|manjaro|endeavouros)
                log_info "通过 pacman 安装系统依赖..."
                local packages=("git" "curl" "base-devel" "openssl" "zlib" "python" "python-pip")
                log_info "安装包: ${packages[*]}"
                ${SUDO_CMD} pacman -Sy --noconfirm "${packages[@]}" || { log_error "pacman install 失败"; return 1; }
                ;;
                
            *)
                log_error "不支持的发行版: ${DISTRO}"
                return 1
                ;;
        esac
    else
        log_error "不支持的操作系统: ${OS_TYPE}"
        return 1
    fi
    
    # 安装 Node.js (可选)
    if [ "${SKIP_NODE}" != true ] && ! command_exists node; then
        log_info "安装 Node.js..."
        if [ "${OS_TYPE}" = "mac" ] && [ "${PKG_MANAGER}" = "brew" ]; then
            brew install node || log_warning "Homebrew 安装 Node.js 失败"
        elif [ "${OS_TYPE}" = "linux" ]; then
            if command_exists curl; then
                curl -fsSL "https://deb.nodesource.com/setup_lts.x" | ${SUDO_CMD} bash - || log_warning "NodeSource 安装失败"
                ${SUDO_CMD} apt-get install -y -qq nodejs || log_warning "Node.js 安装失败"
            fi
        fi
    fi
    
    return 0
}

# ==============================================================================
# 阶段 3: 项目克隆/更新
# ==============================================================================

phase_project_setup() {
    log_section "阶段 3: 项目代码准备"
    
    local is_sprintcycle_repo=false
    
    if [ -d ".git" ]; then
        local remote_url
        remote_url="$(git remote get-url origin 2>/dev/null || echo "")"
        if echo "${remote_url}" | grep -q "sprintcycle"; then
            is_sprintcycle_repo=true
        fi
    fi
    
    if [ "${is_sprintcycle_repo}" = true ]; then
        log_info "当前已是 SprintCycle 仓库"
        
        local current_branch
        current_branch="$(git branch --show-current 2>/dev/null || echo "")"
        log_info "当前分支: ${current_branch:-unknown}"
        
        if confirm "是否拉取最新代码？"; then
            log_info "拉取最新代码..."
            git fetch origin
            git checkout "${GIT_BRANCH}" || git checkout main
            git pull origin "${GIT_BRANCH:-main}" || log_warning "拉取代码失败"
        else
            log_skip "跳过代码更新"
        fi
    else
        log_info "克隆 SprintCycle 仓库..."
        
        local clone_url="${REPO_HTTPS_URL}"
        if command_exists git && ssh -T -o StrictHostKeyChecking=no git@github.com 2>&1 | grep -q "successfully"; then
            clone_url="${REPO_URL}"
            log_info "检测到 SSH，将使用 SSH 克隆"
        fi
        
        if [ -d "sprintcycle" ]; then
            log_warning "sprintcycle 目录已存在，将合并更新"
            cd sprintcycle
            git pull origin "${GIT_BRANCH}" || log_warning "合并失败"
        else
            git clone -b "${GIT_BRANCH}" "${clone_url}" sprintcycle_temp
            if [ -d "sprintcycle_temp" ]; then
                mv sprintcycle_temp sprintcycle
                cd sprintcycle
            else
                log_error "克隆失败"
                return 1
            fi
        fi
    fi
    
    SCRIPT_DIR="$(pwd)"
    
    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml 不存在，可能不是 SprintCycle 项目"
        return 1
    fi
    
    log_success "项目准备完成: $(pwd)"
    return 0
}

# ==============================================================================
# 阶段 4: Python 环境配置
# ==============================================================================

phase_python_env() {
    log_section "阶段 4: 配置 Python 环境"
    
    local python_cmd="python3"
    if command_exists python3.12; then
        python_cmd="python3.12"
    elif command_exists python3.11; then
        python_cmd="python3.11"
    elif command_exists python3.10; then
        python_cmd="python3.10"
    elif ! command_exists python3; then
        log_error "Python3 未安装"
        return 1
    fi
    
    local py_ver
    py_ver="$(${python_cmd} -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
    log_info "使用 Python: ${python_cmd} (${py_ver})"
    
    local venv_path=".venv"
    if [ -d "${venv_path}" ]; then
        if [ "${FORCE_REINSTALL}" = true ]; then
            log_info "强制重建虚拟环境..."
            rm -rf "${venv_path}"
        else
            log_skip "虚拟环境已存在 (${venv_path})"
            if confirm "是否重建虚拟环境？"; then
                log_info "重建虚拟环境..."
                rm -rf "${venv_path}"
            fi
        fi
    fi
    
    if [ ! -d "${venv_path}" ]; then
        log_info "创建虚拟环境..."
        ${python_cmd} -m venv "${venv_path}" || { log_error "虚拟环境创建失败"; return 1; }
    fi
    
    log_info "激活虚拟环境..."
    log_info "升级 pip..."
    "${venv_path}/bin/pip" install --upgrade pip setuptools wheel || { log_error "pip 升级失败"; return 1; }
    
    log_success "Python 环境配置完成"
    return 0
}

# ==============================================================================
# 阶段 5: 安装 Python 依赖
# ==============================================================================

phase_install_python_deps() {
    log_section "阶段 5: 安装 Python 依赖"
    
    local venv_path=".venv"
    local pip_cmd="${venv_path}/bin/pip"
    
    log_info "安装 SprintCycle 依赖 (editable + dev + mcp-sse)..."
    ${pip_cmd} install -e ".[dev,mcp-sse]" || { log_error "依赖安装失败"; return 1; }
    
    if [ -f "requirements.txt" ]; then
        log_info "安装额外依赖 (requirements.txt)..."
        ${pip_cmd} install -r requirements.txt || log_warning "requirements.txt 安装时有警告"
    fi
    
    log_info "安装开发辅助工具..."
    ${pip_cmd} install httpx pytest-cov 2>/dev/null || true
    
    log_success "Python 依赖安装完成"
    return 0
}

# ==============================================================================
# 阶段 6: 环境变量配置
# ==============================================================================

phase_env_config() {
    log_section "阶段 6: 配置环境变量"
    
    local env_file=".env"
    
    if [ -f "${env_file}" ]; then
        log_skip ".env 文件已存在"
        if confirm "是否重新生成 .env 文件（将覆盖现有文件）？"; then
            log_info "重新生成 .env 文件..."
            generate_env_template
        fi
    else
        log_info "创建 .env 文件..."
        generate_env_template
    fi
    
    log_success "环境变量配置完成"
    return 0
}

generate_env_template() {
    cat > ".env" << 'ENVEOF'
# ==============================================================================
# SprintCycle 环境配置
# 请根据你的实际情况填写以下配置
# ==============================================================================

# ===== LLM API 配置 =====
# 支持的提供商: OpenAI, Anthropic, DeepSeek, 豆包, 通义千问 等

# OpenAI (推荐)
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# DeepSeek
DEEPSEEK_API_KEY=
# DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# ===== SprintCycle 运行时配置 =====
SPRINTCYCLE_WORKSPACE=./workspace
SPRINTCYCLE_LOG_LEVEL=INFO
SPRINTCYCLE_MAX_ITERATIONS=10
SPRINTCYCLE_CACHE_DIR=./cache

# ===== MCP Server 配置 =====
# stdio 传输 (默认，用于本地 CLI)
MCP_TRANSPORT=stdio

# SSE 传输 (用于远程访问，可选)
# MCP_SERVER_HOST=0.0.0.0
# MCP_SERVER_PORT=8765

# ===== LLM 回退配置 =====
LLM_FALLBACK_ENABLED=true
LLM_PRIMARY_PROVIDER=openai
ENVEOF

    log_warning "请编辑 .env 文件，填入你的 API Key"
}

# ==============================================================================
# 阶段 7: 创建便捷脚本
# ==============================================================================

phase_create_scripts() {
    log_section "阶段 7: 创建便捷脚本"
    
    # Dashboard 启动脚本
    create_script "run-dashboard.sh" << 'SCRIPTEOF'
#!/bin/bash
# SprintCycle Dashboard 启动脚本

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

echo "启动 SprintCycle Dashboard..."
echo "   地址: http://localhost:8000"
echo "   按 Ctrl+C 停止"
echo ""

cd sprintcycle/dashboard
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
SCRIPTEOF

    # MCP Server 启动脚本
    create_script "run-mcp.sh" << 'SCRIPTEOF'
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
SCRIPTEOF

    # 测试运行脚本
    create_script "run-tests.sh" << 'SCRIPTEOF'
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
SCRIPTEOF

    # Lint 运行脚本
    create_script "run-lint.sh" << 'SCRIPTEOF'
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
SCRIPTEOF

    # 环境激活脚本
    create_script "activate.sh" << 'SCRIPTEOF'
#!/bin/bash
# SprintCycle 开发环境激活脚本
# 使用方法: source activate.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

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
SCRIPTEOF

    log_success "便捷脚本创建完成"
}

create_script() {
    local script_name="$1"
    local script_content="$2"
    
    if [ -f "${script_name}" ] && [ "${FORCE_REINSTALL}" != true ]; then
        log_skip "${script_name} 已存在"
        return 0
    fi
    
    echo "${script_content}" > "${script_name}"
    chmod +x "${script_name}"
    log_success "创建 ${script_name}"
}

# ==============================================================================
# 阶段 8: 验证安装
# ==============================================================================

phase_verify() {
    log_section "阶段 8: 验证安装"
    
    local verify_status=0
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        log_error ".venv 目录不存在"
        return 1
    fi
    
    echo -n "  Python: "
    if python --version &>/dev/null; then
        log_success "$(python --version)"
    else
        log_error "Python 不可用"
        verify_status=1
    fi
    
    echo "  检查关键依赖..."
    local deps=("pydantic" "litellm" "pytest" "ruff" "mypy")
    for dep in "${deps[@]}"; do
        echo -n "    ${dep}: "
        if python -c "import ${dep}" 2>/dev/null; then
            local ver
            ver="$(python -c "import ${dep}; print(getattr(${dep}, '__version__', 'unknown'))")"
            log_success "${ver}"
        else
            log_error "未安装"
            verify_status=1
        fi
    done
    
    echo -n "  sprintcycle CLI: "
    if command -v sprintcycle &>/dev/null; then
        log_success "可用"
    else
        log_error "不可用"
        verify_status=1
    fi
    
    echo -n "  sprintcycle 包: "
    if python -c "import sprintcycle; print(f'v{sprintcycle.__version__}')" 2>/dev/null; then
        log_success "导入成功"
    else
        log_error "导入失败"
        verify_status=1
    fi
    
    if [ ${verify_status} -eq 0 ]; then
        log_success "所有验证通过"
    else
        log_error "部分验证失败，请检查上方的错误信息"
    fi
    
    return ${verify_status}
}

# ==============================================================================
# 显示完成信息
# ==============================================================================

show_completion() {
    echo ""
    echo "${COLOR_BOLD}${COLOR_GREEN}╔══════════════════════════════════════════════════════════════╗${COLOR_RESET}"
    echo "${COLOR_BOLD}${COLOR_GREEN}║                  部署完成！                                ║${COLOR_RESET}"
    echo "${COLOR_BOLD}${COLOR_GREEN}╚══════════════════════════════════════════════════════════════╝${COLOR_RESET}"
    echo ""
    echo "${COLOR_CYAN}📁 项目目录:${COLOR_RESET} $(pwd)"
    echo ""
    
    if [ ${#WARNED_STEPS[@]} -gt 0 ]; then
        echo "${COLOR_YELLOW}⚠️  警告 (${#WARNED_STEPS[@]} 项):${COLOR_RESET}"
        for warn in "${WARNED_STEPS[@]}"; do
            echo "  - ${warn}"
        done
        echo ""
    fi
    
    if [ ${#FAILED_STEPS[@]} -gt 0 ]; then
        echo "${COLOR_RED}❌ 失败 (${#FAILED_STEPS[@]} 项):${COLOR_RESET}"
        for fail in "${FAILED_STEPS[@]}"; do
            echo "  - ${fail}"
        done
        echo ""
    fi
    
    echo "${COLOR_BOLD}🚀 下一步:${COLOR_RESET}"
    echo ""
    echo "  1. ${COLOR_YELLOW}编辑 .env 文件，填入你的 API Key${COLOR_RESET}"
    echo "     vim .env"
    echo ""
    echo "  2. ${COLOR_GREEN}激活开发环境${COLOR_RESET}"
    echo "     source activate.sh"
    echo ""
    echo "  3. ${COLOR_CYAN}验证安装${COLOR_RESET}"
    echo "     sprintcycle --help"
    echo ""
    echo "${COLOR_BOLD}📋 便捷脚本:${COLOR_RESET}"
    echo "  ./run-dashboard.sh   - 启动 Dashboard (http://localhost:8000)"
    echo "  ./run-mcp.sh        - 启动 MCP Server"
    echo "  ./run-tests.sh      - 运行测试"
    echo "  ./run-lint.sh       - 运行代码检查"
    echo ""
    echo "${COLOR_BOLD}📚 文档:${COLOR_RESET}"
    echo "  DEV_SETUP_GUIDE.md  - 详细部署指南"
    echo "  DEPLOY_CHECKLIST.md - 部署检查清单"
    echo ""
    echo "💡 提示: 运行 ${COLOR_YELLOW}source activate.sh${COLOR_RESET} 后，使用 ${COLOR_YELLOW}sprintcycle --help${COLOR_RESET} 查看所有可用命令"
    echo ""
}

# ==============================================================================
# 使用帮助
# ==============================================================================

show_help() {
    cat << HELPEOF
SprintCycle 开发环境一键部署脚本 v${VERSION}

用法: ./dev-setup.sh [选项]

选项:
  --skip-system-deps     跳过系统依赖安装
  --skip-node            跳过 Node.js 安装
  --python-version VER   指定 Python 版本 (如 3.12)
  --branch NAME          指定 Git 分支 (默认: main)
  --force                强制重新安装 (覆盖已有配置)
  --dry-run              仅显示将要执行的操作
  -h, --help             显示此帮助信息

示例:
  ./dev-setup.sh                    # 完整安装
  ./dev-setup.sh --skip-system-deps # 跳过系统依赖
  ./dev-setup.sh --python-version 3.11 --branch develop  # 指定版本和分支
  curl -fsSL <url> | bash           # 远程一键部署

支持的平台:
  - macOS (Intel/Apple Silicon) + Homebrew
  - Linux: Ubuntu, Debian, CentOS, Fedora, Arch
HELPEOF
}

# ==============================================================================
# 命令行参数解析
# ==============================================================================

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --skip-system-deps)
                SKIP_SYSTEM_DEPS=true
                shift
                ;;
            --skip-node)
                SKIP_NODE=true
                shift
                ;;
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --branch)
                GIT_BRANCH="$2"
                shift 2
                ;;
            --force|-f)
                FORCE_REINSTALL=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# ==============================================================================
# 主函数
# ==============================================================================

main() {
    parse_args "$@"
    
    echo ""
    echo "    _____ _____ _____ _____ _____ _____ _____ _____ _____ "
    echo "   |   __|   __|     |  _  |  _  |   __| __  |  _  |   __|"
    echo "   |__   |   __| | | |   __|   __|   __|    -|     |   __|"
    echo "   |_____|_____|_|_|_|__|  |__|  |_____|__|__|__|__|_____|"
    echo ""
    echo "                开发环境一键部署脚本 v${VERSION}"
    echo ""
    
    echo "开始部署 SprintCycle 开发环境..."
    echo ""
    
    phase_system_detection
    phase_install_system_deps || log_warning "系统依赖安装可能有警告"
    phase_project_setup || { log_error "项目准备失败"; exit 1; }
    phase_python_env || { log_error "Python 环境配置失败"; exit 1; }
    phase_install_python_deps || { log_error "Python 依赖安装失败"; exit 1; }
    phase_env_config
    phase_create_scripts
    phase_verify
    
    show_completion
    
    if [ "${STEP_STATUS}" = "FAIL" ]; then
        exit 1
    fi
}

main "$@"
