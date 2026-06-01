#!/bin/bash
# SprintCycle 自动化验证入口脚本
# 基于架构不变性和架构约束规则，完全自动化验证

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN=".venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    echo "❌ 未找到 .venv/bin/python，请先创建虚拟环境"
    exit 1
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "========================================================"
    echo "$1"
    echo "========================================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 主验证流程
main() {
    echo -e "${BLUE}🚀 SprintCycle 自动化验证开始${NC}"
    
    local all_passed=0
    
    # Phase 1: 架构不变性验证
    print_header "Phase 1: 架构不变性验证"
    echo "运行架构验证器..."
    "$PYTHON_BIN" scripts/validate_architecture.py
    if [ $? -ne 0 ]; then
        print_error "架构验证失败"
        all_passed=1
    else
        print_success "架构验证通过"
    fi
    
    # Phase 2: 单元测试
    print_header "Phase 2: 单元测试验证"
    echo "运行单元测试..."
    "$PYTHON_BIN" -m pytest tests/ -v --tb=short -x -q
    if [ $? -ne 0 ]; then
        print_error "单元测试失败"
        all_passed=1
    else
        print_success "单元测试通过"
    fi
    
    # Phase 3: API 契约验证
    print_header "Phase 3: API 契约验证"
    if [ -f "tests/test_integration_api.py" ]; then
        echo "运行 API 测试..."
        "$PYTHON_BIN" -m pytest tests/test_integration_api.py -v --tb=short -q
        if [ $? -ne 0 ]; then
            print_error "API 契约验证失败"
            all_passed=1
        else
            print_success "API 契约验证通过"
        fi
    else
        print_warning "API 测试文件不存在，跳过"
    fi
    
    # Phase 4: E2E 测试
    print_header "Phase 4: E2E 测试验证"
    if [ -d "frontend" ] && [ -d "frontend/node_modules" ]; then
        echo "运行 Playwright E2E 测试..."
        cd frontend
        npx playwright test --reporter=line 2>&1 | tail -20
        local e2e_exit=$?
        cd "${PROJECT_ROOT}"
        if [ $e2e_exit -ne 0 ]; then
            print_warning "E2E 测试失败（非阻塞）"
        else
            print_success "E2E 测试通过"
        fi
    else
        print_warning "前端目录或依赖不存在，跳过 E2E 测试"
    fi
    
    # Phase 5: 文档验证
    print_header "Phase 5: 文档同步验证"
    local docs_ok=0
    for doc in "README.md" "README_EN.md" "docs/ARCHITECTURE_INVARIANTS.md" ".cursor/rules/sprintcycle-architecture-orchestration.mdc"; do
        if [ -f "$doc" ]; then
            echo "✅ $doc"
        else
            print_error "$doc 不存在"
            docs_ok=1
        fi
    done
    if [ $docs_ok -eq 0 ]; then
        print_success "文档验证通过"
    else
        all_passed=1
    fi
    
    # 汇总结果
    print_header "验证结果汇总"
    if [ $all_passed -eq 0 ]; then
        echo -e "${GREEN}🎉 所有验证通过！${NC}"
        echo ""
        echo "✅ SprintCycle 已准备好进入生产环境"
        return 0
    else
        echo -e "${RED}❌ 部分验证失败，请修复后重新验证${NC}"
        return 1
    fi
}

# 执行主流程
main "$@"
exit $?