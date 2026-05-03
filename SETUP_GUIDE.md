# SprintCycle 开发环境部署指南

## 📋 目录
- [快速开始](#快速开始)
- [系统要求](#系统要求)
- [详细安装步骤](#详细安装步骤)
- [环境配置](#环境配置)
- [验证安装](#验证安装)
- [常用命令](#常用命令)
- [故障排除](#故障排除)
- [卸载](#卸载)

---

## ⚡ 快速开始

### 一键部署（推荐）

```bash
# 1. 克隆或进入 SprintCycle 项目目录
cd sprintcycle

# 2. 运行一键部署脚本
chmod +x setup.sh
./setup.sh

# 3. 编辑 .env 文件，填入你的 API Key
vim .env

# 4. 激活环境
source activate.sh

# 5. 开始使用！
sprintcycle --help
```

**就这么简单！整个过程通常只需要 2-5 分钟。**

---

## 💻 系统要求

### 最低要求
- **操作系统**: macOS 11+ / Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / Fedora 34+
- **Python**: 3.10 或更高版本
- **内存**: 2GB RAM（推荐 4GB+）
- **磁盘空间**: 1GB 可用空间

### 软件依赖
- Git
- Python 3.10+
- pip

---

## 📦 详细安装步骤

### 步骤 1: 获取项目代码

```bash
# 如果你还没有代码
git clone <your-repository-url>
cd sprintcycle

# 或者如果你已经有代码
cd /path/to/sprintcycle
```

### 步骤 2: 运行一键部署脚本

```bash
chmod +x setup.sh
./setup.sh
```

脚本会自动完成以下操作：
1. ✅ 检测操作系统和包管理器
2. ✅ 安装系统依赖（Python3、Git）
3. ✅ 创建 Python 虚拟环境
4. ✅ 安装所有 Python 依赖包
5. ✅ 创建 .env 配置文件模板
6. ✅ 创建便捷脚本（activate.sh、start.sh、test.sh）
7. ✅ 验证安装

### 步骤 3: 配置 LLM API Key

编辑 `.env` 文件，配置你使用的 LLM：

#### 选项 A: 使用 OpenAI
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

#### 选项 B: 使用 Anthropic Claude
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

#### 选项 C: 使用豆包（字节跳动）
```env
DOUBAO_API_KEY=xxxxxxxxxxxxxxxx
DOUBAO_API_BASE=https://ark.cn-beijing.volces.com/api/v3
```

#### 选项 D: 使用通义千问（阿里云）
```env
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## 🔧 环境配置

### 虚拟环境说明

脚本会自动创建 `.venv/` 目录作为虚拟环境。**不要直接使用系统 Python！**

激活虚拟环境：
```bash
source activate.sh
# 或者
source .venv/bin/activate
```

退出虚拟环境：
```bash
deactivate
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key | 必填 |
| `OPENAI_API_BASE` | API 端点 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 使用的模型 | `gpt-4` |
| `SPRINTCYCLE_WORKSPACE` | 工作空间目录 | `./workspace` |
| `SPRINTCYCLE_LOG_LEVEL` | 日志级别 | `INFO` |
| `SPRINTCYCLE_MAX_ITERATIONS` | 最大迭代次数 | `10` |
| `MCP_SERVER_HOST` | MCP 服务器主机 | `localhost` |
| `MCP_SERVER_PORT` | MCP 服务器端口 | `8000` |

---

## ✅ 验证安装

安装完成后，运行以下命令验证：

### 1. 检查 Python 版本
```bash
source activate.sh
python --version
# 应该显示 Python 3.10.x 或更高
```

### 2. 检查 sprintcycle CLI
```bash
sprintcycle --version
# 或
sprintcycle --help
```

### 3. 运行单元测试
```bash
./test.sh
# 或
python -m pytest tests/ -v
```

### 4. 导入测试
```bash
python -c "import sprintcycle; print('✅ sprintcycle 导入成功')"
```

---

## 🎯 常用命令

### 环境管理
```bash
# 激活环境
source activate.sh

# 退出环境
deactivate

# 重新安装依赖
pip install -e ".[dev,mcp-sse]"
```

### 开发命令
```bash
# 查看帮助
sprintcycle --help

# 初始化项目
sprintcycle init

# 运行任务
sprintcycle run <prd-file>

# 查看版本
sprintcycle --version
```

### 代码质量检查
```bash
# 类型检查
mypy sprintcycle/

# 代码 lint
ruff check sprintcycle/

# 格式化代码
ruff format sprintcycle/
```

### 测试命令
```bash
# 运行所有测试
./test.sh

# 运行特定测试
python -m pytest tests/test_agents.py -v

# 生成覆盖率报告
python -m pytest --cov=sprintcycle tests/
```

---

## 🔍 故障排除

### 问题 1: 权限错误

**症状**: `Permission denied` 或需要 sudo

**解决方法**:
```bash
# 给脚本执行权限
chmod +x setup.sh activate.sh start.sh test.sh

# 如果 Homebrew 需要权限
sudo chown -R $(whoami) /usr/local/*
```

---

### 问题 2: Python 版本太低

**症状**: `Python version is too low` 或语法错误

**解决方法**:

#### macOS
```bash
# 安装 Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.11
brew install python@3.11
brew link python@3.11 --force
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

#### CentOS/Fedora
```bash
# Fedora
sudo dnf install -y python3.11

# CentOS
sudo yum install -y centos-release-scl
sudo yum install -y rh-python311
scl enable rh-python311 bash
```

---

### 问题 3: pip 安装慢或失败

**症状**: pip 安装超时或速度很慢

**解决方法**: 使用国内镜像源

```bash
# 临时使用镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package-name

# 或者永久配置镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

常用镜像源：
- 清华: `https://pypi.tuna.tsinghua.edu.cn/simple`
- 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
- 中科大: `https://pypi.mirrors.ustc.edu.cn/simple/`

---

### 问题 4: 虚拟环境创建失败

**症状**: `Error: [Errno 13] Permission denied`

**解决方法**:
```bash
# 删除旧的虚拟环境
rm -rf .venv

# 确保目录权限正确
chmod -R 755 .

# 手动创建虚拟环境
python3 -m venv .venv

# 激活并升级 pip
source .venv/bin/activate
pip install --upgrade pip
```

---

### 问题 5: 导入模块失败

**症状**: `ModuleNotFoundError: No module named 'sprintcycle'`

**解决方法**:
```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 以开发模式安装
pip install -e .

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

---

### 问题 6: Mac M1/M2 架构问题

**症状**: 某些包安装失败，提示架构不兼容

**解决方法**:
```bash
# 使用 Rosetta 2 运行终端（如果需要）
# 或者强制使用 x86_64 架构
arch -x86_64 ./setup.sh

# 通常不需要，Python 3.9+ 原生支持 Apple Silicon
```

---

### 问题 7: 网络问题

**症状**: 无法下载包或连接超时

**解决方法**:
```bash
# 检查网络连接
curl -I https://pypi.org

# 配置代理（如果需要）
export HTTP_PROXY=http://proxy-server:port
export HTTPS_PROXY=http://proxy-server:port

# 或者在 .env 中配置
```

---

### 问题 8: 测试失败

**症状**: pytest 运行失败

**解决方法**:
```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 安装测试依赖
pip install -e ".[dev]"

# 清除缓存
rm -rf .pytest_cache __pycache__

# 重新运行
python -m pytest tests/ -v
```

---

### 通用调试技巧

1. **查看详细输出**
   ```bash
   # 使用 -x 选项查看 bash 脚本执行详情
   bash -x setup.sh
   ```

2. **检查 Python 环境**
   ```bash
   which python
   which pip
   pip list
   ```

3. **手动逐步执行**
   如果脚本失败，可以手动执行每一步来定位问题。

---

## 🗑️ 卸载

如果需要完全卸载 SprintCycle 开发环境：

```bash
# 1. 退出虚拟环境
deactivate

# 2. 删除虚拟环境
rm -rf .venv

# 3. 删除生成的脚本（可选）
rm -f activate.sh start.sh test.sh

# 4. 删除 .env 文件（可选）
rm -f .env

# 5. 删除工作空间（可选）
rm -rf workspace

# 6. 删除缓存（可选）
rm -rf .pytest_cache __pycache__ .mypy_cache
rm -rf .sprintcycle
```

---

## 📞 获取帮助

如果以上方法都无法解决你的问题：

1. 检查 `DEPLOY_CHECKLIST.md` 确认每一步都完成
2. 查看项目的 `README.md`
3. 检查 `docs/` 目录下的其他文档
4. 在项目 Issue 中搜索类似问题
5. 联系技术支持

---

## 📝 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.9.2 | 2026-05-03 | 初始版本，支持 macOS 和 Linux |

---

## 📄 许可证

与 SprintCycle 项目保持一致。
