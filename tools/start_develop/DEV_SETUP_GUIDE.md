# SprintCycle 开发环境部署指南

## 📋 目录

- [快速开始](#快速开始)
- [系统要求](#系统要求)
- [各平台详细步骤](#各平台详细步骤)
  - [macOS](#macos)
  - [Ubuntu/Debian](#ubuntudebian)
  - [CentOS/RHEL](#centosrhel)
  - [Fedora](#fedora)
  - [Arch Linux](#arch-linux)
- [环境变量配置](#环境变量配置)
- [常见问题排查 (FAQ)](#常见问题排查-faq)
- [手动安装步骤](#手动安装步骤)
- [开发工作流](#开发工作流)

---

## ⚡ 快速开始

### 一行命令部署

```bash
# 进入项目目录（如果没有克隆）
git clone https://github.com/sprintcycle/sprintcycle.git && cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh && ./dev-setup.sh
```

### 远程一键部署

```bash
# 直接从 GitHub 运行（需要先克隆或手动创建脚本）
curl -fsSL https://raw.githubusercontent.com/sprintcycle/sprintcycle/main/dev-setup.sh | bash
```

### 部署后

```bash
# 1. 编辑 .env 文件，填入 API Key
vim .env

# 2. 激活开发环境
source activate.sh

# 3. 验证安装
sprintcycle --help
```

---

## 💻 系统要求

### 最低要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 11+ / Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / Fedora 34+ / Arch |
| Python | 3.10 或更高版本 |
| 内存 | 2GB RAM（推荐 4GB+） |
| 磁盘空间 | 1GB 可用空间 |

### 软件依赖

| 依赖 | 说明 | 必须 |
|------|------|------|
| Git | 代码版本控制 | ✅ |
| Python 3.10+ | 运行环境 | ✅ |
| pip | 包管理器 | ✅ |
| Homebrew (macOS) | macOS 包管理器 | ✅ (macOS) |
| sudo (Linux) | 管理员权限 | ⚠️ (Linux) |

---

## 📦 各平台详细步骤

### macOS

#### 前置条件

1. **安装 Homebrew**（如果未安装）：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. **验证安装**：

```bash
brew --version
```

#### 运行部署脚本

```bash
# 克隆项目（如果还没有）
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh
./dev-setup.sh
```

#### 脚本会自动完成

- ✅ 检测系统环境
- ✅ 安装 Git（通过 Homebrew）
- ✅ 安装 Python 3.12（通过 Homebrew）
- ✅ 创建 Python 虚拟环境
- ✅ 安装所有 Python 依赖
- ✅ 创建 .env 配置文件
- ✅ 创建便捷脚本
- ✅ 验证安装

#### 手动安装（备用）

```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install git python@3.12

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"

# 创建 .env 文件
cp .env.example .env  # 或手动创建
```

---

### Ubuntu/Debian

#### 前置条件

确保有 sudo 权限：

```bash
sudo -v
```

#### 运行部署脚本

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装必要工具
sudo apt-get install -y git curl

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh
./dev-setup.sh
```

#### 脚本会自动完成

- ✅ 检测系统环境（Ubuntu/Debian）
- ✅ 更新 apt 包列表
- ✅ 安装 Git、curl、build-essential、libssl-dev
- ✅ 安装 Python 3.12（通过 deadsnakes PPA）
- ✅ 创建 Python 虚拟环境
- ✅ 安装所有 Python 依赖
- ✅ 创建 .env 配置文件
- ✅ 创建便捷脚本

#### 手动安装（备用）

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础工具
sudo apt-get install -y git curl build-essential libssl-dev zlib1g-dev software-properties-common

# 添加 Python PPA 并安装
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

# 设置默认 Python
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"
```

---

### CentOS/RHEL

#### 前置条件

确保有 sudo 或 root 权限。

#### 运行部署脚本

```bash
# 安装基础工具
sudo yum install -y git curl

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh
./dev-setup.sh
```

#### 脚本会自动完成

- ✅ 检测系统环境（CentOS/RHEL）
- ✅ 安装 EPEL 仓库
- ✅ 安装开发工具组
- ✅ 安装 Git、curl、openssl-devel、zlib-devel
- ✅ 安装 Python 3（通过系统仓库或 SCL）
- ✅ 创建 Python 虚拟环境
- ✅ 安装所有 Python 依赖

#### 手动安装（备用）

```bash
# 安装 EPEL 和开发工具
sudo yum install -y epel-release
sudo yum groupinstall -y "Development Tools"

# 安装基础工具
sudo yum install -y git curl openssl-devel zlib-devel

# CentOS 8+ 使用模块安装 Python
sudo yum module reset python -y
sudo yum module enable python38 -y
sudo yum install -y python38 python38-pip python38-devel

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"
```

---

### Fedora

#### 运行部署脚本

```bash
# 安装基础工具
sudo dnf install -y git curl

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh
./dev-setup.sh
```

#### 手动安装（备用）

```bash
# 安装基础工具
sudo dnf install -y git curl openssl-devel zlib-devel python3 python3-pip python3-devel

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"
```

---

### Arch Linux

#### 运行部署脚本

```bash
# 安装基础工具
sudo pacman -Sy git curl

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 运行部署脚本
chmod +x dev-setup.sh
./dev-setup.sh
```

#### 手动安装（备用）

```bash
# 安装基础工具
sudo pacman -Sy git curl base-devel openssl zlib python python-pip

# 克隆项目
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"
```

---

## 🔧 环境变量配置

### .env 文件说明

部署脚本会自动创建 `.env` 文件，包含以下配置项：

```env
# ==============================================================================
# SprintCycle 环境配置
# ==============================================================================

# ===== LLM API 配置 =====
# 支持的提供商: OpenAI, Anthropic, DeepSeek, 豆包, 通义千问 等

# OpenAI (推荐)
OPENAI_API_KEY=                    # 留空，运行时填入
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# DeepSeek
DEEPSEEK_API_KEY=                  # 留空，运行时填入

# ===== SprintCycle 运行时配置 =====
SPRINTCYCLE_WORKSPACE=./workspace
SPRINTCYCLE_LOG_LEVEL=INFO
SPRINTCYCLE_MAX_ITERATIONS=10
SPRINTCYCLE_CACHE_DIR=./cache

# ===== MCP Server 配置 =====
MCP_TRANSPORT=stdio

# SSE 传输 (用于远程访问，可选)
# MCP_SERVER_HOST=0.0.0.0
# MCP_SERVER_PORT=8765

# ===== LLM 回退配置 =====
LLM_FALLBACK_ENABLED=true
LLM_PRIMARY_PROVIDER=openai
```

### 配置项说明

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API Key | - | ✅ |
| `OPENAI_API_BASE` | API 端点 | `https://api.openai.com/v1` | - |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o` | - |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | (可选) |
| `SPRINTCYCLE_WORKSPACE` | 工作空间目录 | `./workspace` | - |
| `SPRINTCYCLE_LOG_LEVEL` | 日志级别 | `INFO` | - |
| `SPRINTCYCLE_MAX_ITERATIONS` | 最大迭代次数 | `10` | - |
| `SPRINTCYCLE_CACHE_DIR` | 缓存目录 | `./cache` | - |
| `MCP_TRANSPORT` | MCP 传输方式 | `stdio` | - |
| `MCP_SERVER_HOST` | MCP 服务器地址 | `localhost` | - |
| `MCP_SERVER_PORT` | MCP 服务器端口 | `8000` | - |

### 获取 API Key

#### OpenAI

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册并登录
3. 进入 API Keys 页面
4. 创建新的 API Key

#### DeepSeek

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册并登录
3. 创建 API Key

---

## ❓ 常见问题排查 (FAQ)

### Q1: 脚本执行失败怎么办？

**A**: 首先检查错误信息，然后尝试以下步骤：

```bash
# 1. 查看详细错误
./dev-setup.sh --dry-run

# 2. 跳过系统依赖安装（如果已安装）
./dev-setup.sh --skip-system-deps

# 3. 强制重新安装
./dev-setup.sh --force

# 4. 参考手动安装步骤
```

### Q2: Python 版本低于 3.10

**A**: 需要升级 Python。脚本会自动处理，如果没有：

```bash
# Ubuntu/Debian
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

# macOS
brew install python@3.12

# CentOS
sudo yum module enable python38 -y
sudo yum install -y python38 python38-pip
```

### Q3: Homebrew 未安装 (macOS)

**A**: 安装 Homebrew：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Q4: 虚拟环境创建失败

**A**: 检查磁盘空间和权限：

```bash
# 检查磁盘空间
df -h

# 检查权限
ls -la

# 手动创建虚拟环境
rm -rf .venv
python3 -m venv .venv
```

### Q5: pip install 失败

**A**: 尝试以下方法：

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev,mcp-sse]"

# 检查网络连接
curl -I https://pypi.org
```

### Q6: sprintcycle 命令找不到

**A**: 确保在虚拟环境中：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 重新安装包
pip install -e ".[dev,mcp-sse]"

# 检查安装
pip list | grep sprintcycle
```

### Q7: ModuleNotFoundError

**A**: 重新安装依赖：

```bash
# 清除缓存
rm -rf .venv __pycache__ .pytest_cache

# 重新创建环境
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,mcp-sse]"
```

### Q8: 权限错误 (Linux)

**A**: 确保有 sudo 权限：

```bash
# 检查当前用户
whoami

# 检查 sudo
sudo -v

# 手动安装系统依赖
sudo apt-get install -y git curl build-essential
```

### Q9: 如何更新 SprintCycle？

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -e ".[dev,mcp-sse]" --upgrade
```

### Q10: 如何完全卸载？

```bash
# 删除虚拟环境和缓存
rm -rf .venv __pycache__ .pytest_cache .ruff_cache .mypy_cache

# 删除生成的文件
rm -f .env activate.sh run-*.sh start.sh test.sh

# 卸载包
pip uninstall sprintcycle
```

---

## 🔨 手动安装步骤

如果脚本失败，使用以下步骤手动安装：

### 1. 系统依赖

**macOS:**
```bash
brew install git python@3.12
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y git curl build-essential libssl-dev zlib1g-dev
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
```

**CentOS:**
```bash
sudo yum install -y git curl epel-release
sudo yum groupinstall -y "Development Tools"
sudo yum module enable python38 -y
sudo yum install -y python38 python38-pip python38-devel
```

**Fedora:**
```bash
sudo dnf install -y git curl openssl-devel zlib-devel python3 python3-pip python3-devel
```

**Arch:**
```bash
sudo pacman -Sy git curl base-devel openssl zlib python python-pip
```

### 2. 项目代码

```bash
git clone https://github.com/sprintcycle/sprintcycle.git
cd sprintcycle
```

### 3. Python 环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

### 4. 安装依赖

```bash
# 安装项目依赖
pip install -e ".[dev,mcp-sse]"

# 安装额外依赖（如果需要）
pip install -r requirements.txt
```

### 5. 环境配置

```bash
# 创建 .env 文件
cat > .env << 'EOF'
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
SPRINTCYCLE_WORKSPACE=./workspace
SPRINTCYCLE_LOG_LEVEL=INFO
EOF
```

### 6. 验证安装

```bash
# 检查 Python
python --version

# 检查 sprintcycle
sprintcycle --help

# 运行测试
python -m pytest tests/ -v
```

---

## 🛠️ 开发工作流

### 日常开发

```bash
# 1. 激活环境
source activate.sh

# 2. 拉取最新代码（如果有更新）
git pull origin main

# 3. 运行开发任务
sprintcycle run your-task

# 4. 完成后退出
deactivate
```

### 运行测试

```bash
# 使用便捷脚本
./run-tests.sh

# 或手动运行
source activate.sh
python -m pytest tests/ -v
```

### 代码检查

```bash
# 使用便捷脚本
./run-lint.sh

# 或手动运行
source activate.sh
ruff check sprintcycle/
mypy sprintcycle/ --ignore-missing-imports
```

### 启动 Dashboard

```bash
# 使用便捷脚本
./run-dashboard.sh

# 或手动运行
source activate.sh
cd sprintcycle/dashboard
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 MCP Server

```bash
# 使用便捷脚本
./run-mcp.sh

# 或手动运行
source activate.sh
sprintcycle mcp
```

### 更新依赖

```bash
source activate.sh
pip install -e ".[dev,mcp-sse]" --upgrade
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看 [常见问题](#常见问题排查-faq)
2. 查看 [DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)
3. 查看 [GitHub Issues](https://github.com/sprintcycle/sprintcycle/issues)
4. 提交新的 Issue

---

**文档版本**: v2.0.0  
**最后更新**: 2026-05-04
