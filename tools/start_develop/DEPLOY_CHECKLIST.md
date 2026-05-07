# SprintCycle 部署检查清单

> 📋 确保 SprintCycle 开发环境部署的每一步都正确完成。

---

## 🚀 部署前检查

### 系统环境
- [ ] **操作系统**: macOS / Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 34+, Arch)
- [ ] **内存**: 至少 2GB RAM（推荐 4GB+）
- [ ] **磁盘空间**: 至少 1GB 可用空间
- [ ] **网络连接**: 可以访问外网

### 必备软件
- [ ] **Git**: `git --version`
- [ ] **Python**: 3.11 或更高版本 `python3 --version`
- [ ] **pip**: `pip3 --version`

---

## 📦 部署过程检查

### 步骤 1: 运行部署脚本

```bash
cd sprintcycle
./tools/start_develop/dev-setup.sh
```

- [ ] 脚本执行过程中没有报错
- [ ] 脚本执行完成后显示"部署完成"

### 步骤 2: 虚拟环境
- [ ] `.venv/` 目录已创建
- [ ] `.venv/bin/python` 可执行

### 步骤 3: Python 依赖
- [ ] sprintcycle 包已安装: `pip list | grep sprintcycle`
- [ ] 核心依赖可用: pydantic, litellm
- [ ] 开发依赖可用: pytest, ruff, mypy

### 步骤 4: 便捷脚本
- [ ] `activate.sh` 已创建
- [ ] `run-dashboard.sh` 已创建
- [ ] `run-mcp.sh` 已创建
- [ ] `run-tests.sh` 已创建
- [ ] `run-lint.sh` 已创建

### 步骤 5: 配置文件
- [ ] `.env` 文件已创建

---

## 🔧 配置检查

### API Key 配置
- [ ] `OPENAI_API_KEY` 已填入（或选择其他 LLM）
- [ ] `OPENAI_MODEL` 已配置

### 可选配置
- [ ] `SPRINTCYCLE_WORKSPACE`（默认 `./workspace`）
- [ ] `SPRINTCYCLE_LOG_LEVEL`（默认 `INFO`）

---

## ✅ 部署验证

### 基础验证
```bash
source tools/start_develop/activate.sh
```

- [ ] 虚拟环境激活成功，提示符显示 `(.venv)`
- [ ] `python --version` 显示 >= 3.11
- [ ] `pip --version` 正常

### SprintCycle 验证
```bash
sprintcycle --help
```

- [ ] CLI 帮助正常显示
- [ ] `sprintcycle --version` 显示版本

### 导入验证
```bash
python -c "import sprintcycle; print(sprintcycle.__version__)"
```

- [ ] sprintcycle 包可正常导入
- [ ] 无 ModuleNotFoundError

### 依赖验证
- [ ] `pytest --version`
- [ ] `ruff --version`
- [ ] `mypy --version`

---

## 🧪 功能测试

### 运行测试
```bash
./tools/start_develop/run-tests.sh
```

- [ ] 测试可正常执行
- [ ] 基础测试通过

### 代码检查
```bash
./tools/start_develop/run-lint.sh
```

- [ ] ruff lint 通过
- [ ] mypy 类型检查完成

---

## 📚 文档检查

- [ ] `DEVELOPMENT_GUIDE.md` 存在
- [ ] `DEPLOY_CHECKLIST.md`（本文件）存在
- [ ] `README.md` 存在且内容最新

---

## ❓ 故障排查

### 常见问题

| 问题 | 解决方法 |
|------|----------|
| sprintcycle 命令找不到 | 确保在虚拟环境中：`source .venv/bin/activate` |
| ModuleNotFoundError | 重新安装：`pip install -e ".[full,dev,mcp-sse]"` |
| 测试失败 | 清除缓存：`rm -rf .pytest_cache __pycache__` |
| 权限错误 (Linux) | 检查 sudo 权限：`sudo -v` |

### 详细文档
参考 `DEVELOPMENT_GUIDE.md` 中的"常见问题"章节。

---

## 🎯 部署完成确认

- [ ] 所有部署步骤都已完成
- [ ] 所有验证测试都已通过
- [ ] `.env` 文件已配置 API Key
- [ ] 可以正常使用 SprintCycle

---

**文档版本**: 2.0  
**最后更新**: 2024
