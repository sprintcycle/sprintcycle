#!/bin/bash
# SprintCycle 自动修复集成脚本
# 版本: 1.0.0
# 更新: 2026-05-19

set -e

echo "🚀 SprintCycle 自动修复集成安装..."

# 1. 检查 Ruff
if ! command -v ruff &> /dev/null; then
    echo "📦 安装 Ruff..."
    pip install ruff
else
    echo "✅ Ruff 已安装: $(ruff --version)"
fi

# 2. 安装 pre-commit
if ! command -v pre-commit &> /dev/null; then
    echo "📦 安装 pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit 已安装"
fi

# 3. 安装 pre-commit hooks
echo "🔧 安装 Git hooks..."
pre-commit install

# 4. 运行首次检查
echo "🔍 运行首次代码检查..."
ruff check sprintcycle/ --output-format=concise

echo ""
echo "✅ 安装完成！"
echo ""
echo "📋 使用方式："
echo "   1. 在 Cursor 中保存文件时，Ruff 会自动修复风格问题"
echo "   2. 未定义变量等严重问题会报错，需人工修复"
echo "   3. 运行 'ruff fix sprintcycle/' 手动修复所有问题"
echo "   4. 运行 'ruff check sprintcycle/' 查看所有问题"
echo ""
