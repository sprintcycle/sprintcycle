# SprintCycle 自我进化模块 - 变更日志

## v0.5.0 (2026-04-28)

### 概述

SprintCycle 自我进化模块实现完成，集成 Hermes Agent Self-Evolution (GEPA) 算法驱动框架自我优化。

### 新增功能

#### P0 阶段 - 配置层
- ✅ `SprintCycleConfig` 新增进化配置
- ✅ `EvolutionLLMConfig` - 进化引擎 LLM 配置（必填）
- ✅ `EvolutionConfig` - 进化引擎配置
- ✅ `CodingConfig` - 编码引擎配置（cursor/llm/claude）
- ✅ 环境变量支持
- ✅ 配置验证逻辑

#### P1 阶段 - 进化引擎层
- ✅ `EvolutionEngine` - 核心进化引擎
  - `evolve_code(target, goal)` - 进化指定 Python 代码文件（核心方法）
  - `evolve_batch(targets, goal)` - 批量进化
  - `should_evolve(metrics)` - 判断是否需要进化
- ✅ `GEPAClient` - GEPA 客户端封装
  - `vary()` - 变异生成
  - `select()` - 帕累托选择
  - `inherit()` - 基因遗传
- ✅ `types.py` - 类型定义
- ✅ `config.py` - 进化配置

#### P2 阶段 - Sprint 集成
- ✅ `SprintEvolutionIntegration` - Sprint 进化集成器
  - `trigger_after_sprint()` - Sprint 结束后触发进化
  - `evolve_modules()` - 手动进化指定模块

### 目录结构

```
sprintcycle/
├── sprintcycle/
│   ├── config.py                    # 配置层
│   ├── evolution/                   # 进化引擎
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── config.py
│   │   ├── client.py
│   │   └── engine.py
│   ├── integrations/               # 集成层
│   │   ├── __init__.py
│   │   └── evolution_integration.py
│   └── types/
├── examples/
│   └── evolution_examples.py
└── CHANGELOG-evolution.md
```

### 核心接口

```python
from sprintcycle.evolution.engine import EvolutionEngine
from sprintcycle.evolution.config import EvolutionEngineConfig

# 进化 SprintCycle 自身的 Python 代码文件
result = await engine.evolve_code(
    target="sprintcycle/config.py",
    goal="优化配置解析性能"
)
```

### 环境变量

```bash
export DEEPSEEK_API_KEY="sk-xxx"
export EVOLUTION_LLM_PROVIDER=deepseek
export EVOLUTION_LLM_MODEL=deepseek-reasoner
```

### 进化目标

SprintCycle 的自我进化目标是 **确定性代码**：

```
进化目标 = SprintCycle 的 Python 代码文件
├── sprintcycle/config.py
├── sprintcycle/server.py
└── sprintcycle/evolution/*.py
```

### 技术特点

1. **GEPA 集成**：通过 hermes-agent-self-evolution 库调用
2. **降级模式**：Hermes 库不可用时使用内置简化逻辑
3. **帕累托选择**：多目标优化选择最优变体
4. **精英遗传**：优秀基因传递给下一代
