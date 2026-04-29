# SprintCycle 自进化技能文档

**版本**: v2.0 (严格约束版)  
**适用版本**: SprintCycle v0.8.0+  
**最后更新**: 2026-04-29  

---

## ⚠️ 严格约束说明 (v2.0 新增)

**重要**: 自进化功能现在使用严格约束模式，确保所有操作都是真实有效的。

### 核心原则

1. **真实测量**: 所有指标必须来自真实工具
   - 覆盖率: `pytest --cov`
   - 复杂度: `radon cc`
   - 类型检查: `mypy`

2. **实际修改**: 执行阶段(10-12)必须实际修改 `sprintcycle/` 目录下的 `.py` 文件

3. **变更验证**: 每个执行阶段完成后，通过 `git diff --stat` 验证确实产生了代码变更

4. **测试守护**: 修改后跑 `python -m pytest tests/ -q --tb=short` 确认测试通过

5. **Git提交**: 每个阶段产生实际变更后自动 git commit

6. **无变更=失败**: 整个流程没有代码变更则标记为 **FAILED**

---

## 1. 概述

### 1.1 什么是自进化

自进化是 SprintCycle 的核心能力之一，允许框架使用自身的能力来优化自身。通过 SelfEvolutionAgent，框架可以：

- 分析自身状态 (使用真实工具测量)
- 识别优化点 (基于真实数据)
- 制定进化计划 (基于真实分析)
- 执行优化 (实际修改代码)
- 验证结果 (运行真实测试)

### 1.2 适用场景

- ✅ 代码覆盖率提升
- ✅ 代码复杂度优化
- ✅ 类型错误修复
- ✅ 性能优化
- ✅ 代码重构
- ✅ 依赖升级
- ✅ 文档完善

---

## 2. 快速开始

### 2.1 基本使用 (DRY_RUN 模式 - 仅分析)

```python
from sprintcycle.agents import SelfEvolutionAgent

# 初始化 (默认 DRY_RUN，仅分析不修改)
agent = SelfEvolutionAgent(project_path=".")

# 执行自进化 (仅分析，不实际修改代码)
result = agent.evolve(mode="incremental")

# 检查结果
if result.success:
    print("分析完成!")
print(f"文件变更: {result.metrics.get('files_changed', 0)}")
```

### 2.2 实际修改代码 (LIVE 模式)

```python
from sprintcycle.agents import SelfEvolutionAgent

# 执行自进化 (实际修改代码)
agent = SelfEvolutionAgent(project_path=".")
result = agent.evolve(mode="incremental", live=True)  # live=True 实际修改

if result.success:
    print("进化成功!")
else:
    print("进化失败!")
```

### 2.3 进化模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `incremental` | 增量进化 | 日常小幅改进 |
| `full` | 全量进化 | 重大版本升级 |
| `targeted` | 针对性进化 | 特定模块优化 |

---

## 3. 15 阶段自进化流程 (严格约束版)

### 3.1 流程概览

```
阶段 1-3:  分析阶段 (Analysis) - 真实工具测量
├── 阶段1: 代码结构分析 (radon cc)
├── 阶段2: 测试覆盖分析 (pytest --cov)
└── 阶段3: 类型错误分析 (mypy)
    ↓
阶段 4-6:  规划阶段 (Planning) - 基于真实数据
├── 阶段4: 覆盖率提升规划
├── 阶段5: 复杂度优化规划
└── 阶段6: 类型修复规划
    ↓
阶段 7-9:  设计阶段 (Design) - 生成具体方案
├── 阶段7: 测试用例设计
├── 阶段8: 代码优化方案设计
└── 阶段9: 文档更新设计
    ↓
阶段 10-12: 执行阶段 (Execution) - 必须实际改代码
├── 阶段10: 创建/修改测试文件
├── 阶段11: 优化/重构框架代码
└── 阶段12: 修复类型错误
    ↓
阶段 13-15: 验证阶段 (Validation) - 真实数据验证
├── 阶段13: 运行完整测试套件
├── 阶段14: 重新测量覆盖率
└── 阶段15: 生成最终报告
```

### 3.2 各阶段详解

#### 阶段 1-3: 分析阶段 (真实工具)

| 阶段 | 工具 | 测量内容 |
|------|------|----------|
| 阶段1 | `radon cc` | 代码复杂度 (Cyclomatic Complexity) |
| 阶段2 | `pytest --cov` | 测试覆盖率 (含分支覆盖) |
| 阶段3 | `mypy` | 类型错误和警告 |

**示例输出**:
```
阶段1: 复杂度分析
  - 高复杂度函数 (>= 10): 5个
  - Top 3: chorus.py:optimize_sprint() - 25

阶段2: 覆盖率分析
  - 总体覆盖率: 65%
  - 低覆盖模块: cache.py (45%), autofix.py (52%)

阶段3: 类型检查
  - 类型错误: 3个
  - 文件: server.py, config.py
```

#### 阶段 4-6: 规划阶段 (基于真实数据)

- **阶段4**: 基于 pytest --cov 结果制定覆盖率提升计划
- **阶段5**: 基于 radon cc 结果制定复杂度优化计划
- **阶段6**: 基于 mypy 结果制定类型修复计划

#### 阶段 7-9: 设计阶段

- **阶段7**: 为低覆盖模块设计具体测试用例
- **阶段8**: 为高复杂度函数设计简化方案
- **阶段9**: 设计文档更新内容

#### 阶段 10-12: 执行阶段 (⚠️ 必须实际改代码)

**严格约束**: 这三个阶段必须产生实际的代码变更！

- **阶段10**: 创建/修改测试文件 (`tests/test_xxx_coverage.py`)
- **阶段11**: 实际修改 `sprintcycle/` 目录下的框架代码
- **阶段12**: 实际修复类型错误

**变更验证流程**:
```python
# 每个执行阶段完成后:
changed_files, _ = get_git_diff_stat()

if changed_files == 0:
    # ⚠️ 严格约束触发!
    print("⚠️ 无代码变更! 执行阶段失败!")
    # 阶段标记为 FAILED
```

#### 阶段 13-15: 验证阶段 (真实数据)

- **阶段13**: 运行完整测试套件 `pytest tests/ -q`
- **阶段14**: 重新运行 `pytest --cov` 获取真实覆盖率
- **阶段15**: 生成报告 (无代码变更则 FAILED)

---

## 4. API 参考

### 4.1 SelfEvolutionAgent (v2.0)

```python
class SelfEvolutionAgent:
    def __init__(
        self,
        project_path: str = ".",
        data_dir: str = ".sprintcycle/evolution",
        dry_run: bool = True  # 默认 DRY_RUN
    ):
        """
        初始化自进化 Agent
        
        Args:
            project_path: 项目路径
            data_dir: 数据存储目录
            dry_run: 是否仅模拟运行 (默认True)
        """
        
    def evolve(
        self,
        mode: str = "incremental",
        target_modules: Optional[List[str]] = None,
        max_iterations: int = 10,
        live: bool = False  # 新增: 实际修改代码
    ) -> EvolutionResult:
        """
        执行自进化
        
        Args:
            mode: 进化模式 (incremental/full/targeted)
            target_modules: 目标模块列表 (targeted 模式使用)
            max_iterations: 最大迭代次数
            live: 是否实际修改代码 (默认False，仅分析)
            
        Returns:
            EvolutionResult: 进化结果
        """
        
    def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化状态"""
```

### 4.2 StageExecutor (新增)

```python
from sprintcycle.evolution import StageExecutor, StrictEvolutionConfig

# 配置
config = StrictEvolutionConfig(
    project_path=".",
    coverage_threshold=70.0,
    complexity_threshold=10,
    auto_commit=True
)

# 执行所有15阶段
executor = StageExecutor(project_path=".", config=config)
report = executor.execute_all_stages(dry_run=True)  # 默认仅分析

# 或实际修改
report = executor.execute_all_stages(dry_run=False)  # 实际修改代码
```

### 4.3 数据结构

```python
@dataclass
class EvolutionSnapshot:
    phase: str              # analysis/planning/execution/validation/complete
    mode: str               # incremental/full/targeted
    status: str             # complete/failed/dry_run
    findings: List[Dict]    # 分析发现 (来自真实工具)
    recommendations: List[Dict]  # 建议
    changes_made: List[str] # 执行的变更
    duration_seconds: float
    timestamp: str
    dry_run: bool           # 是否为模拟运行

@dataclass
class EvolutionResult:
    success: bool
    snapshots: List[EvolutionSnapshot]
    metrics: Dict[str, Any]
    recommendations: List[str]
    errors: List[str]
    dry_run: bool           # 新增: 标记是否为模拟运行
```

---

## 5. 命令行工具

### 5.1 15阶段执行器

```bash
# DRY_RUN 模式 (仅分析)
python -m sprintcycle.evolution.stage_executor --dry-run

# LIVE 模式 (实际修改代码)
python -m sprintcycle.evolution.stage_executor --live

# 指定项目路径
python -m sprintcycle.evolution.stage_executor --project-path /path/to/project --live
```

### 5.2 输出示例

```
======================================================================
🚀 SprintCycle 15阶段自进化执行器 v2.0 (严格约束版)
======================================================================
📁 项目路径: /path/to/project
🔧 模式: DRY_RUN (仅分析不修改)
======================================================================

======================================================================
📊 阶段 1/15: stage_1_code_analysis
======================================================================
🔍 使用 radon cc 分析代码复杂度...
📊 分析完成:
   - 高复杂度函数 (>= 10): 5个
   - Top 5 复杂度:
     1. chorus.py:optimize_sprint: 25
     2. chorus.py:run_all_sources: 18
...

======================================================================
📊 最终报告
======================================================================
⚠️  DRY_RUN模式: 未实际修改代码
   移除 --live 参数以实际执行修改
```

---

## 6. 最佳实践

### 6.1 干运行优先

```python
# ✅ 推荐: 先 DRY_RUN 验证
agent = SelfEvolutionAgent(dry_run=True)
result = agent.evolve(mode="incremental")
print(f"分析完成: {result.metrics}")

# 确认结果后实际执行
if result.success:
    agent = SelfEvolutionAgent(dry_run=False)
    result = agent.evolve(mode="incremental", live=True)
```

### 6.2 针对性进化

```python
# ✅ 推荐: 使用针对性进化
result = agent.evolve(
    mode="targeted",
    target_modules=["cache.py", "autofix.py"],
    live=True
)
```

### 6.3 定期执行

```python
# 建议每周执行一次增量进化
# 每月执行一次全量进化
```

---

## 7. 故障排查

### 7.1 进化失败

```python
result = agent.evolve(mode="incremental", live=True)
if not result.success:
    for error in result.errors:
        print(f"错误: {error}")
        
    # 检查失败的阶段
    for snapshot in result.snapshots:
        if snapshot.status == "failed":
            print(f"失败阶段: {snapshot.phase}")
            print(f"问题: {snapshot.findings}")
```

### 7.2 严格约束触发

```
⚠️ 严格约束: 执行阶段无代码变更!
```

**原因**: 执行阶段(10-12)没有产生任何代码变更。

**解决方案**:
1. 检查目标模块是否存在
2. 确认有低覆盖/高复杂度/类型错误需要处理
3. 检查 git 状态是否正常

### 7.3 测试失败

```python
# 检查测试结果
result = agent.evolve(mode="incremental", live=True)

# 验证测试通过
for snapshot in result.snapshots:
    if "test_pass_rate" in str(snapshot.findings):
        if not snapshot.findings[0].get("passed"):
            print("测试失败，需要检查")
```

---

## 8. 术语表

| 术语 | 说明 |
|------|------|
| SelfEvolutionAgent | 自进化 Agent (v2.0) |
| StageExecutor | 15阶段执行器 (v2.0 新增) |
| DRY_RUN | 干运行模式，仅分析不修改 |
| LIVE | 实际执行模式，会修改代码 |
| Strict Mode | 严格约束模式 |
| 真实测量 | 使用 pytest --cov, radon cc, mypy 等工具 |
| 变更验证 | git diff --stat 检查 |

---

## 9. 依赖工具

| 工具 | 版本 | 用途 |
|------|------|------|
| pytest | >= 7.0 | 测试运行 |
| pytest-cov | >= 4.0 | 覆盖率测量 |
| radon | >= 6.0 | 复杂度分析 |
| mypy | >= 1.0 | 类型检查 |
| git | any | 版本控制 |

安装依赖:
```bash
pip install pytest pytest-cov radon mypy
```

---

**文档版本**: v2.0 (严格约束版)  
**更新日期**: 2026-04-29  
**维护者**: SprintCycle Team
