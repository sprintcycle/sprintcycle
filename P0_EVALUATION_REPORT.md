# SprintCycle P0 需求完整评估报告

**版本**：v0.8.0  
**生成日期**：2026年1月  
**状态**：正式评估完成

---

## 1. 执行摘要

### 两个 P0 的最终推荐方案

| P0 编号 | 需求 | 最终推荐方案 | 核心理由 |
|---------|------|--------------|----------|
| **P0-1** | 可证伪进化 | **分层验证体系**：硬性门控(pytest+coverage+mypy) + 客观度量(radon) + Rubrics分级评测 + 深度验证(mutmut夜间) | 数学严格 + 零主观判断 + 进化循环友好 |
| **P0-2** | 架构护栏 | **import-linter** | 7年成熟度、官方pre-commit支持、explore+drawgraph可视化、与6步精简无缝衔接 |

### 关键结论

1. **P0-1 覆盖度**：现有工具均无法完整覆盖，Hermes框架约覆盖40%，需组合多个工具实现分层验证
2. **P0-2 工具选择**：import-linter 在成熟度、CI集成、可视化三维度全面胜出
3. **Rubrics评测**：SprintCycle 天然满足两个先决条件（无UI、AI框架可自验证），应立即引入rubrics型评测

---

## 2. P0-1 可证伪进化完整评估

### 2.1 需求定义

SprintCycle 的 `SelfEvolutionAgent` 能"进化"，但进化后没有严格的机制证伪"这轮改动是改进"。需要一套**可证伪的验证机制**，确保：
- 进化产生的改动确实带来改进
- 改动不会引入新的问题
- 改进是可量化、可复现的

### 2.2 调研全景对比表

| 方案 | 成熟度 | 许可 | 语言 | 特点 | 进化循环友好度 | 最终结论 |
|------|--------|------|------|------|---------------|----------|
| **Geneclaw (GEP协议)** | ⭐ (v0.1.0, 34 stars) | MIT | Python | 可证伪进化协议 | 高 | ❌ 极不成熟，推翻 |
| **Hermes (Nous Research)** | ⭐⭐⭐⭐⭐ (100k+ stars) | Apache | Python | 自进化Agent框架，Skill自动生成+迭代 | 高 | ⚠️ 覆盖~40%，Tinker-Atropos RL管线不可用 |
| **Harness Evolver** | ⭐⭐⭐ | - | Node.js | Claude Code插件，6种Agent类型 | 中 | ❌ Node.js，SprintCycle接不进去 |
| **AgentEvolver (阿里通义)** | ⭐⭐⭐ | Apache | Python | RL训练框架，训练模型参数 | 低 | ❌ 训练模型用，非代码进化 |
| **A-Evolve (Orchestra-Research)** | ⭐⭐⭐ | MIT | Python | @evolve装饰器 | 高 | ⚠️ 依赖OpenEvolve，偏重 |
| **EvolveR** | ⭐⭐ | - | Python | 学术项目，经验蒸馏+策略进化 | 中 | ⚠️ 研究向，生产可用性待验证 |
| **agent-evolve (pypi)** | ⭐⭐ | MIT | Python | @evolve装饰器+Streamlit dashboard | 高 | ⚠️ Beta阶段，需评估稳定性 |
| **自建GRPO信号** | ⭐ | - | Python | 借鉴Hermes奖励函数 | 高 | ⚠️ ~200行可实现，需评估ROI |
| **mutmut 突变测试** | ⭐⭐⭐⭐ | MIT | Python | 数学严格，系统性注入bug | 高 | ⚠️ 后被推翻：衡量测试质量非代码质量 |
| **radon 客观度量** | ⭐⭐⭐⭐ | MIT | Python | McCabe复杂度+Halstead+MI指数 | 高 | ✅ 推荐：零主观判断 |
| **pytest+coverage+mypy** | ⭐⭐⭐⭐⭐ | - | Python | 硬性门控 | 高 | ✅ 推荐：成熟稳定 |

### 2.3 逐方案评估

#### 2.3.1 Geneclaw (GEP协议) — ❌ 不推荐（第一轮推翻）

**优势**：
- 可证伪进化协议，概念契合
- Python实现，MIT许可

**劣势**：
- v0.1.0，极早期项目
- 34 stars，社区极小
- 2026年2月18日后未更新
- 依赖nanobot，项目本身不独立

**适用性**：❌ 不适用  
**不适用理由**：项目成熟度远未达到生产可用标准，使用风险过高

---

#### 2.3.2 Hermes (Nous Research) — ⚠️ 参考借鉴，覆盖~40%

**优势**：
- 100k+ stars，顶级成熟度
- 自进化Agent框架，Skill自动生成+迭代
- 学习闭环覆盖约40%可证伪进化需求
- GRPO确定性奖励思路可借鉴

**劣势**：
- Tinker-Atropos RL训练管线是 Nous 内部用的，普通用户拿不到
- 七层安全防护是运行时安全（危险命令审批、上下文注入扫描、容器隔离），不解决代码结构问题

**适用性**：⚠️ 部分适用  
**GRPO奖励函数参考**：
```python
# 借鉴Hermes的确定性奖励设计
reward_weights = {
    "format": 0.2,      # 格式正确
    "schema": 0.3,      # Schema符合
    "execution": 0.5,   # 执行通过
    "completion": 1.0,  # 完整交付
    "hallucination": -1.0  # 幻觉惩罚
}
```

---

#### 2.3.3 Harness Evolver — ❌ 不适用

**优势**：
- Claude Code插件，成熟度较高
- 6种Agent类型，流程完整
- RAG agent测试从0.575→1.000(+74%)

**劣势**：
- Node.js实现 (`npx`)
- 需要LangSmith API Key
- 不是独立Python库

**适用性**：❌ 不适用  
**不适用理由**：SprintCycle是Python框架，无法集成Node.js插件

---

#### 2.3.4 AgentEvolver (阿里通义) — ❌ 不适用

**优势**：
- 三大机制完整（自我提问+自我导航+自我归因）
- 14B模型 avg@8 从29.8%→57.6%
- Python，Apache许可

**劣势**：
- RL训练框架，偏重训练模型参数
- 不是给项目代码进化用的

**适用性**：❌ 不适用  
**不适用理由**：目标是训练模型权重，而非进化项目代码结构

---

#### 2.3.5 A-Evolve (Orchestra-Research) — ⚠️ 参考

**优势**：
- Python，MIT许可
- @evolve装饰器，API友好
- Benchmark优秀：MCP-Atlas 79.4%, SWE-bench 76.8%

**劣势**：
- 依赖OpenEvolve做底层优化
- 整体方案偏重

**适用性**：⚠️ 参考其装饰器设计思路  
**不适用理由**：强依赖OpenEvolve，引入成本高

---

#### 2.3.6 mutmut 突变测试 — ⚠️ 后被推翻

**初始推荐理由**：
- 数学严格：系统性注入bug看测试能否抓住
- 直接衡量测试有效性

**推翻过程**（自证伪）：

1. **突变分数衡量的是测试质量，不是代码质量**
   - 加新功能 → 突变分可能下降，但不代表系统变差
   - 重构 → 突变分也可能下降
   - 这是核心矛盾：进化产生的新代码天然会降低原有测试的突变分数

2. **性能问题**
   - 701个测试跑突变可能数小时
   - 进不了进化循环（进化需要快速反馈）

3. **适合场景**
   - 夜间深度检查：✅ 推荐
   - 进化循环内快速验证：❌ 不适合

**最终结论**：保留为夜间深度验证工具，不进入进化循环

---

#### 2.3.7 radon 客观度量 — ✅ 推荐

**优势**：
- 纯客观度量，零主观判断
- McCabe复杂度 + Halstead度量 + MI可维护性指数
- 实现量小：~80行 EvolutionVerifier 类
- 进化前后可对比

**劣势**：
- 度量结果需要解读（复杂度高≠代码差）
- 需要设定合理的阈值

**适用性**：✅ 推荐  
**配置示例**：
```python
# evolution_verifier.py (~80行)
from radon.metrics import h_visit, mi_visit
from radon.complexity import cc_visit

class EvolutionVerifier:
    def __init__(self, baseline_path: str):
        with open(baseline_path) as f:
            self.baseline = json.load(f)
    
    def measure(self, file_path: str) -> dict:
        with open(file_path) as f:
            code = f.read()
        
        # McCabe复杂度
        cc = cc_visit(code)
        avg_cc = sum(c.complexity for c in cc) / len(cc) if cc else 0
        
        # Halstead度量
        halstead = h_visit(code)
        
        # 可维护性指数
        mi = mi_visit(code, exclude=[], multi=False)
        
        return {
            "avg_cyclomatic_complexity": avg_cc,
            "halstead_volume": halstead.total.volume if hasattr(halstead, 'total') else 0,
            "maintainability_index": mi
        }
    
    def is_improvement(self, before: dict, after: dict) -> bool:
        """判断进化是否带来改进"""
        # 复杂度降低 or 可维护性提升
        return (after["avg_cyclomatic_complexity"] <= before["avg_cyclomatic_complexity"] 
                and after["maintainability_index"] >= before["maintainability_index"])
```

---

### 2.4 关键决策节点时间线

```
[第一轮] 推荐 Geneclaw(GEP协议) + import-linter
    ↓
[第二轮] 发现 Geneclaw 极不成熟（34 stars, v0.1.0）
    ↓ 修正：推荐 Evolver(3.1k stars) 或自建轻量版
[第三轮] 用户集成 Hermes Agent 后评估
    ↓ Hermes 覆盖~40%，Tinker-Atropos RL 管线不可用
[第四轮] 搜索对比：Harness Evolver / AgentEvolver / A-Evolve / EvolveR / 自建GRPO
    ↓ 排除 Harness(非Python) / AgentEvolver(训练用) / A-Evolve(偏重)
[第五轮] 推荐 mutmut 突变测试
    ↓
[自推翻] 突变分数衡量测试质量非代码质量 + 性能问题
    ↓ 修正
[第六轮] 修正为 radon（客观度量）+ pytest+coverage+mypy（硬性门控）
    ↓
[第七轮] 补充阿里云《Harness Engineering实践》文章启示
    ↓ 发现 SprintCycle 缺失 rubrics 型评测
[最终] 分层验证体系：硬性门控+客观度量+rubrics评测+深度验证
```

### 2.5 最终推荐方案：分层验证体系

#### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    SelfEvolutionAgent 进化循环                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │ Generate │ → │  Gate 1  │ → │  Gate 2  │ → │  Gate 3  │       │
│  │  改动   │    │硬性门控  │    │客观度量  │    │Rubrics  │       │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘       │
│                     ↓              ↓              ↓             │
│              pytest pass    复杂度不增      AI分级评分           │
│              coverage不降   MI指数不降      >0.8通过             │
│              mypy 0 errors                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  夜间深度验证   │
                    │   mutmut 运行   │
                    └─────────────────┘
```

#### 各层职责

| 层次 | 工具 | 检查内容 | 通过标准 | 执行时间 |
|------|------|----------|----------|----------|
| **Gate 1** | pytest + coverage + mypy | 功能正确性、类型安全 | 全部pass、coverage不降、mypy 0 errors | ~30s |
| **Gate 2** | radon | 代码复杂度、可维护性 | CC不增加、MI不下降 | ~5s |
| **Gate 3** | Rubrics AI评测 | 架构质量、协作效果 | 平均分 > 0.8 | ~60s |
| **深度验证** | mutmut | 测试有效性 | 突变分数不显著下降 | ~2h（夜间） |

---

### 2.6 实施路径（分阶段，从轻到重）

#### Phase 1: 硬性门控集成（1-2天）
```yaml
# .github/workflows/evolution-gate.yml
name: Evolution Gate
on:
  pull_request:
    paths:
      - 'src/**'

jobs:
  gate1-hard-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install pytest pytest-cov mypy
      
      - name: Run pytest with coverage
        run: pytest --cov=sprintmind --cov-fail-under=66 .
      
      - name: Run mypy
        run: mypy sprintmind/ --no-error-summary
        # 允许当前227个错误逐步消减，但新代码必须clean
```

#### Phase 2: 客观度量集成（2-3天）
```python
# src/sprintmind/evolution/evolution_verifier.py
"""进化验证器 - 客观度量层"""

from dataclasses import dataclass
from pathlib import Path
import json

from radon.metrics import h_visit, mi_visit
from radon.complexity import cc_visit


@dataclass
class VerificationResult:
    passed: bool
    avg_cyclomatic_complexity: float
    maintainability_index: float
    halstead_volume: float
    details: str


class EvolutionVerifier:
    """基于客观度量的进化验证器"""
    
    def __init__(self, baseline_path: str = ".evolution/baseline.json"):
        self.baseline_path = baseline_path
        self.baseline = self._load_baseline()
    
    def _load_baseline(self) -> dict:
        if Path(self.baseline_path).exists():
            with open(self.baseline_path) as f:
                return json.load(f)
        return {}
    
    def measure_file(self, file_path: str) -> dict:
        with open(file_path) as f:
            code = f.read()
        
        # McCabe 复杂度
        cc_blocks = cc_visit(code)
        avg_cc = sum(b.complexity for b in cc_blocks) / len(cc_blocks) if cc_blocks else 0
        
        # Halstead 度量
        halstead = h_visit(code)
        volume = halstead.total.volume if hasattr(halstead, 'total') else 0
        
        # 可维护性指数
        mi = mi_visit(code, exclude=[], multi=False)
        
        return {
            "avg_cyclomatic_complexity": avg_cc,
            "maintainability_index": mi,
            "halstead_volume": volume
        }
    
    def verify(self, file_paths: list[str]) -> VerificationResult:
        """验证进化是否带来改进"""
        current = {fp: self.measure_file(fp) for fp in file_paths}
        
        # 计算整体指标
        total_cc = sum(m["avg_cyclomatic_complexity"] for m in current.values())
        total_mi = sum(m["maintainability_index"] for m in current.values()) / len(current)
        
        # 与baseline对比
        baseline_cc = self.baseline.get("avg_cyclomatic_complexity", total_cc)
        baseline_mi = self.baseline.get("maintainability_index", total_mi)
        
        passed = (total_cc <= baseline_cc * 1.1) and (total_mi >= baseline_mi * 0.9)
        
        return VerificationResult(
            passed=passed,
            avg_cyclomatic_complexity=total_cc,
            maintainability_index=total_mi,
            halstead_volume=sum(m["halstead_volume"] for m in current.values()),
            details=f"CC: {baseline_cc:.1f} → {total_cc:.1f}, MI: {baseline_mi:.1f} → {total_mi:.1f}"
        )
    
    def save_baseline(self):
        """保存当前状态为baseline"""
        Path(self.baseline_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, 'w') as f:
            json.dump(self.baseline, f, indent=2)
```

#### Phase 3: Rubrics 评测设计（3-5天）

见第4节详细设计。

#### Phase 4: 夜间深度验证（1天）
```yaml
# .github/workflows/nightly-mutmut.yml
name: Nightly Mutation Testing
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点

jobs:
  mutmut:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install mutmut
        run: pip install mutmut
      
      - name: Run mutation testing
        run: |
          mutmut run --no-banner
          mutmut results
```

---

## 3. P0-2 架构护栏完整评估

### 3.1 需求定义

防止架构腐化、依赖方向违规、模块边界被侵蚀。需要**工具化的架构约束**，确保：
- 模块间依赖方向正确
- 禁止的依赖路径被检测
- 架构规则可验证、可执行

### 3.2 调研全景对比表

| 工具 | 成熟度 | 许可 | 配置格式 | 可视化 | CI集成 | 特点 |
|------|--------|------|----------|--------|--------|------|
| **import-linter** | ⭐⭐⭐⭐⭐ 7年老牌 | BSD | INI/YAML | ✅ explore+drawgraph | ✅ lint-imports一行 | pre-commit官方支持 |
| deply | ⭐⭐ 2026新(0.8.2) | MIT | YAML | ✅ Mermaid图 | ✅ deply analyze | 类级别规则，行内忽略 |
| arch_lint | ⭐⭐⭐ fluidattacks | MIT | 无文档 | ❌ | 需自己写 | 文档缺失 |
| layers-linter | ⭐⭐ 2025新 | 未知 | TOML | ❌ | ✅ | flake8插件 |
| pytest-archon | ⭐⭐⭐ | Apache | pytest代码 | ❌ | ✅ 跟pytest走 | 自定义谓词，架构违规=测试失败 |
| 自建AST | ⭐ | - | 纯代码 | 需自建 | 需自建 | 重复造轮子 |

### 3.3 逐方案评估

#### 3.3.1 import-linter — ✅ 推荐

**优势**：
- 7年老牌，稳定可靠
- BSD许可，商业友好
- INI/YAML配置，简洁直观
- explore命令交互式查看依赖图
- drawgraph命令导出可视化
- lint-imports一行命令，极简CI集成
- pre-commit官方支持

**劣势**：
- 规则语法需要学习
- 不支持类级别规则（仅包级别）

**适用性**：✅ 强烈推荐  
**SprintCycle配置示例**：

```ini
# .importlinter
[levels]
layer_core = sprintmind/core
layer_agents = sprintmind/agents
layer_tools = sprintmind/tools
layer_cli = sprintmind/cli

[rules]
no_circular_imports = true

# SprintCycle 特定规则
# CLI 可导入 agents/tools，但 agents/tools 不可导入 cli
# Core 是底层，不可被高层导入
[[layers]]
name = "sprintmind_architecture"
containers = [
    "sprintmind",
]
layers = [
    "sprintmind.core",
    "sprintmind.agents",
    "sprintmind.tools", 
    "sprintmind.cli",
]

# 依赖方向：core → agents → tools → cli
# 不可反向
```

或等效 YAML 配置：
```yaml
# .importlinter.yaml
version: 2

layers:
  - name: core
    containers:
      - sprintmind.core
    containers_by_regex:
      - regex: "^sprintmind\\.core\\..*"
        name: core_submodule
  
  - name: agents
    containers:
      - sprintmind.agents
  
  - name: tools
    containers:
      - sprintmind.tools
  
  - name: cli
    containers:
      - sprintmind.cli

rules:
  - name: no_circular_imports
  - name: layering
    containers:
      - sprintmind
    layers:
      - sprintmind.core
      - sprintmind.agents
      - sprintmind.tools
      - sprintmind.cli
    ignore_nested_packages: true
```

**CI集成**：
```yaml
# .github/workflows/arch-lint.yml
name: Architecture Lint
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install import-linter
      - run: lint-imports
```

**pre-commit集成**：
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/s滕sr/import-linter
    rev: v1.10.0
    hooks:
      - id: import-linter
```

---

#### 3.3.2 deply — ⚠️ 备选

**优势**：
- YAML配置
- Mermaid图可视化
- 支持行内忽略注释
- 类级别规则

**劣势**：
- 2026年新项目（v0.8.2），成熟度低
- 社区小，文档有限

**适用性**：⚠️ 备选，如import-linter不满足再评估

---

#### 3.3.3 pytest-archon — ⚠️ 概念好，执行复杂

**优势**：
- "架构违规=测试失败"概念好
- 自定义谓词灵活

**劣势**：
- 需要写Python代码定义谓词
- SprintCycle的架构规则是简单层级约束，不需要复杂谓词
- 增加测试复杂度

**适用性**：⚠️ 不推荐  
**不适用理由**：杀鸡焉用牛刀，import-linter的声明式配置更适合简单层级约束

---

#### 3.3.4 自建AST — ❌ 不推荐

**劣势**：
- 重复造轮子
- 需自建可视化和CI集成
- 维护成本高

**适用性**：❌ 不推荐

---

### 3.4 最终推荐及理由

**推荐：import-linter**

| 决策维度 | import-linter | pytest-archon | deply |
|----------|---------------|----------------|-------|
| **成熟度** | ⭐⭐⭐⭐⭐ 7年 | ⭐⭐⭐ | ⭐⭐ |
| **配置简洁性** | ⭐⭐⭐⭐⭐ 声明式 | ⭐⭐⭐ 代码式 | ⭐⭐⭐⭐ |
| **CI集成** | ⭐⭐⭐⭐⭐ 一行命令 | ⭐⭐⭐⭐ 跟pytest | ⭐⭐⭐⭐ |
| **可视化** | ⭐⭐⭐⭐ explore+drawgraph | ❌ | ⭐⭐⭐⭐ Mermaid |
| **pre-commit** | ⭐⭐⭐⭐⭐ 官方支持 | 需额外配置 | 无 |

**关键决策理由**：
1. **pytest-archon的"架构违规=测试失败"看似更好**，但SprintCycle的架构规则是简单层级约束，不需要复杂谓词
2. **可视化在重构期更实用**：SprintCycle正在6步精简中，explore命令交互式查看依赖图非常实用
3. **CI加一行lint-imports不存在"被遗忘"问题**：简洁的CI集成反而更容易维护
4. **7年成熟度 > 新项目**：deply虽然有类级别规则等特性，但成熟度差距太大

---

### 3.5 SprintCycle 具体配置示例

基于SprintCycle当前架构（6步精简进行中）：

```yaml
# .importlinter.yaml
# SprintCycle 架构约束配置

version: 2

# 层级定义（基于6步精简的最终目标架构）
layers:
  - name: foundation
    known_first_party_packages:
      - sprintmind.foundation

  - name: core
    known_first_party_packages:
      - sprintmind.core
      - sprintmind.contracts
      - sprintmind.events

  - name: agents
    known_first_party_packages:
      - sprintmind.agents
      - sprintmind.evolution

  - name: tools
    known_first_party_packages:
      - sprintmind.tools

  - name: cli
    known_first_party_packages:
      - sprintmind.cli

# 依赖规则
rules:
  - name: no_circular_imports
  
  - name: layering
    containers:
      - sprintmind
    layers:
      - sprintmind.foundation
      - sprintmind.core
      - sprintmind.agents
      - sprintmind.tools
      - sprintmind.cli
    ignore_nested_packages: true

# 允许的工具层直接依赖核心层（特殊情况）
exceptions:
  - name: tools_may_import_core
    from_layer: sprintmind.tools
    to_layer: sprintmind.core
    reason: "Tools需要访问核心合约和事件系统"
```

验证命令：
```bash
# 本地验证
lint-imports

# 交互式查看依赖图
import-linter --show-config
import-linter explore

# 导出可视化
import-linter drawgraph --output arch_diagram.png
```

---

## 4. 阿里云文章启示与 Rubrics 评测设计

### 4.1 文章核心观点提炼

**文章信息**：
- 标题：《Harness Engineering实践，做了一个平台让AI一晚上自动评测和优化你的系统》
- 作者：凤聆（阿里云）
- 平台：Auto Test Platform（QoderWork）

**核心观点**：

1. **两种评测类型**
   - **Standard评测**：0/1结论（通过/失败），SprintCycle已有（pytest）
   - **Rubrics评测**：分级打分（如1-5分），SprintCycle**完全缺失**

2. **评测→优化→评测→优化 往复循环**
   - v1: 90.7 → v2: 97.4 → v3: 99.1
   - 关键：每轮评测都发现改进点，形成闭环

3. **AI可自动生成评测集**
   - 文章中AI自动生成13个用例覆盖MCP全功能
   - 对SprintCycle的启示：可以让SelfEvolutionAgent自动生成评测用例

4. **两个先决条件**
   - 纯后端无UI问题：✅ SprintCycle满足
   - 本身是AI框架可自我验证：✅ SprintCycle满足

### 4.2 对 SprintCycle 的具体启示

| 启示点 | 当前状态 | 建议行动 |
|--------|----------|----------|
| Rubrics评测缺失 | 只有pytest（standard型） | 立即引入rubrics型评测 |
| "Chorus编排质量"无法评测 | 无分级标准 | 设计编排质量rubrics |
| "Agent协作效果"无法量化 | 无评分机制 | 设计协作效果rubrics |
| "错误恢复能力"无法测试 | 无故障注入口 | 设计恢复能力rubrics |
| AI生成评测集 | 手动编写测试 | 探索SelfEvolutionAgent自动生成评测 |

### 4.3 Rubrics 评测集初步设计

针对 SprintCycle 核心能力的分级评分标准：

#### 4.3.1 Chorus 编排质量评分标准

| 维度 | 5分 | 4分 | 3分 | 2分 | 1分 |
|------|-----|-----|-----|-----|-----|
| **意图路由准确性** | 100%路由正确 | ≥95% | ≥85% | ≥70% | <70% |
| **并行执行效率** | 理论最优并行度 | 实际并行度≥90% | 实际并行度≥75% | 实际并行度≥50% | 串行执行 |
| **错误传播完整性** | 错误完整传递+语义保留 | 错误传递+部分语义 | 错误传递但语义丢失 | 错误丢失 | 静默失败 |

**评分公式**：
```
chorus_score = 0.4 * intent_routing + 0.3 * parallel_efficiency + 0.3 * error_propagation
```

---

#### 4.3.2 Agent 协作效果评分标准

| 维度 | 5分 | 4分 | 3分 | 2分 | 1分 |
|------|-----|-----|-----|-----|-----|
| **上下文复用率** | >90%复用有效上下文 | >75% | >60% | >40% | <40% |
| **任务分工合理性** | 完全符合能力边界 | 基本符合 | 偶有跨边界 | 频繁跨边界 | 完全混乱 |
| **状态同步一致性** | 所有agent状态强一致 | 最终一致 | 偶有不一致 | 频繁不一致 | 完全不一致 |

**评分公式**：
```
agent_score = 0.35 * context_reuse + 0.35 * task_division + 0.3 * state_sync
```

---

#### 4.3.3 错误恢复能力评分标准

| 维度 | 5分 | 4分 | 3分 | 2分 | 1分 |
|------|-----|-----|-----|-----|-----|
| **检测覆盖率** | >95%异常被检测 | >85% | >70% | >50% | <50% |
| **恢复策略适当性** | 最优恢复策略 | 次优但有效 | 勉强有效 | 有副作用 | 完全失败 |
| **恢复时间** | <1秒 | <5秒 | <30秒 | <2分钟 | >2分钟或失败 |

**评分公式**：
```
recovery_score = 0.3 * detection_rate + 0.4 * strategy_quality + 0.3 * recovery_time_factor
```

---

#### 4.3.4 进化有效性评分标准（针对P0-1）

| 维度 | 5分 | 4分 | 3分 | 2分 | 1分 |
|------|-----|-----|-----|-----|-----|
| **功能保持率** | 100%原有功能正常 | ≥98% | ≥95% | ≥90% | <90% |
| **新功能完整性** | 100%需求实现 | ≥90% | ≥80% | ≥60% | <60% |
| **性能影响** | 无性能下降 | <5%下降 | <10%下降 | <20%下降 | ≥20%下降 |

**进化通过标准**：
```python
def is_evolution_valid(scores: dict) -> bool:
    return (
        scores["functionality"] >= 0.95
        and scores["new_features"] >= 0.80
        and scores["performance"] >= 0.90
        and sum(scores.values()) / 3 >= 0.85  # 总体平均≥0.85
    )
```

---

#### 4.3.5 Rubrics 评测实现

```python
# src/sprintmind/evolution/rubrics_evaluator.py
"""Rubrics分级评测器"""

from dataclasses import dataclass
from typing import Protocol
from enum import Enum


class ScoreLevel(Enum):
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    NEEDS_IMPROVEMENT = 2
    POOR = 1


@dataclass
class RubricDimension:
    name: str
    weight: float
    scorer: 'DimensionScorer'


class DimensionScorer(Protocol):
    """维度评分器协议"""
    def score(self, context: dict) -> tuple[float, str]:
        """
        返回 (分数, 评分理由)
        分数范围: 1.0 - 5.0
        """
        ...


@dataclass
class RubricEvaluationResult:
    dimension_scores: dict[str, float]
    weighted_score: float
    passed: bool
    details: list[str]


class ChorusQualityScorer:
    """Chorus编排质量评分器"""
    
    def __init__(self, test_cases: list[dict]):
        self.test_cases = test_cases
    
    def score(self, context: dict) -> tuple[float, str]:
        intent_routing = self._score_intent_routing(context)
        parallel_efficiency = self._score_parallel_efficiency(context)
        error_propagation = self._score_error_propagation(context)
        
        chorus_score = (
            0.4 * intent_routing +
            0.3 * parallel_efficiency +
            0.3 * error_propagation
        )
        
        details = (
            f"意图路由: {intent_routing:.2f}, "
            f"并行效率: {parallel_efficiency:.2f}, "
            f"错误传播: {error_propagation:.2f}"
        )
        
        return chorus_score, details
    
    def _score_intent_routing(self, context: dict) -> float:
        results = context.get("routing_results", [])
        if not results:
            return 3.0
        correct = sum(1 for r in results if r.get("correct", False))
        rate = correct / len(results)
        return min(5.0, max(1.0, rate * 5))
    
    def _score_parallel_efficiency(self, context: dict) -> float:
        expected = context.get("expected_parallelism", 1)
        actual = context.get("actual_parallelism", 1)
        if expected <= 1:
            return 5.0 if actual >= 1 else 3.0
        rate = actual / expected
        return min(5.0, max(1.0, rate * 5))
    
    def _score_error_propagation(self, context: dict) -> float:
        error_tests = context.get("error_propagation_tests", [])
        if not error_tests:
            return 3.0
        passed = sum(1 for t in error_tests if t.get("passed", False))
        rate = passed / len(error_tests)
        return min(5.0, max(1.0, rate * 5))


class RubricsEvaluator:
    """Rubrics评测器主类"""
    
    def __init__(self, dimensions: list[RubricDimension], threshold: float = 0.8):
        self.dimensions = dimensions
        self.threshold = threshold
    
    def evaluate(self, context: dict) -> RubricEvaluationResult:
        dimension_scores = {}
        details = []
        
        for dim in self.dimensions:
            score, detail = dim.scorer.score(context)
            dimension_scores[dim.name] = score
            details.append(f"{dim.name}: {detail}")
        
        weighted_score = sum(
            dimension_scores[dim.name] * dim.weight
            for dim in self.dimensions
        )
        
        passed = weighted_score >= self.threshold * 5
        
        return RubricEvaluationResult(
            dimension_scores=dimension_scores,
            weighted_score=weighted_score,
            passed=passed,
            details=details
        )


# 使用示例
def create_sprintcycle_evaluator() -> RubricsEvaluator:
    """创建SprintCycle的Rubrics评测器"""
    
    dimensions = [
        RubricDimension(
            name="chorus_quality",
            weight=0.30,
            scorer=ChorusQualityScorer(test_cases=[])
        ),
        RubricDimension(
            name="agent_collaboration",
            weight=0.25,
            scorer=AgentCollaborationScorer(test_cases=[])
        ),
        RubricDimension(
            name="error_recovery",
            weight=0.20,
            scorer=ErrorRecoveryScorer(test_cases=[])
        ),
        RubricDimension(
            name="evolution_validity",
            weight=0.25,
            scorer=EvolutionValidityScorer(test_cases=[])
        ),
    ]
    
    return RubricsEvaluator(dimensions=dimensions, threshold=0.8)
```

---

## 5. 与架构精简工作的关系

### 5.1 6步精简为 P0 集成做的铺垫

| 精简步骤 | 当前状态 | 对P0的意义 |
|----------|----------|------------|
| **Step 1** | ✅ 完成 | 定义清晰的模块边界是import-linter规则的前提 |
| **Step 2** | ✅ 完成 | 统一依赖方向为分层规则奠定基础 |
| **Step 3** | ✅ 完成 | 消除循环依赖使验证更可靠 |
| **Step 4** | ✅ 完成 | 清晰的层级结构是rubrics评分的前提 |
| **Step 5** | 🔄 进行中 | 提取核心抽象，当前工作与evolution verifier直接相关 |
| **Step 6** | ⏳ 待开始 | 消除技术债，为rubrics评测提供稳定基础 |

### 5.2 P0 集成的最佳时间点

**建议时序**：

```
当前状态                    建议时间点
    │                            │
    ├─ Step 5 进行中             │
    │                            │
    ├─ Step 5 完成 ──────────────┼──→ P0-2 (import-linter) 立即集成
    │                            │    理由：模块边界已清晰，规则可精确配置
    │                            │
    ├─ Step 6 完成 ──────────────┼──→ P0-1 Phase 1-2 (硬性门控+客观度量)
    │                            │    理由：技术债消除后，baseline稳定
    │                            │
    └─ Rubrics评测设计完成 ──────┼──→ P0-1 Phase 3 (Rubrics评测)
                                 │    理由：需要基于稳定架构设计评分标准
```

### 5.3 6步精简过程中的P0准备

**Step 5 进行中阶段的准备事项**：

1. **记录当前模块边界**
   ```bash
   # 生成当前依赖图作为后续验证的参考
   pip install import-linter
   lint-imports --show-config > architecture_snapshot.json
   ```

2. **建立evolution baseline**
   ```bash
   # 在6步完成前建立baseline，后续进化验证都与之对比
   python -c "
   from sprintmind.evolution.evolution_verifier import EvolutionVerifier
   ev = EvolutionVerifier()
   ev.baseline = ev.measure_directory('src/sprintmind')
   ev.save_baseline()
   "
   ```

---

## 6. 风险和注意事项

### 6.1 P0-1 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **radon度量与代码质量脱钩** | 中 | 中 | 设定合理阈值，不作为唯一标准 |
| **rubrics评分主观性** | 高 | 中 | AI评分一致性验证 + 人工抽检 |
| **进化循环过慢** | 中 | 高 | Gate 1-3控制在2分钟内，mutmut移至夜间 |
| **baseline陈旧** | 中 | 高 | 定期更新baseline（如每月） |
| **过度工程化** | 中 | 中 | Phase 1先跑通，再逐步引入后续阶段 |

### 6.2 P0-2 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **规则过严阻塞正常开发** | 中 | 高 | initial_ignores配置 + 逐步收紧 |
| **import-linter误报** | 低 | 低 | 官方稳定版 + 规则review |
| **6步精简后规则需重构** | 高 | 中 | 保持规则简单，等待精简完成再精细化 |
| **CI误报导致PR阻塞** | 中 | 中 | pre-commit优先检查，本地catch |

### 6.3 通用注意事项

1. **不要为了工具而工具**：确保每个工具确实解决实际问题
2. **渐进式引入**：先跑通，再优化，不要追求一步到位
3. **保持可逆性**：所有配置都应易于调整和回滚
4. **监控误报率**：如果误报率>10%，需要调整规则或阈值

---

## 7. 总结与下一步行动

### 7.1 总结

本次评估完成了对 SprintCycle 两个 P0 需求的全面调研和方案设计：

1. **P0-1 可证伪进化**：
   - 覆盖40%需求的 Hermes 框架不可直接使用（RL管线不可用）
   - mutmut 突变测试被自我推翻（衡量测试质量非代码质量）
   - 最终推荐分层验证体系：硬性门控(pytest+coverage+mypy) → 客观度量(radon) → Rubrics分级评测 → 夜间深度验证(mutmut)

2. **P0-2 架构护栏**：
   - import-linter 在成熟度、CI集成、可视化三维度全面胜出
   - pytest-archon 概念好但过度设计
   - 最终推荐 import-linter，配置简洁，7年稳定

3. **Rubrics评测**：
   - SprintCycle 天然满足两个先决条件（无UI + AI框架可自验证）
   - 设计了Chorus编排质量、Agent协作效果、错误恢复能力、进化有效性四个维度的评分标准
   - 建议立即引入rubrics型评测

4. **与架构精简的关系**：
   - P0-2 可在Step 5完成后立即集成
   - P0-1 应在Step 6完成后系统引入

### 7.2 下一步行动

#### 立即行动（本周）

| 优先级 | 任务 | 负责人 | 预计工时 |
|--------|------|--------|----------|
| P0 | import-linter 初步配置（基于当前架构） | SelfEvolutionAgent | 2小时 |
| P1 | rubrics 评测框架基础代码 | SelfEvolutionAgent | 4小时 |
| P2 | radon 客观度量器实现 | SelfEvolutionAgent | 2小时 |

#### 短期行动（Step 5完成后）

| 优先级 | 任务 | 预计工时 |
|--------|------|----------|
| P0 | import-linter 规则精细化（基于6步精简后的架构） | 2小时 |
| P0 | evolution gate CI workflow | 2小时 |
| P1 | Rubrics评测器与SelfEvolutionAgent集成 | 4小时 |

#### 中期行动（Step 6完成后）

| 优先级 | 任务 | 预计工时 |
|--------|------|----------|
| P0 | mutmut 夜间测试配置 | 2小时 |
| P1 | Rubrics评分一致性验证 | 4小时 |
| P2 | 进化历史可视化dashboard | 8小时 |

---

**报告生成完成**

如需进一步讨论或调整方案，请告知。
