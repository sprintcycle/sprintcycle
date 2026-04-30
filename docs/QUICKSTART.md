# SprintCycle 5 分钟快速开始

本文档帮助你在 5 分钟内快速上手 SprintCycle。

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
