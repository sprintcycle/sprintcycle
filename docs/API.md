# SprintCycle API 文档

## 目录

- [GEPAClient](#gepaclient) - GEPA 客户端
- [EvolutionEngine](#evolutionengine) - 进化引擎
- [CodingEngine](#codingengine) - 编码引擎
- [配置项说明](#配置项说明)

---

## GEPAClient

`from sprintcycle.evolution.client import GEPAClient`

Hermes Agent 自我进化 (GEPA) 客户端封装。

### 构造函数

```python
GEPAClient(config: EvolutionEngineConfig)
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| config | EvolutionEngineConfig | 是 | 进化引擎配置 |

### 方法

#### `async vary()`

生成代码变体候选。

```python
async def vary(
    code: str,
    context: SprintContext,
    goal: str,
    max_variations: int = 5
) -> List[Variation]
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | str | 是 | 原始代码 |
| context | SprintContext | 是 | Sprint 上下文 |
| goal | str | 是 | 进化目标描述 |
| max_variations | int | 否 | 最大变体数量，默认 5 |

**返回:** `List[Variation]` - 变异候选列表

**示例:**

```python
from sprintcycle.evolution.client import GEPAClient
from sprintcycle.evolution.config import EvolutionEngineConfig
from sprintcycle.evolution.types import SprintContext

config = EvolutionEngineConfig(
    llm_provider="deepseek",
    llm_model="deepseek-reasoner",
    llm_api_key="your-api-key"
)
client = GEPAClient(config)

context = SprintContext(
    sprint_id="sprint-001",
    sprint_number=1,
    goal="优化性能"
)

variations = await client.vary(
    code="def add(a, b): return a + b",
    context=context,
    goal="添加类型提示和错误处理",
    max_variations=3
)

for var in variations:
    print(f"{var.id}: {var.change_summary}")
```

#### `async select()`

Pareto 前沿选择。

```python
async def select(
    variations: List[Variation],
    fitness_scores: List[Dict[str, float]]
) -> List[Variation]
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| variations | List[Variation] | 是 | 变异候选列表 |
| fitness_scores | List[Dict[str, float]] | 是 | 适应度评分列表 |

**返回:** `List[Variation]` - 选择的变异列表

**示例:**

```python
fitness_scores = [
    {"correctness": 0.9, "performance": 0.8, "stability": 0.7},
    {"correctness": 0.8, "performance": 0.9, "stability": 0.6},
]

selected = await client.select(variations, fitness_scores)
print(f"选择 {len(selected)} 个最优变体")
```

#### `async inherit()`

精英基因传承。

```python
async def inherit(
    elite_genes: List[Gene],
    context: SprintContext
) -> List[Gene]
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| elite_genes | List[Gene] | 是 | 精英基因列表 |
| context | SprintContext | 是 | Sprint 上下文 |

**返回:** `List[Gene]` - 遗传后的新基因列表

**示例:**

```python
elite_genes = [
    Gene(id="gene_1", type=GeneType.CODE, content="...", fitness_scores={...}),
]

inherited = await client.inherit(elite_genes, context)
for gene in inherited:
    print(f"遗传基因: {gene.id}, 版本: {gene.version}")
```

#### `async save_checkpoint()`

保存检查点。

```python
async def save_checkpoint(sprint_id: str, data: Dict[str, Any]) -> None
```

#### `async load_checkpoint()`

加载检查点。

```python
async def load_checkpoint(sprint_id: str) -> Optional[Dict[str, Any]]
```

---

## EvolutionEngine

`from sprintcycle.evolution.engine import EvolutionEngine`

SprintCycle 自我进化引擎。

### 构造函数

```python
EvolutionEngine(config: EvolutionEngineConfig)
```

### 方法

#### `async evolve_code()`

🚀 核心方法：进化单个代码文件。

```python
async def evolve_code(
    target: str,
    context: Optional[SprintContext] = None,
    goal: Optional[str] = None,
    max_variations: int = 5
) -> EvolutionResult
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target | str | 是 | 目标文件路径 |
| context | SprintContext | 否 | Sprint 上下文 |
| goal | str | 否 | 进化目标描述 |
| max_variations | int | 否 | 最大变异数量 |

**返回:** `EvolutionResult` - 进化结果

**完整示例:**

```python
from sprintcycle.evolution.engine import EvolutionEngine
from sprintcycle.evolution.config import EvolutionEngineConfig
from sprintcycle.evolution.types import SprintContext

config = EvolutionEngineConfig(
    llm_provider="deepseek",
    llm_model="deepseek-reasoner",
    llm_api_key="your-api-key",
    cache_dir="./evolution_cache",
    pareto_dimensions=["correctness", "performance", "stability"],
    inheritance_enabled=True,
)

engine = EvolutionEngine(config)

context = SprintContext(
    sprint_id="sprint-001",
    sprint_number=1,
    goal="优化代码性能",
    current_metrics={"success_rate": 0.8, "error_count": 3}
)

result = await engine.evolve_code(
    target="./src/main.py",
    context=context,
    goal="将执行时间减少50%",
    max_variations=5
)

if result.success:
    print(f"✅ 生成 {len(result.variations)} 个变体")
    print(f"🎯 选择 {len(result.selected_genes)} 个最优基因")
    print(f"🧬 遗传 {len(result.inherited_genes)} 个基因")
    print(f"⏱️ 耗时: {result.execution_time:.2f}s")
else:
    print(f"❌ 错误: {result.error}")
```

#### `async evolve_batch()`

批量进化多个文件。

```python
async def evolve_batch(
    targets: List[str],
    context: Optional[SprintContext] = None,
    goal: Optional[str] = None
) -> List[EvolutionResult]
```

**示例:**

```python
results = await engine.evolve_batch(
    targets=["./src/module1.py", "./src/module2.py", "./src/utils.py"],
    context=context,
    goal="统一代码风格"
)

for r in results:
    print(f"{'✅' if r.success else '❌'} {r}")
```

#### `should_evolve()`

判断是否需要触发进化。

```python
def should_evolve(metrics: Dict[str, Any]) -> bool
```

**触发条件:**
- `success_rate < 0.7`
- `error_count > 10`
- `avg_duration > 600`

**示例:**

```python
metrics = {"success_rate": 0.65, "error_count": 5, "avg_duration": 100}
if engine.should_evolve(metrics):
    print("触发自我进化...")
```

#### `register_callbacks()`

注册进化回调函数。

```python
def register_callbacks(
    on_variation=None,
    on_selection=None,
    on_inheritance=None
)
```

**示例:**

```python
def on_variation(variations):
    print(f"生成 {len(variations)} 个变体")

def on_selection(genes):
    print(f"选择 {len(genes)} 个基因")

engine.register_callbacks(
    on_variation=on_variation,
    on_selection=on_selection
)
```

#### 其他方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `add_gene(gene)` | None | 添加基因到基因池 |
| `get_best_genes(top_k)` | List[Gene] | 获取 top-k 最优基因 |
| `get_pareto_front()` | List[Gene] | 获取 Pareto 前沿 |
| `get_summary()` | Dict[str, Any] | 获取进化摘要 |
| `load_checkpoint(sprint_id)` | bool | 加载检查点 |
| `reset()` | None | 重置引擎状态 |

---

## CodingEngine

`from sprintcycle.coding_engine import CodingEngine`

编码引擎工厂，支持三种策略：Cursor、LLM、Claude。

### 构造函数

```python
CodingEngine(config: CodingConfig)
```

### 方法

#### `async generate_code()`

生成代码。

```python
async def generate_code(
    prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> str
```

**示例:**

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

code = await engine.generate_code(
    prompt="实现一个快速排序算法",
    context={"language": "python", "style": "functional"}
)

print(code)
```

#### `async review_code()`

代码审查。

```python
async def review_code(
    code: str,
    review_type: str = "general"
) -> Dict[str, Any]
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | str | 是 | 待审查代码 |
| review_type | str | 否 | 审查类型: `general`, `security`, `performance`, `style` |

**返回:**

```python
{
    "score": 8.5,                    # 评分 1-10
    "issues": [                      # 发现的问题
        {
            "severity": "high",      # high/medium/low
            "line": 10,
            "description": "未处理的异常",
            "suggestion": "添加 try-except"
        }
    ],
    "summary": "代码质量良好",
    "recommendations": ["建议添加类型提示"],
    "success": True
}
```

#### `async explain_code()`

解释代码。

```python
async def explain_code(code: str) -> str
```

### 使用示例

```python
from sprintcycle.coding_engine import CodingEngine

# 使用 Cursor
cursor_engine = CodingEngine.from_engine("cursor")

# 使用 LLM
llm_engine = CodingEngine.from_engine("llm", api_key="your-key")

# 使用 Claude
claude_engine = CodingEngine.from_engine("claude", api_key="your-key")

# 代码生成
code = await llm_engine.generate_code("实现一个 LRU 缓存")

# 代码审查
review = await llm_engine.review_code(code, review_type="performance")

# 代码解释
explanation = await llm_engine.explain_code(code)
```

---

## 配置项说明

### EvolutionEngineConfig

进化引擎配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `llm_provider` | str | "deepseek" | LLM 提供商 |
| `llm_model` | str | "deepseek-reasoner" | LLM 模型 |
| `llm_api_key` | str | "" | API 密钥 |
| `llm_api_base` | str | None | API Base URL |
| `llm_temperature` | float | 0.7 | 生成温度 |
| `llm_max_tokens` | int | 2048 | 最大 token 数 |
| `hermes_repo` | str | "~/.hermes/hermes-agent" | Hermes 仓库路径 |
| `cache_dir` | str | "./evolution_cache" | 缓存目录 |
| `max_iterations` | int | 10 | 最大迭代次数 |
| `max_variations_per_gen` | int | 5 | 每代最大变异数 |
| `pareto_dimensions` | List[str] | 见下方 | Pareto 优化维度 |
| `reflection_enabled` | bool | True | 反思阶段开关 |
| `reflection_depth` | int | 3 | 反思深度 |
| `selection_strategy` | str | "pareto_frontier" | 选择策略 |
| `inheritance_enabled` | bool | True | 遗传阶段开关 |
| `elite_ratio` | float | 0.1 | 精英比例 |

**默认 Pareto 维度:**

```python
["correctness", "performance", "stability", "code_quality"]
```

### CodingConfig

编码引擎配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `engine` | str | "cursor" | 引擎类型: cursor/llm/claude |
| `llm` | CodingLLMConfig | None | LLM 配置 |
| `claude` | CodingClaudeConfig | None | Claude 配置 |

### CodingLLMConfig

LLM 编码配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `provider` | str | "deepseek" | 提供商 |
| `model` | str | "deepseek-chat" | 模型 |
| `api_key` | str | "" | API 密钥 |
| `api_base` | str | None | API Base URL |

### CodingClaudeConfig

Claude 编码配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `model` | str | "claude-3-5-sonnet" | Claude 模型 |
| `api_key` | str | "" | API 密钥 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 |
| `EVOLUTION_LLM_PROVIDER` | 进化 LLM 提供商 |
| `EVOLUTION_LLM_MODEL` | 进化 LLM 模型 |
| `CODING_ENGINE` | 编码引擎类型 |
| `CODING_LLM_PROVIDER` | 编码 LLM 提供商 |
| `CODING_LLM_MODEL` | 编码 LLM 模型 |

### 配置文件示例

**YAML 格式 (`sprintcycle.yaml`):**

```yaml
evolution:
  enabled: true
  llm:
    provider: deepseek
    model: deepseek-reasoner
    api_key: ${DEEPSEEK_API_KEY}
    api_base: null
    temperature: 0.7
    max_tokens: 2048
  hermes_repo: ~/.hermes/hermes-agent
  cache_dir: ./evolution_cache
  max_iterations: 10
  pareto_dimensions:
    - correctness
    - performance
    - stability
    - code_quality
  reflection_enabled: true
  inheritance_enabled: true

coding:
  engine: llm
  llm:
    provider: deepseek
    model: deepseek-chat
    api_key: ${DEEPSEEK_API_KEY}
    api_base: null
```

---

## 类型参考

### SprintContext

Sprint 上下文。

```python
SprintContext(
    sprint_id: str,              # Sprint ID
    sprint_number: int,           # Sprint 编号
    goal: str,                   # Sprint 目标
    current_metrics: Dict,        # 当前指标
    gene_pool: List[Gene],        # 基因池
    execution_traces: List[Dict],# 执行轨迹
    reflection: str,              # 反思内容
    constraints: Dict            # 约束条件
)
```

### EvolutionResult

进化结果。

```python
EvolutionResult(
    stage: EvolutionStage,        # 当前阶段
    success: bool,                # 是否成功
    variations: List[Variation],  # 变异列表
    selected_genes: List[Gene],   # 选择的基因
    inherited_genes: List[Gene],  # 遗传的基因
    error: Optional[str],         # 错误信息
    metrics: Dict,                # 指标
    execution_time: float          # 执行时间
)
```

### Gene

基因。

```python
Gene(
    id: str,
    type: GeneType,               # CODE/PROMPT/CONFIG/WORKFLOW/METRICS
    content: str,
    metadata: Dict,
    fitness_scores: Dict[str, float],
    parent_ids: List[str],
    created_at: datetime,
    version: int
)
```

### Variation

变异候选。

```python
Variation(
    id: str,
    gene_id: str,
    variation_type: VariationType,  # POINT/BLOCK/STRUCTURAL/SEMANTIC
    original_content: str,
    modified_content: str,
    change_summary: str,
    risk_level: str,                # low/medium/high
    metadata: Dict,
    predicted_fitness: Dict[str, float],
    confidence: float
)
```
