# SprintCycle 架构重构 - 实施代码示例

## 📋 核心问题

`api.py` 有 80 个方法，应该拆分成：
- `api.py`: 核心业务逻辑（~30 个方法）
- `InternalAPIService`: Dashboard 视图（~30 个方法）
- `PublicAPIService`: 外部集成（~10 个方法）

---

## 🔧 实施示例

### Step 1: 定义需要迁移的 Dashboard 方法

```python
# sprintcycle/application/internal_api_service.py

# 在 InternalAPIService.__init__ 中添加新属性
def __init__(self, sc: SprintCycle):
    self._sc = sc
    
    # 聚合 dashboard 视图方法
    self._dashboard_views = DashboardViewService(
        project_path=sc.project_path,
    )
    self._management_service = ManagementOverviewService(
        project_path=sc.project_path,
        suggestion_facade=sc._suggestion,
    )

# 添加 dashboard 视图方法
async def console_overview(self, limit: int = 20, **kwargs) -> dict:
    """Dashboard 控制台概览"""
    # 直接在这里实现或委托给 service
    return await self._sc.console_overview(limit=limit, **kwargs)

async def platform_overview(self, **kwargs) -> dict:
    """平台概览"""
    return await self._sc.platform_overview(**kwargs)

async def suggestion_overview(self, **kwargs) -> dict:
    """建议概览"""
    return await self._sc.suggestion_overview(**kwargs)
```

### Step 2: 更新 api.py 保留委托（向后兼容）

```python
# sprintcycle/api.py

class SprintCycle:
    """核心业务逻辑 - 保留委托，保持向后兼容"""
    
    def __init__(self, ...):
        # ... 现有代码 ...
        
        # 新增：内部 API 服务引用
        self._internal_api: Optional[InternalAPIService] = None
        self._public_api: Optional[PublicAPIService] = None
    
    def _get_internal_api(self) -> InternalAPIService:
        """懒加载 InternalAPIService"""
        if self._internal_api is None:
            self._internal_api = InternalAPIService(self)
        return self._internal_api
    
    # === 保留委托方法（向后兼容）===
    
    async def console_overview(self, limit: int = 20, **kwargs) -> dict:
        """保留：委托给 InternalAPIService"""
        return await self._get_internal_api().console_overview(limit=limit, **kwargs)
    
    async def platform_overview(self, **kwargs) -> dict:
        """保留：委托给 InternalAPIService"""
        return await self._get_internal_api().platform_overview(**kwargs)
    
    async def suggestion_overview(self, **kwargs) -> dict:
        """保留：委托给 InternalAPIService"""
        return await self._get_internal_api().suggestion_overview(**kwargs)
    
    # === 核心方法（不委托）===
    
    async def execute_plan(self, task_id: str, **kwargs) -> RunResult:
        """核心执行 - 不委托"""
        # 实现核心逻辑
        ...
    
    async def rollback(self, execution_id: str) -> RollbackResult:
        """回滚 - 不委托"""
        # 实现核心逻辑
        ...
```

### Step 3: 更新 presentation/server.py

```python
# sprintcycle/presentation/server.py

def create_app(project_path: str = ".") -> FastAPI:
    sc = SprintCycle(project_path=project_path)
    
    # 创建服务层
    internal_api = InternalAPIService(sc)
    public_api = PublicAPIService(sc)
    
    # 将服务注入到 SprintCycle（用于委托）
    sc._internal_api = internal_api
    sc._public_api = public_api
    
    # 构建路由
    app = FastAPI(...)
    app.include_router(build_public_router(public_api, project_path))
    app.include_router(build_internal_router(internal_api, project_path))
    
    return app
```

---

## 📊 迁移清单

### 需要从 api.py 移到 InternalAPIService 的方法

| 方法名 | 行数估算 | 依赖服务 |
|--------|---------|---------|
| `console_overview*` | ~30 | DashboardViewService |
| `platform_overview*` | ~20 | PlatformSummaryService |
| `management_overview*` | ~25 | ManagementOverviewService |
| `evolution_overview*` | ~30 | EvolutionVersionService |
| `suggestion_overview*` | ~25 | SuggestionFacade |
| `fitness_view*` | ~15 | FitnessEvaluator |
| `deploy_view*` | ~15 | DeploymentSpecService |

### 保留在 api.py 的核心方法

| 方法名 | 说明 |
|--------|------|
| `execute_plan` | 核心执行 |
| `get_status` | 状态查询 |
| `stop` | 停止执行 |
| `rollback` | 回滚 |
| `diagnose` | 诊断 |
| `check_governance` | 治理检查 |

---

## ✅ 迁移后的架构

```
presentation/server.py
    │
    ├─ SprintCycle (api.py) ─── 核心业务逻辑 (~20 方法)
    │       │
    │       ├─ _internal_api ───→ InternalAPIService
    │       └─ _public_api ────→ PublicAPIService
    │
    ├─ InternalAPIService ─── Dashboard 视图 (~20 方法)
    │
    └─ PublicAPIService ────── 外部集成 (~10 方法)
```

---

## 🚀 执行建议

### 方案 A: 一次性重构（推荐）

```bash
# 1. 备份
cp sprintcycle/api.py sprintcycle/api.py.bak

# 2. 识别所有 Dashboard 方法
grep -n "def.*overview\|def.*view\|def.*dashboard" sprintcycle/api.py

# 3. 创建迁移脚本
python scripts/migrate_methods.py

# 4. 测试
pytest tests/test_api_layering_services.py
```

### 方案 B: 渐进式重构

```bash
# 每次迭代迁移一个方法家族
# Iteration 1: console_overview*
# Iteration 2: platform_overview*
# Iteration 3: management_overview*
# ...
```

---

## 📝 注意事项

1. **向后兼容**: 迁移过程中保持 `api.py` 方法可用
2. **测试覆盖**: 每迁移一个方法，确保测试通过
3. **文档更新**: 更新 FINAL_ARCHITECTURE.md 反映最新架构
4. **CI 验证**: 确保 `make ci-local` 全绿后再合并
