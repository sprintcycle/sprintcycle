#!/bin/bash
# ==============================================================================
# SprintCycle 一键开发环境部署脚本
# 支持: macOS (Intel/Apple Silicon) / Linux (Ubuntu/Debian/CentOS/Fedora)
# 功能: 0成本快速构建完整开发环境
# ==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     OS_TYPE="linux";;
        Darwin*)    OS_TYPE="mac";;
        *)          OS_TYPE="unknown";;
    esac
    print_info "检测到操作系统: ${OS}"
    
    # 检测 Linux 发行版
    if [ "${OS_TYPE}" = "linux" ]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO="${ID}"
            DISTRO_VERSION="${VERSION_ID}"
            print_info "Linux 发行版: ${DISTRO} ${DISTRO_VERSION}"
        elif command -v lsb_release &> /dev/null; then
            DISTRO="$(lsb_release -si | tr '[:upper:]' '[:lower:]')"
            print_info "Linux 发行版: ${DISTRO}"
        else
            DISTRO="unknown"
            print_warning "无法检测 Linux 发行版"
        fi
    fi
    
    # 检测 Mac CPU 架构
    if [ "${OS_TYPE}" = "mac" ]; then
        ARCH="$(uname -m)"
        print_info "CPU 架构: ${ARCH}"
    fi
}

# 检测包管理器
detect_package_manager() {
    if [ "${OS_TYPE}" = "mac" ]; then
        if command -v brew &> /dev/null; then
            PKG_MANAGER="brew"
            print_info "包管理器: Homebrew"
        else
            PKG_MANAGER="none"
            print_warning "未检测到 Homebrew"
        fi
    elif [ "${OS_TYPE}" = "linux" ]; then
        if command -v apt-get &> /dev/null; then
            PKG_MANAGER="apt"
            print_info "包管理器: apt"
        elif command -v yum &> /dev/null; then
            PKG_MANAGER="yum"
            print_info "包管理器: yum"
        elif command -v dnf &> /dev/null; then
            PKG_MANAGER="dnf"
            print_info "包管理器: dnf"
        else
            PKG_MANAGER="none"
            print_warning "未检测到包管理器"
        fi
    fi
}

# 安装系统依赖
install_system_deps() {
    print_info "安装系统依赖..."
    
    local PYTHON_MIN_VERSION="3.10"
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_info "已安装 Python: ${PYTHON_VERSION}"
        
        if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
            print_warning "Python 版本低于 ${PYTHON_MIN_VERSION}，将尝试安装更新版本"
            NEED_PYTHON_INSTALL=true
        else
            NEED_PYTHON_INSTALL=false
        fi
    else
        print_info "未检测到 Python3，将进行安装"
        NEED_PYTHON_INSTALL=true
    fi
    
    # 根据操作系统安装
    if [ "${OS_TYPE}" = "mac" ]; then
        if [ "${PKG_MANAGER}" = "brew" ]; then
            if [ "${NEED_PYTHON_INSTALL}" = true ]; then
                print_info "通过 Homebrew 安装 Python3..."
                brew install python3
            fi
            
            # 检查 Git
            if ! command -v git &> /dev/null; then
                print_info "安装 Git..."
                brew install git
            fi
        else
            print_error "Mac 需要先安装 Homebrew，请访问: https://brew.sh/"
            print_info "请手动安装后重新运行此脚本"
            exit 1
        fi
    elif [ "${OS_TYPE}" = "linux" ]; then
        case "${PKG_MANAGER}" in
            apt)
                print_info "更新 apt 包列表..."
                sudo apt-get update -y
                if [ "${NEED_PYTHON_INSTALL}" = true ]; then
                    print_info "安装 Python3 和 pip..."
                    sudo apt-get install -y python3 python3-pip python3-venv
                fi
                if ! command -v git &> /dev/null; then
                    print_info "安装 Git..."
                    sudo apt-get install -y git
                fi
                sudo apt-get install -y python3-dev
                ;;
            yum|dnf)
                if [ "${NEED_PYTHON_INSTALL}" = true ]; then
                    print_info "安装 Python3 和 pip..."
                    sudo ${PKG_MANAGER} install -y python3 python3-pip python3-devel
                fi
                if ! command -v git &> /dev/null; then
                    print_info "安装 Git..."
                    sudo ${PKG_MANAGER} install -y git
                fi
                ;;
            *)
                print_warning "请手动安装 Python3 (>=3.10) 和 Git"
                ;;
        esac
    fi
    
    print_success "系统依赖安装完成"
}

# 配置 Python 虚拟环境
setup_python_env() {
    print_info "配置 Python 虚拟环境..."
    
    # 确保在项目根目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}"
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv .venv
    else
        print_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    print_success "虚拟环境已激活"
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip
    
    print_success "Python 环境配置完成"
}

# 安装 Python 依赖
install_python_deps() {
    print_info "安装 Python 依赖..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}"
    
    # 确保虚拟环境已激活
    if [ -z "${VIRTUAL_ENV}" ]; then
        source .venv/bin/activate
    fi
    
    print_info "安装核心依赖..."
    pip install -e ".[dev,mcp-sse]"
    
    print_success "Python 依赖安装完成"
}

# 配置环境变量
setup_env_vars() {
    print_info "配置环境变量..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}"
    
    # 创建 .env 文件（如果不存在）
    if [ ! -f ".env" ]; then
        print_info "创建 .env 文件..."
        cat > .env << 'ENVEOF'
# ==============================================================================
# SprintCycle 环境配置
# 请根据你的实际情况填写以下配置
# ==============================================================================

# ===== LLM 配置 =====
# 你可以选择使用任何支持的 LLM 提供商

# 选项 1: OpenAI (默认)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 选项 2: Anthropic Claude
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 选项 3: 豆包 (字节跳动)
# DOUBAO_API_KEY=your_doubao_api_key_here
# DOUBAO_API_BASE=https://ark.cn-beijing.volces.com/api/v3

# 选项 4: 通义千问 (阿里云)
# DASHSCOPE_API_KEY=your_dashscope_api_key_here

# ===== SprintCycle 配置 =====
SPRINTCYCLE_WORKSPACE=./workspace
SPRINTCYCLE_LOG_LEVEL=INFO
SPRINTCYCLE_MAX_ITERATIONS=10

# ===== MCP 配置 =====
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

ENVEOF
        print_warning "请编辑 .env 文件填入你的 API Key"
    else
        print_info ".env 文件已存在"
    fi
    
    print_success "环境变量配置完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}"
    
    # 确保虚拟环境已激活
    if [ -z "${VIRTUAL_ENV}" ]; then
        source .venv/bin/activate
    fi
    
    # 检查 Python
    PYTHON_VERSION=$(python --version)
    print_info "Python: ${PYTHON_VERSION}"
    
    # 检查 pip
    PIP_VERSION=$(pip --version)
    print_info "pip: ${PIP_VERSION}"
    
    # 检查 sprintcycle CLI
    if command -v sprintcycle &> /dev/null; then
        SPRINTCYCLE_VERSION=$(sprintcycle --version 2>/dev/null || echo "可用")
        print_info "sprintcycle CLI: ${SPRINTCYCLE_VERSION}"
    else
        print_warning "sprintcycle CLI 未找到"
    fi
    
    # 运行基础测试
    print_info "运行基础测试..."
    if python -c "import sprintcycle; print('sprintcycle 导入成功')" 2>/dev/null; then
        print_success "sprintcycle 包导入成功"
    else
        print_error "sprintcycle 包导入失败"
        return 1
    fi
    
    print_success "安装验证完成"
}

# 创建便捷命令
create_aliases() {
    print_info "创建便捷命令..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}"
    
    # 创建激活脚本
    cat > activate.sh << 'EOF'
#!/bin/bash
# SprintCycle 环境激活脚本
# 使用方法: source activate.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 激活虚拟环境
source .venv/bin/activate

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "========================================"
echo "  SprintCycle 开发环境已激活"
echo "  工作目录: $(pwd)"
echo "  Python: $(python --version)"
echo "========================================"
echo ""
echo "可用命令:"
echo "  sprintcycle --help    - 查看 CLI 帮助"
echo "  sprintcycle init      - 初始化项目"
echo "  sprintcycle run       - 运行任务"
echo "  deactivate            - 退出虚拟环境"
EOF
    chmod +x activate.sh
    
    # 创建快速启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash
# SprintCycle 快速启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

source activate.sh

echo ""
echo "启动 SprintCycle..."
sprintcycle --help
EOF
    chmod +x start.sh
    
    # 创建测试脚本
    cat > test.sh << 'EOF'
#!/bin/bash
# SprintCycle 测试脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

source .venv/bin/activate

echo "运行单元测试..."
python -m pytest tests/ -v --tb=short
EOF
    chmod +x test.sh
    
    print_success "便捷命令创建完成"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 部署完成！                                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 项目目录: $(pwd)"
    echo ""
    echo "🚀 快速开始:"
    echo "  1. 编辑 .env 文件，填入你的 API Key"
    echo "  2. 运行: source activate.sh    # 激活开发环境"
    echo "  3. 运行: sprintcycle --help    # 查看 CLI 帮助"
    echo ""
    echo "📋 便捷脚本:"
    echo "  ./activate.sh   - 激活开发环境 (使用 source 命令)"
    echo "  ./start.sh      - 快速启动并查看帮助"
    echo "  ./test.sh       - 运行单元测试"
    echo ""
    echo "📚 文档:"
    echo "  - SETUP_GUIDE.md   - 详细使用文档"
    echo "  - DEPLOY_CHECKLIST.md  - 部署检查清单"
    echo ""
    echo "💡 提示: 如果遇到问题，请查看 SETUP_GUIDE.md 中的故障排除章节"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           SprintCycle 一键开发环境部署工具                      ║"
    echo "║                支持 macOS / Linux                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    detect_os
    detect_package_manager
    install_system_deps
    setup_python_env
    install_python_deps
    setup_env_vars
    create_aliases
    verify_installation
    show_completion
}

# 运行主函数
main
