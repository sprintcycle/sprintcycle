# SprintCycle 自动化验证工具使用指南

## 📖 概述

本指南介绍 SprintCycle 的自动化验证工具体系，帮助团队实现**无需人工介入**的自动化升级验证，确保架构不变性和功能正确性。

---

## 🛠️ 工具清单

### 1. 架构验证器
**文件**: `scripts/validate_architecture.py`

自动验证代码是否符合架构规范，基于 `ARCHITECTURE_INVARIANTS.md` 和架构约束规则。

**检查项**:
- ✅ 端口定义数量（应为 17 个）
- ✅ 领域层纯粹性（无外部框架依赖）
- ✅ 聚合根不可变性（@dataclass(frozen=True)）
- ✅ 端口/适配器分离
- ✅ 组合根模式
- ✅ 六边形架构层依赖
- ✅ 前后端契约对齐
- ✅ Hooks 模块结构
- ✅ 兼容代码检测

### 2. Playwright E2E 测试套件
**文件**: `frontend/e2e/architecture.spec.ts`

自动化 Web UI 功能验证，覆盖所有主要页面和用户流程。

**测试范围**:
- Dashboard 主页面加载
- 导航菜单完整性
- 生命周期状态机流程
- 治理页面功能
- HITL 页面验证
- 历史记录页面
- 页面路由切换
- 响应式布局
- API 接口健康检查
- WebSocket 连接测试

### 3. 升级验证器
**文件**: `scripts/auto_upgrade_verify.py`

完整的 5 阶段升级验证流程，一次性验证所有关键点。

**验证阶段**:
1. Phase 1: 架构不变性验证
2. Phase 2: 单元测试验证
3. Phase 3: API 契约验证
4. Phase 4: E2E 测试验证
5. Phase 5: 文档同步验证

### 4. 统一运行脚本
**文件**: `scripts/run_auto_verify.sh`

一键运行所有验证的入口脚本，适合日常验证和 CI/CD 集成。

---

## 🚀 快速开始

### 环境要求

```bash
# Python 3.11+
python --version

# Node.js 18+ (用于 E2E 测试)
node --version

# Playwright (自动安装)
cd frontend && npm install
```

### 一键验证

```bash
# 运行完整验证
./scripts/run_auto_verify.sh
```

输出示例:
```
🚀 SprintCycle 自动化验证开始

========================================================
Phase 1: 架构不变性验证
========================================================
🏗️ 开始架构不变性验证...
✅ 通过: 11
⚠️ 警告: 12
❌ 错误: 4
🎉 架构验证通过

========================================================
Phase 2: 单元测试验证
========================================================
...
🎉 所有验证通过！
```

---

## 📋 详细使用说明

### 1. 架构验证器

#### 基本用法

```bash
# 标准运行
python scripts/validate_architecture.py

# 严格模式（警告视为错误）
python scripts/validate_architecture.py --strict
```

#### 输出说明

```
🏗️ 开始架构不变性验证...

======================================================================
✅ 通过: 11
⚠️ 警告: 12
❌ 错误: 4
======================================================================

📋 验证结果详情:

✅ 通过项:
  - 端口定义数量正确: 17 个
  - 领域层纯粹性检查通过
  ...

⚠️ 警告项:
  - 可能存在兼容代码: xxx.py 包含 'compatibility'
  ...

❌ 错误项:
  - 架构层依赖违规: xxx.py 依赖了 application (不允许)
  ...
```

#### 退出码

- `0`: 所有检查通过
- `1`: 存在错误或严格模式下存在警告

---

### 2. 升级验证器

#### 基本用法

```bash
# 完整验证（生成 JSON 报告）
python scripts/auto_upgrade_verify.py

# 查看详细报告
cat upgrade_verification_report.json
```

#### 输出报告

```json
{
  "architecture": {
    "passed": true,
    "stdout": "...",
    "stderr": ""
  },
  "unit_tests": {
    "passed": true,
    "passed_count": 120,
    "failed_count": 0
  },
  "api_contract": {
    "passed": true
  },
  "e2e": {
    "passed": true
  },
  "documentation": {
    "passed": true
  }
}
```

---

### 3. Playwright E2E 测试

#### 前置条件

```bash
# 安装前端依赖
cd frontend
npm install

# 安装 Playwright 浏览器
npx playwright install chromium
```

#### 运行测试

```bash
# 在 frontend 目录运行
cd frontend
npx playwright test

# 指定浏览器
npx playwright test --project=chromium

# 生成测试报告
npx playwright test --reporter=html
```

#### 测试配置

编辑 `frontend/playwright.config.ts`:

```typescript
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:8765',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
```

---

### 4. 单元测试

#### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_lifecycle_service.py -v

# 快速运行（遇到失败停止）
python -m pytest tests/ -x

# 生成覆盖率报告
python -m pytest tests/ --cov=sprintcycle --cov-report=html
```

---

## 🔄 CI/CD 集成

### GitHub Actions

创建 `.github/workflows/auto-verify.yml`:

```yaml
name: Auto Verification

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
          
      - name: Run architecture validation
        run: .venv/bin/python scripts/validate_architecture.py
        
      - name: Run unit tests
        run: .venv/bin/python -m pytest tests/ -v --tb=short
        
      - name: Setup Node.js
        if: success()
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Run E2E tests
        if: success()
        run: |
          cd frontend
          npm install
          npx playwright install --with-deps chromium
          npx playwright test
```

### 本地 Git Hook

创建 `.githooks/pre-commit`:

```bash
#!/bin/bash
# SprintCycle pre-commit 钩子

echo "🔍 Running pre-commit validation..."

# 运行架构验证
python scripts/validate_architecture.py
if [ $? -ne 0 ]; then
    echo "❌ Architecture validation failed"
    exit 1
fi

# 运行快速测试
python -m pytest tests/ -x -q
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo "✅ Pre-commit validation passed"
```

激活钩子:

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

---

## 🎯 验证流程图

```
代码提交/合并请求
        ↓
┌─────────────────────────────────┐
│  GitHub Actions CI              │
├─────────────────────────────────┤
│  1. 架构验证                     │
│     ↓                           │
│  2. 单元测试                    │
│     ↓                           │
│  3. API 契约测试                │
│     ↓                           │
│  4. E2E 测试                    │
│     ↓                           │
│  5. 文档验证                    │
│     ↓                           │
│  6. 汇总报告                    │
└─────────────────────────────────┘
        ↓
   所有通过? ──→ 是 ──→ 合并/部署
        │
       否
        ↓
   返回失败报告
```

---

## 🔧 架构违规修复记录

### 已修复的架构违规

| 违规文件 | 问题描述 | 修复方案 |
|---------|---------|---------|
| `arch_guard/engine.py` | 领域层依赖应用层获取适配器 | 使用端口注入模式 + 全局注册机制 |
| `platform/overview.py` | 领域层依赖应用层容器 | 使用全局注册机制获取适配器 |
| `interfaces/config.py` | 配置加载器延迟导入容器 | 移除延迟导入，使用全局注册 |

### 修复策略：依赖注入 + 全局注册

#### 1. 端口注入模式（ArchGuardEngine）

```python
# Before: 延迟导入（违规）
def _load_adapters(self):
    from sprintcycle.application.composition.di_container import container
    self._adapter = container.governance.adapter()

# After: 构造函数注入
def __init__(self, config, adapter=None):
    self._adapter = adapter
```

#### 2. 全局注册机制

```python
# 在领域层定义注册函数
_adapter_registry = None

def register_adapter(adapter):
    global _adapter_registry
    _adapter_registry = adapter

def get_adapter():
    if _adapter_registry is None:
        raise RuntimeError("适配器未注册")
    return _adapter_registry
```

#### 3. 容器初始化时注册

```python
# 在 di_container.py 的 create_container()
def create_container(project_path="."):
    global _container_instance
    _container_instance = Container(project_path)
    
    # 注册适配器到领域层
    from domain.module import register_adapter
    register_adapter(_container_instance.adapter())
    
    return _container_instance
```

### 验证修复结果

```bash
python scripts/validate_architecture.py
# ✅ 错误: 0
# ⚠️ 警告: 12 (兼容代码提示)
```

---

## ⚙️ 高级配置

### 架构验证器配置

编辑 `scripts/validate_architecture.py`:

```python
class ArchitectureValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # 可配置的检查项
        self.expected_port_count = 17  # 端口数量
        self.forbidden_imports = [     # 禁止的外部依赖
            "fastapi", "uvicorn", "sqlalchemy"
        ]
```

### E2E 测试配置

编辑 `frontend/playwright.config.ts`:

```typescript
// 添加自定义配置
const config = {
  // 超时配置
  timeout: 30000,
  
  // 重试配置
  retries: 2,
  
  // 并行配置
  workers: 4,
  
  // 报告配置
  reporter: [['html', { outputFolder: 'playwright-report' }]],
}
```

---

## 🔧 故障排查

### 常见问题

#### 1. 架构验证失败

```bash
# 查看详细错误
python scripts/validate_architecture.py

# 查看具体违规
# 修复相应的架构违规后重新验证
```

#### 2. E2E 测试失败

```bash
# 安装 Playwright 依赖
cd frontend
npx playwright install-deps
npx playwright install chromium

# 运行单个测试
npx playwright test smoke.spec.ts

# 查看测试视频/截图
ls playwright-report/
```

#### 3. 单元测试失败

```bash
# 运行详细测试
python -m pytest tests/ -v --tb=long

# 运行特定测试
python -m pytest tests/test_lifecycle_service.py -v -k "test_name"

# 查看测试覆盖
python -m pytest tests/ --cov=sprintcycle --cov-report=term-missing
```

### 性能优化

#### 加速测试

```bash
# 使用 pytest-xdist 并行测试
pip install pytest-xdist
pytest tests/ -n auto

# 跳过慢速测试
pytest tests/ -m "not slow"
```

---

## 📊 验证指标

### 通过标准

| 指标 | 目标值 |
|------|--------|
| 架构验证 | 0 错误 |
| 单元测试通过率 | 100% |
| API 契约测试通过率 | 100% |
| E2E 测试通过率 | 100% |
| 测试覆盖率 | ≥ 80% |

### 监控指标

建议在 CI/CD 中监控:

- 测试通过率趋势
- 测试执行时间
- 覆盖率变化
- 架构违规数量

---

## 📚 相关文档

- [ARCHITECTURE_INVARIANTS.md](../ARCHITECTURE_INVARIANTS.md) - 架构不变性规范
- [sprint-optimize.md](../.cursor/commands/sprint-optimize.md) - 优化工作流
- [CI/CD 配置](../.github/workflows/) - 持续集成配置
- [生产部署指南](./production/PRODUCTION_DEPLOYMENT_GUIDE.md) - 生产环境部署

---

## 🤝 贡献指南

### 添加新的验证规则

1. 编辑 `scripts/validate_architecture.py`
2. 添加新的验证方法:

```python
def _validate_new_rule(self):
    """验证新规则"""
    # 实现验证逻辑
    if passed:
        self.passed.append("新规则检查通过")
    else:
        self.errors.append("新规则检查失败")
```

3. 在 `validate()` 方法中调用:

```python
def validate(self):
    # ... 现有验证 ...
    self._validate_new_rule()
```

### 添加新的 E2E 测试

1. 编辑 `frontend/e2e/architecture.spec.ts`
2. 添加新的测试:

```typescript
test('新功能验证', async ({ page }) => {
  await page.goto('/new-feature')
  await expect(page.getByText('预期内容')).toBeVisible()
})
```

---

## ❓ 常见问题

**Q: 架构验证失败但代码能运行？**
A: 架构验证确保长期可维护性，即使当前能运行，架构违规也会导致未来维护困难。

**Q: E2E 测试超时？**
A: 增加超时配置或检查网络连接。也可以在本地运行调试。

**Q: 如何跳过某些验证？**
A: 不建议跳过，但可以在 `auto_upgrade_verify.py` 中注释相应阶段。

**Q: 验证脚本在哪里配置？**
A: 主要在 `scripts/validate_architecture.py` 和 `frontend/playwright.config.ts`。

---

## 🎉 最佳实践

1. **每次提交前运行验证** - 使用 pre-commit 钩子
2. **PR 前完整验证** - 确保所有检查通过
3. **定期审查报告** - 监控指标趋势
4. **及时修复违规** - 不要积累技术债务
5. **更新验证规则** - 随着项目演进调整标准

---

*最后更新: 2026-06-01*
