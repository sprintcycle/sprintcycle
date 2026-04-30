# SprintCycle API 文档

> ⚠️ 本文档正在更新中，部分内容可能已过时（GEPA/Hermes 相关内容已废弃）。

## 目录

- [EvolutionPipeline](#evolutionpipeline) - 进化流水线
- [SprintExecutor](#sprintexecutor) - Sprint 执行器
- [配置项说明](#配置项说明)

---

## EvolutionPipeline

`from sprintcycle.evolution.pipeline import EvolutionPipeline`

统一的进化流水线，替代已废弃的 GEPAClient。

### 构造函数

```python
EvolutionPipeline(config: Optional[PipelineConfig] = None)
```

## SprintExecutor

`from sprintcycle.execution.engine import SprintExecutor`

Sprint 执行引擎。

## 配置项说明

### RuntimeConfig

`from sprintcycle.config import RuntimeConfig`

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_sprints | int | 10 | 最大Sprint数 |
| max_tasks_per_sprint | int | 5 | 每Sprint最大任务数 |
| parallel_tasks | int | 3 | 并行任务数 |
| evolution_enabled | bool | True | 启用进化 |
| llm_provider | str | "deepseek" | LLM提供者 |
| llm_model | str | "deepseek-reasoner" | 模型名 |
| dry_run | bool | False | 干跑模式 |
