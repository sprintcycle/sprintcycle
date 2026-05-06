# SprintCycle 5 分钟快速开始

本文档帮助你在 5 分钟内快速上手 SprintCycle。

### 与 Scrum 的对应（读代码/写集成时）

| 你看到的名字 | Scrum 里怎么理解 |
|--------------|------------------|
| **ReleasePlan / plan YAML** | 多 Sprint 的**可执行交付计划**（非整份 Product Backlog）；根包 `from sprintcycle import ReleasePlan` 与 `release_plan.models` 为同一类型。 |
| **`PRDSprint` / `sprints[]`** | 一次 **Sprint**：`goals` ≈ Sprint Goal；`tasks` ≈ Sprint Backlog。 |
| **`PRDTask` / YAML `description:`** | Sprint 内一条工作说明，≈ **Sprint Backlog Item**；别名 `SprintBacklogItem`；代码字段 **`description`**。 |
| **`SprintOrchestrator`** | **Sprint 执行编排**（`orchestration` 主实现）。 |

完整分级改造见 **[`docs/DESIGN_SCRUM_NAMING_MIGRATION.md`](DESIGN_SCRUM_NAMING_MIGRATION.md)**。

代码治理、质量门禁与 Docker 产品一键启动的**工程方案与可执行 Issue 列表**见 **[`docs/GOVERNANCE_ENGINEERING.md`](GOVERNANCE_ENGINEERING.md)**；golden / `model-compare` 见 **[`docs/GOVERNANCE_GOLDEN.md`](GOVERNANCE_GOLDEN.md)**。

在同一项目根下做**双遍 pytest 对比**且未传 pytest 参数时，`--quick` 会默认只跑 **`golden`** 标记用例（大仓库更省时间）；可按需叠加 `--env1` / `--env2` `KEY=VALUE` 切换模型等环境：

```bash
sprintcycle governance model-compare --quick
```

未提供 `sprintcycle.toml` 时，运行态默认 **质量档位 L2**（会跑 pytest / 覆盖率相关门禁）且执行状态使用 **SQLite**（`.sprintcycle/data/sprintcycle.db`）。原型速写可设 `[quality] profile = "fast"` 或 `level = "L0"`；完整约定见仓库内 **`sprintcycle.toml.example`** 与普通任务模板 **`sprintcycle/release_plan/templates/normal_task.yaml`**。

## 安装

```bash
pip install sprintcycle
```

或者从源码安装：

```bash
git clone https://github.com/your-org/sprintcycle.git
cd sprintcycle
pip install -e .
```

开发 Web Dashboard（Vue 3 + Vite）时，建议同时安装：`pip install -e ".[dashboard,dev]"`，并在 `frontend` 目录安装 Node 依赖：`cd frontend && npm install`。

### Web Dashboard 怎么用

**依赖**：`pip install -e ".[dashboard]"`（或 `full`）。

**生产模式（只起 Python，托管构建后的静态文件）**  

先在前端工程目录打包，再启动服务（默认端口 **8080**）：

```bash
cd frontend && npm ci && npm run build
cd ..
sprintcycle dashboard --host 127.0.0.1 --port 8080
```

浏览器访问终端里打印的地址；需使用 **构建后的** 完整 UI，而不是仓库里仅占位用的 `static/index.html`。

**一键开发（源码克隆，子进程启动 Vite）**  

确保仓库根下存在 `frontend/`，且已执行 `cd frontend && npm install`：

```bash
sprintcycle dashboard --dev
```

- 后端 API：`http://127.0.0.1:8080`（与 `--port` 一致）  
- 前端开发服务器：`http://localhost:5173` — **请用浏览器打开此地址**（Vite 将 `/api` 代理到后端）。  
- CLI 会为子进程设置 `VITE_PROXY_TARGET=http://127.0.0.1:<port>`；也可自行导出该变量后运行 `npm run dev`。

**手动双终端**（与 `--dev` 等价）：

```bash
# 终端 1
SPRINTCYCLE_ENV=development sprintcycle dashboard --port 8080

# 终端 2
cd frontend && npm run dev
```

发版前若要打含完整前端的 wheel，请参阅 **`docs/RELEASE_CHECKLIST.md`**。

### 人机卡点（HITL）

在 **`sprintcycle.toml`** 中增加 **`[hitl]`**（或环境变量 **`SPRINTCYCLE_HITL_*`**）可在执行过程中插入**人工确认**：默认将待决请求写入项目根下 **`.sprintcycle/hitl.db`**（可用 **`db_path`** 覆盖）。决策通过 **同一套 REST / CLI / MCP** 提交，执行协程轮询数据库直至收到决策或超时，因此 **Dashboard 与 `sprintcycle run` 在同一进程时** 打开 Dashboard 页签即可点按钮放行；**纯 CLI 跑、另开终端决策** 时也可工作（依赖共享的 DB 路径与项目根）。

**与「知识注入确认门」的区别**：**知识门**（`require_knowledge_injection_confirm` 等）管的是「是否允许把知识写进执行上下文 / 是否继续跑」；**HITL** 管的是「在指定编排门（如 Sprint 前后、任务后）由人选择 **approve / skip_sprint / abort_execution**」。两者可并存，语义不要混用。

**常用配置项**（完整示例见仓库根 **`sprintcycle.toml.example`**）：

| 键 | 含义 |
|----|------|
| **`enabled`** | 是否启用 HITL。 |
| **`gates`** | 逗号分隔：`before_sprint`、`after_sprint`、`after_task`。 |
| **`default_timeout_seconds`** | 单条卡点最长等待秒数；到期按 **`timeout_behavior`** 自动结案。 |
| **`timeout_behavior`** | `approve`（默认） / `abort_execution` / `skip_sprint`。 |
| **`after_task_on_failure`** | 为 `true` 时仅在任务非成功后在 `after_task` 门卡点（默认 `true`）。 |
| **`after_sprint_always`** | 为 `true` 时每个 Sprint 结束后都在 `after_sprint` 门卡点；默认 `false` 时仅在本 Sprint 聚合状态**非** `success` 时在该门卡点。 |

**决策含义**（与执行器语义一致）：

- **`approve`**：继续后续流程。  
- **`skip_sprint`**：当前 Sprint 不跑任务，记为跳过。  
- **`abort_execution`**：中止后续 Sprint（在 **before_sprint** 上还会将当前 Sprint 记为取消）；在 **after_sprint / after_task** 上会在下一 Sprint 边界停止。

**决策别名**（CLI / MCP / REST 提交时会被规范化为上表三种；**不会**自动接受 `regen` / `need_info` / `modify`）：

| 输入别名 | 规范为 |
|----------|--------|
| `reject`, `deny`, `abort`, `stop`, `halt` | `abort_execution` |
| `skip` | `skip_sprint` |
| `pass`, `ok`, `yes`, `continue` | `approve` |

**Dashboard**：打开 **「✋ 人机卡点」** 页签，可刷新待办、填备注并提交决策；**「实时事件」** 中会收到 **`hitl_request_open` / `hitl_request_resolved`** SSE。单条记录只读接口：**`GET /api/hitl/requests/{request_id}`**（不依赖 `[hitl] enabled`，直接读 HITL SQLite）。

**执行事件只读回放**（落库在 **`.sprintcycle/data/exec_events.sqlite`**，与 **`execution_event_backend = "sqlite"`** 一致时才有数据）：**`GET /api/execution/{execution_id}/events?limit=`**；CLI **`sprintcycle execution-events <execution_id> [--limit N]`**。若当前配置不是 sqlite 后端，接口返回空列表并带说明字段。

**CLI**：

```bash
sprintcycle hitl pending
sprintcycle hitl submit <request_id> --decision approve
sprintcycle hitl show <request_id>
sprintcycle hitl history --limit 30
sprintcycle execution-events <execution_id> --limit 100
```

**MCP**：**`sprintcycle_hitl_pending`**、**`sprintcycle_hitl_submit`**（`decision` 为字符串，支持上表别名）、**`sprintcycle_hitl_history`**、**`sprintcycle_hitl_show`**、**`sprintcycle_execution_events`**（参数与上列 REST/CLI 对应）。

### 执行缓存切换（diskcache / Redis / 关闭）

默认使用本地 **diskcache**；多实例或共享缓存可改为 **Redis**（需 `pip install -e ".[cache-redis]"`）。在项目根 **`sprintcycle.toml`** 的 **`[cache]`** 或环境变量 **`SPRINTCYCLE_CACHE_*`** 中切换，详见 **[`docs/CACHE.md`](CACHE.md)**。

## 环境准备

设置环境变量：

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

## 快速开始

### 场景 1：使用 Python 代码进化

```python
import asyncio
from sprintcycle.evolution.engine import EvolutionEngine
from sprintcycle.evolution.config import EvolutionEngineConfig
from sprintcycle.evolution.types import SprintContext

async def main():
    # 1. 创建配置
    config = EvolutionEngineConfig(
        llm_provider="deepseek",
        llm_model="deepseek-reasoner",
        llm_api_key="your-api-key",
        cache_dir="./evolution_cache",
    )
    
    # 2. 创建进化引擎
    engine = EvolutionEngine(config)
    
    # 3. 创建 Sprint 上下文
    context = SprintContext(
        sprint_id="sprint-001",
        sprint_number=1,
        goal="优化代码性能",
        current_metrics={"success_rate": 0.8}
    )
    
    # 4. 执行进化
    result = await engine.evolve_code(
        target="./src/main.py",
        context=context,
        goal="将执行时间减少50%",
        max_variations=5
    )
    
    # 5. 查看结果
    if result.success:
        print(f"✅ 生成 {len(result.variations)} 个变体")
        print(f"🎯 选择 {len(result.selected_genes)} 个最优基因")

asyncio.run(main())
```

### 场景 2：批量进化

```python
# 进化整个目录
results = await engine.evolve_batch(
    targets=["./src/module1.py", "./src/module2.py", "./src/utils.py"],
    goal="统一代码风格"
)
```

### 场景 3：使用 CLI 命令

```bash
# 初始化配置文件
sprintcycle config --init

# 进化单个文件
sprintcycle evolve --target src/main.py --goal "优化性能"

# 查看进化状态
sprintcycle status

# 查看配置
sprintcycle config --show
```

## 常见场景示例

### 场景 1：性能优化

```python
context = SprintContext(
    sprint_id="perf-sprint",
    sprint_number=1,
    goal="优化性能",
    current_metrics={"avg_duration": 500}  # 500ms
)

result = await engine.evolve_code(
    target="./src/api_handler.py",
    context=context,
    goal="将 API 响应时间减少 50%"
)
```

### 场景 2：稳定性改进

```python
context = SprintContext(
    sprint_id="stability-sprint",
    sprint_number=1,
    goal="提升稳定性",
    current_metrics={
        "success_rate": 0.65,
        "error_count": 20
    }
)

result = await engine.evolve_code(
    target="./src/database.py",
    context=context,
    goal="减少错误率到 5% 以下"
)
```

### 场景 3：代码重构

```python
result = await engine.evolve_code(
    target="./src/legacy_module.py",
    goal="重构为现代 Python 风格",
    max_variations=10
)
```

### 场景 4：添加错误处理

```python
result = await engine.evolve_code(
    target="./src/api_client.py",
    goal="添加完善的错误处理和重试机制"
)
```

### 场景 5：自动化代码审查

```python
from sprintcycle.coding_engine import CodingEngine
from sprintcycle.config import CodingConfig, CodingLLMConfig

config = CodingConfig(
    engine="llm",
    llm=CodingLLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key="your-api-key"
    )
)

engine = CodingEngine(config)

# 审查代码
review = await engine.review_code(
    open("src/main.py").read(),
    review_type="security"  # security/performance/style/general
)

print(f"评分: {review['score']}/10")
for issue in review['issues']:
    print(f"  [{issue['severity']}] {issue['description']}")
```

### 场景 6：Sprint 触发进化

```python
# 根据指标自动判断是否需要进化
metrics = {
    "success_rate": 0.7,
    "error_count": 15,
    "avg_duration": 120
}

if engine.should_evolve(metrics):
    result = await engine.evolve_code(
        target="./src/main.py",
        goal="解决当前性能问题"
    )
```

### 场景 7：Pareto 前沿分析

```python
# 获取 Pareto 前沿
pareto_genes = engine.get_pareto_front()

for gene in pareto_genes:
    print(f"基因 {gene.id}:")
    for dim, score in gene.fitness_scores.items():
        print(f"  {dim}: {score:.3f}")

# 获取 top-5 最优基因
best_genes = engine.get_best_genes(top_k=5)
```

### 场景 8：使用回调函数

```python
def on_variation(variations):
    print(f"📦 生成 {len(variations)} 个变体")
    for v in variations:
        print(f"   - {v.change_summary}")

def on_selection(genes):
    print(f"🎯 选择 {len(genes)} 个基因")

def on_inheritance(genes):
    print(f"🧬 遗传 {len(genes)} 个基因")

engine.register_callbacks(
    on_variation=on_variation,
    on_selection=on_selection,
    on_inheritance=on_inheritance
)

result = await engine.evolve_code(target="./src/main.py")
```

## 配置文件

创建 `sprintcycle.yaml`:

```yaml
evolution:
  enabled: true
  llm:
    provider: deepseek
    model: deepseek-reasoner
    api_key: ${DEEPSEEK_API_KEY}
    temperature: 0.7
    max_tokens: 2048
  cache_dir: ./evolution_cache
  max_iterations: 10
  pareto_dimensions:
    - correctness
    - performance
    - stability
    - code_quality
  inheritance_enabled: true
  reflection_enabled: true

coding:
  engine: llm
  llm:
    provider: deepseek
    model: deepseek-chat
    api_key: ${DEEPSEEK_API_KEY}
```

## 故障排除

### 问题 1：API 密钥未设置

```
Error: DEEPSEEK_API_KEY environment variable not set
```

解决：

```bash
export DEEPSEEK_API_KEY="your-actual-api-key"
```

```

### 问题 3：文件不存在

```
Error: 文件不存在: ./src/main.py
```

解决：
- 确认文件路径正确
- 使用绝对路径

## 下一步

- 查看 [API 文档](./API.md) 了解完整 API
- 查看 `examples/` 目录获取更多示例
- 查看 `tests/` 目录了解测试方法
