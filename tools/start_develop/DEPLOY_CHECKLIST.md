# SprintCycle 部署检查清单 v2.0

> 📋 **说明**: 此清单用于确保 SprintCycle 开发环境部署的每一步都正确完成。
> 部署完成后，请逐行核对并打勾 ✅

---

## 🚀 部署前检查

### 系统环境
- [ ] **操作系统**: macOS 11+ / Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 34+, Arch)
- [ ] **内存**: 至少 2GB RAM（推荐 4GB+）
- [ ] **磁盘空间**: 至少 1GB 可用空间
- [ ] **网络连接**: 可以访问外网（用于下载依赖）

### 必备软件
- [ ] **Git**: 已安装 (`git --version`)
- [ ] **Python**: 3.10 或更高版本 (`python3 --version`)
- [ ] **pip**: 已安装 (`pip3 --version`)

### 权限检查
- [ ] **目录权限**: 对项目目录有读写权限
- [ ] **sudo 权限**: (Linux) 有 sudo 权限用于安装系统包
- [ ] **Homebrew**: (macOS) 已安装 Homebrew (`brew --version`)

---

## 📦 部署过程检查

### 步骤 1: 获取部署脚本
- [ ] `dev-setup.sh` 脚本存在
- [ ] 脚本有执行权限: `chmod +x dev-setup.sh`

### 步骤 2: 运行部署脚本
- [ ] 运行: `./dev-setup.sh`
- [ ] 脚本执行过程中没有报错
- [ ] 脚本执行完成后显示"部署完成"

### 步骤 3: 项目代码
- [ ] 项目代码已克隆或更新到本地
- [ ] 当前工作目录在 sprintcycle 项目根目录
- [ ] `pyproject.toml` 文件存在

### 步骤 4: 虚拟环境创建
- [ ] `.venv/` 目录已创建
- [ ] `.venv/bin/` 目录下有 python 和 pip 可执行文件
- [ ] `.venv/lib/python3.x/site-packages/` 目录存在

### 步骤 5: Python 依赖安装
- [ ] 核心依赖已安装 (pydantic, litellm, diskcache 等)
- [ ] 开发依赖已安装 (pytest, mypy, ruff 等)
- [ ] MCP 相关依赖已安装 (uvicorn, starlette)
- [ ] sprintcycle 包以开发模式安装 (`pip list | grep sprintcycle`)

### 步骤 6: 便捷脚本创建
- [ ] `activate.sh` 已创建且有执行权限
- [ ] `run-dashboard.sh` 已创建且有执行权限
- [ ] `run-mcp.sh` 已创建且有执行权限
- [ ] `run-tests.sh` 已创建且有执行权限
- [ ] `run-lint.sh` 已创建且有执行权限

### 步骤 7: 配置文件创建
- [ ] `.env` 文件已创建
- [ ] `.env` 文件包含所有必要的配置项

---

## 🔧 环境配置检查

### API Key 配置
- [ ] `OPENAI_API_KEY` 已填入（或选择其他 LLM 提供商）
- [ ] `OPENAI_API_BASE` 已正确配置
- [ ] `OPENAI_MODEL` 已正确配置

### 可选 LLM 配置（按需配置）
- [ ] `DEEPSEEK_API_KEY`（如使用 DeepSeek）
- [ ] 其他 LLM 提供商配置

### SprintCycle 配置
- [ ] `SPRINTCYCLE_WORKSPACE` 已配置（默认为 `./workspace`）
- [ ] `SPRINTCYCLE_LOG_LEVEL` 已配置（默认为 `INFO`）
- [ ] `SPRINTCYCLE_MAX_ITERATIONS` 已配置（默认为 10）
- [ ] `SPRINTCYCLE_CACHE_DIR` 已配置（默认为 `./cache`）

### MCP 配置
- [ ] `MCP_TRANSPORT` 已配置（默认为 `stdio`）
- [ ] `MCP_SERVER_HOST`（如使用 SSE 传输）
- [ ] `MCP_SERVER_PORT`（如使用 SSE 传输）

---

## ✅ 部署验证检查

### 基础验证
- [ ] 可以激活虚拟环境: `source activate.sh`
- [ ] 激活后命令行提示符显示 `(.venv)`
- [ ] Python 版本正确: `python --version` (>= 3.10)
- [ ] pip 版本正确: `pip --version`
- [ ] 虚拟环境路径正确: `which python` 指向 `.venv/bin/python`

### SprintCycle CLI 验证
- [ ] sprintcycle 命令可用: `sprintcycle --help`
- [ ] 可以查看版本: `sprintcycle --version`
- [ ] CLI 帮助信息显示正常

### 导入验证
- [ ] 可以导入 sprintcycle 包: `python -c "import sprintcycle"`
- [ ] 可以导入核心模块: `python -c "from sprintcycle.cli import cli"`
- [ ] 没有 ModuleNotFoundError

### 依赖验证
- [ ] pydantic 可用: `python -c "import pydantic"`
- [ ] litellm 可用: `python -c "import litellm"`
- [ ] mcp 可用: `python -c "import mcp"`
- [ ] pytest 可用: `pytest --version`
- [ ] ruff 可用: `ruff --version`
- [ ] mypy 可用: `mypy --version`

### Dashboard 验证
- [ ] Dashboard 脚本可执行: `./run-dashboard.sh`
- [ ] uvicorn 可用: `python -c "import uvicorn"`

### MCP Server 验证
- [ ] MCP Server 脚本可执行: `./run-mcp.sh`

---

## 🧪 功能测试检查

### 基础功能
- [ ] sprintcycle CLI 帮助正常显示
- [ ] sprintcycle 版本信息正确

### 测试验证
- [ ] 可以运行测试脚本: `./run-tests.sh`
- [ ] pytest 可以正常执行
- [ ] 基础测试全部通过

### 代码质量检查
- [ ] 可以运行 lint: `./run-lint.sh`
- [ ] ruff 可以正常执行 lint
- [ ] mypy 可以正常执行类型检查

---

## 📚 文档检查

### 部署文档
- [ ] `DEV_SETUP_GUIDE.md` 存在且内容完整
- [ ] 快速开始部分清晰易懂
- [ ] 各平台步骤覆盖完整
- [ ] 故障排除部分覆盖常见问题

### 检查清单
- [ ] `DEPLOY_CHECKLIST.md`（本文件）存在
- [ ] 检查项完整
- [ ] 状态更新及时

### 项目文档
- [ ] `README.md` 存在且内容最新
- [ ] `pyproject.toml` 配置正确
- [ ] `config.yaml` 存在

---

## 🔍 常见问题排查清单

### 如果部署失败

#### 问题 A: 脚本执行报错
- [ ] 检查错误信息
- [ ] 尝试: `./dev-setup.sh --dry-run` 查看将执行的操作
- [ ] 尝试: `./dev-setup.sh --skip-system-deps` 跳过系统依赖
- [ ] 尝试: `./dev-setup.sh --force` 强制重新安装
- [ ] 参考 DEV_SETUP_GUIDE.md 中的"手动安装步骤"

#### 问题 B: Python 版本太低
- [ ] 检查当前 Python 版本: `python3 --version`
- [ ] 系统包管理器已更新
- [ ] 已尝试安装更新版本的 Python
- [ ] 已参考 DEV_SETUP_GUIDE.md 中的"故障排除"章节

#### 问题 C: pip 安装失败
- [ ] 检查网络连接
- [ ] 尝试使用国内镜像源
- [ ] 检查代理设置
- [ ] 升级 pip: `pip install --upgrade pip`

#### 问题 D: 权限错误
- [ ] 检查目录权限: `ls -la`
- [ ] 确保有写入权限
- [ ] (Linux) 检查 sudo 权限
- [ ] (macOS) 检查 Homebrew 权限

#### 问题 E: 虚拟环境创建失败
- [ ] 删除旧的 .venv 目录: `rm -rf .venv`
- [ ] 检查磁盘空间: `df -h`
- [ ] 手动创建: `python3 -m venv .venv`

#### 问题 F: Homebrew 未安装 (macOS)
- [ ] 访问 https://brew.sh 安装 Homebrew
- [ ] 安装完成后重新运行脚本

---

### 如果验证失败

#### 问题 1: sprintcycle 命令找不到
- [ ] 确保在虚拟环境中: `source .venv/bin/activate`
- [ ] 重新安装包: `pip install -e .`
- [ ] 检查 PATH: `echo $PATH`

#### 问题 2: ModuleNotFoundError
- [ ] 确认在虚拟环境中
- [ ] 重新安装: `pip install -e ".[dev,mcp-sse]"`
- [ ] 检查 site-packages: `ls .venv/lib/python*/site-packages/`

#### 问题 3: 测试失败
- [ ] 确认测试依赖已安装
- [ ] 清除 pytest 缓存: `rm -rf .pytest_cache`
- [ ] 清除 Python 缓存: `find . -name "__pycache__" -exec rm -rf {} +`
- [ ] 单独运行单个测试文件

#### 问题 4: Dashboard 启动失败
- [ ] 确认 uvicorn 已安装
- [ ] 检查端口是否被占用: `lsof -i :8000`
- [ ] 查看错误日志

#### 问题 5: MCP Server 启动失败
- [ ] 确认 mcp 已安装
- [ ] 检查配置是否正确
- [ ] 查看错误日志

---

## 🎯 部署完成确认

### 最终检查
- [ ] ✅ 所有部署步骤都已完成
- [ ] ✅ 所有验证测试都已通过
- [ ] ✅ 所有配置都已正确设置
- [ ] ✅ 文档完整且最新
- [ ] ✅ 可以正常使用 SprintCycle 基本功能

### 部署信息记录
- **部署日期**: _______________
- **部署人员**: _______________
- **操作系统**: _______________
- **Python 版本**: _______________
- **SprintCycle 版本**: _______________
- **LLM 提供商**: _______________
- **备注**: _________________________

---

## 📋 维护检查清单（部署后）

### 日常维护
- [ ] 定期更新依赖: `pip install -e ".[dev,mcp-sse]" --upgrade`
- [ ] 定期运行测试: `./run-tests.sh`
- [ ] 定期清理缓存: `rm -rf .pytest_cache __pycache__ .ruff_cache .mypy_cache`
- [ ] 检查日志文件大小，定期清理

### 版本更新
- [ ] 更新代码前备份当前环境（可选）
- [ ] 拉取最新代码: `git pull origin main`
- [ ] 重新安装依赖: `pip install -e ".[dev,mcp-sse]" --upgrade`
- [ ] 运行所有测试确保更新后正常工作

### 便捷脚本使用
- [ ] `./run-dashboard.sh` - 启动 Web Dashboard
- [ ] `./run-mcp.sh` - 启动 MCP Server
- [ ] `./run-tests.sh` - 运行测试套件
- [ ] `./run-lint.sh` - 运行代码质量检查
- [ ] `source activate.sh` - 激活开发环境

---

## 💡 最佳实践

1. **始终使用虚拟环境**，不要使用系统 Python
2. **定期更新依赖**，但注意兼容性
3. **运行测试**，确保每次修改后功能正常
4. **备份配置**，特别是 .env 文件
5. **记录问题和解决方案**，帮助团队其他成员
6. **使用版本控制**，跟踪配置变更
7. **使用便捷脚本**，提高开发效率
8. **参考 DEV_SETUP_GUIDE.md**，解决常见问题

---

## 📞 支持与反馈

如果在部署过程中遇到问题：

1. 参考 `DEV_SETUP_GUIDE.md` 中的"常见问题排查 (FAQ)"章节
2. 查看 `DEV_SETUP_GUIDE.md` 中的"手动安装步骤"
3. 检查项目的 GitHub Issues
4. 提交新的 Issue 并提供:
   - 操作系统和版本
   - Python 版本
   - 完整的错误信息
   - 已尝试的解决方法

---

**本清单最后更新日期**: 2026-05-04  
**版本**: 2.0.0
**对应脚本**: dev-setup.sh v2.0.0
