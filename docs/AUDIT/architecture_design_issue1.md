# SprintCycle 架构分层设计方案
## 问题 #1 详解：api.py 与 interfaces/http/ 的关系

---

## 📋 当前架构分析

### 现状

```
presentation/server.py (FastAPI 应用层)
    │
    ├─ SprintCycle() ← api.py (核心业务逻辑类)
    │
    ├─ InternalAPIService(SprintCycle)
    │   └─ build_internal_router() ← interfaces/http/internal.py
    │
    └─ PublicAPIService(SprintCycle)
        └─ build_public_router() ← interfaces/http/public.py
```

**✅ 架构连接正确** - `interfaces/http/` 已经被 `presentation/server.py` 使用。

---

## ❌ 真正的架构问题

### 问题：api.py 方法过多（80个），职责不清

根据 Final Architecture：

```
Layer 1: Dashboard / REST API ─── presentation/server.py ✓
Layer 2: Internal / Public API ── interfaces/http/ ✓
Layer 3: Application Services ─── application/services/ ✓
Layer 4: Core Domain ──────────── api.py (SprintCycle 类) ← 太胖了
```

**问题**：`api.py` 有 80 个方法，既包含 Dashboard 视图逻辑，又包含 Public API 逻辑，还包含内部编排逻辑。

---

## 🎯 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    presentation/server.py                    │
│                        (FastAPI 应用)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│ InternalAPIService  │   │  PublicAPIService   │
│   (Dashboard 视图)  │   │  (外部集成)          │
└─────────┬───────────┘   └─────────┬───────────┘
          │                           │
          ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   SprintCycle (api.py)                       │
│                   Core Domain (核心逻辑)                      │
│                                                              │
│  只保留真正的核心能力:                                        │
│  - execute_sprint()                                          │
│  - create_plan()                                             │
│  - get_status()                                              │
│  - rollback()                                                │
│                                                              │
│  不应该有的:                                                  │
│  - console_overview() ← 移到 InternalAPIService              │
│  - platform_overview() ← 移到 InternalAPIService             │
│  - evolution_overview_*() ← 移到 InternalAPIService          │
│  - suggestion_overview_*() ← 移到 InternalAPIService          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 详细拆分方案

### 1. api.py 应该保留的方法（核心能力）

```python
class SprintCycle:
    """核心业务逻辑 - 只保留不可分割的核心能力"""
    
    # === 核心执行 ===
    def execute_plan(self, task_id: str, ...) -> RunResult
    def get_status(self, execution_id: str) -> StatusResult
    def stop(self, execution_id: str) -> StopResult
    def rollback(self, execution_id: str) -> RollbackResult
    
    # === 生命周期 ===
    def diagnose(self, execution_id: str) -> DiagnoseResult
    def get_metrics(self, execution_id: str) -> MetricsResult
    
    # === 治理 ===
    def check_governance(self, ...) -> GovernanceResult
    
    # === 演化（核心能力）===
    def evolve(self, ...) -> EvolutionResult
    def get_evolution_history(self, ...) -> EvolutionHistoryResult
```

### 2. 应该移到 InternalAPIService 的方法（Dashboard 视图）

```python
class InternalAPIService:
    """Dashboard 专用 - 聚合多个 core 方法"""
    
    # === 概览视图 ===
    def console_overview(self, ...) -> ConsoleOverviewResult
    def platform_overview(self, ...) -> PlatformOverviewResult
    def management_overview(self, ...) -> ManagementOverviewResult
    
    # === 演化视图 ===
    def evolution_overview(self, ...) -> EvolutionOverviewResult
    def evolution_overview_cli(self, ...) -> EvolutionOverviewResult
    def evolution_overview_dashboard(self, ...) -> EvolutionOverviewResult
    
    # === 建议视图 ===
    def suggestion_overview(self, ...) -> SuggestionOverviewResult
    def suggestion_overview_cli(self, ...) -> SuggestionOverviewResult
    def suggestion_overview_dashboard(self, ...) -> SuggestionOverviewResult
    def review_suggestion(self, ...) -> ReviewResult
    
    # === 部署视图 ===
    def deploy_view(self, ...) -> DeployViewResult
    def fitness_view(self, ...) -> FitnessViewResult
```

### 3. 应该移到 PublicAPIService 的方法（外部集成）

```python
class PublicAPIService:
    """外部系统集成 - 只保留稳定 API"""
    
    def plan(self, context: RequestContext, **payload) -> dict
    def run(self, context: RequestContext, **payload) -> dict
    def status(self, context: RequestContext, execution_id: str) -> dict
    def stop(self, context: RequestContext, execution_id: str) -> dict
    def rollback(self, context: RequestContext, execution_id: str) -> dict
    def diagnose(self, context: RequestContext) -> dict
```

---

## 🚀 实施步骤

### Phase 1: 确认当前委托模式（已完成 ✅）

```python
# presentation/server.py 已经有了正确的连接
def create_app():
    sc = SprintCycle(project_path=project_path)
    internal_api = InternalAPIService(sc)  # 传入 SprintCycle 实例
    public_api = PublicAPIService(sc)      # 传入 SprintCycle 实例
    
    app.include_router(build_public_router(public_api, project_path))
    app.include_router(build_internal_router(internal_api, project_path))
```

### Phase 2: 拆分 api.py 方法（核心任务）

#### 步骤 2.1: 识别 api.py 中的 Dashboard 方法

```python
# api.py 中需要移到 InternalAPIService 的方法
DASHBOARD_METHODS = [
    'console_overview',
    'console_overview_cli', 
    'console_overview_dashboard',
    'platform_overview',
    'management_overview_payload',
    'management_overview',
    'management_overview_cli',
    'management_overview_dashboard',
    'evolution_overview',
    'evolution_overview_cli',
    'evolution_overview_dashboard',
    'suggestion_overview',
    'suggestion_overview_cli',
    'suggestion_overview_dashboard',
    'suggestion_review',
    'review_suggestion',
    'approve_suggestion',
    'reject_suggestion',
    'fitness_view',
    'fitness_payload',
    'deploy_view',
    'deploy_payload',
    # ... 更多
]
```

#### 步骤 2.2: 创建方法迁移脚本

```python
# 伪代码：迁移方法
def migrate_method(method_name: str, from_class: str, to_class: str):
    """
    1. 从 api.py 复制方法到 InternalAPIService
    2. 在 api.py 中保留委托：
       def console_overview(self, ...):
           return self._internal_api.console_overview(...)
    3. 更新调用方
    """
```

### Phase 3: 验证路由连接

```bash
# 测试 FastAPI 路由
curl http://localhost:8000/api/console/overview
# 应该返回 console_overview 的结果

curl http://localhost:8000/api/v1/status
# 应该返回 status 的结果
```

---

## 📁 预期文件变更

```
sprintcycle/
├── api.py                          # 精简到 ~30 个核心方法
├── application/
│   ├── internal_api_service.py     # 聚合 Dashboard 视图 (~20 个方法)
│   └── public_api_service.py      # 外部集成 (~10 个方法)
└── interfaces/http/
    ├── internal.py                 # Dashboard HTTP 路由
    └── public.py                   # Public HTTP 路由
```

---

## ✅ 验收标准

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| api.py 方法数 | 80 | < 30 | ❌ |
| api.py 行数 | 595 | < 200 | ❌ |
| InternalAPIService 方法数 | ? | 20-30 | ❌ |
| PublicAPIService 方法数 | ? | 6-10 | ❌ |
| HTTP 路由正确连接 | ✅ | ✅ | ✅ |

---

## 🎯 总结

### 当前状态
- ✅ `interfaces/http/` 已经正确连接
- ✅ `presentation/server.py` 正确使用了路由
- ❌ `api.py` 方法过多（80个），应该拆分

### 解决方案
1. **保留** `api.py` 作为核心业务逻辑类
2. **拆分** Dashboard 视图方法到 `InternalAPIService`
3. **保留委托** 在 `api.py` 中，保持向后兼容
4. **逐步迁移** 最终移除 api.py 中的冗余方法
