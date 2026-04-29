# SprintCycle 自进化技能文档

**版本**: v1.0  
**适用版本**: SprintCycle v0.8.0+  
**最后更新**: 2026-04-29  

---

## 1. 概述

### 1.1 什么是自进化

自进化是 SprintCycle 的核心能力之一，允许框架使用自身的能力来优化自身。通过 SelfEvolutionAgent，框架可以：

- 分析自身状态
- 识别优化点
- 制定进化计划
- 执行优化
- 验证结果

### 1.2 适用场景

- ✅ 代码覆盖率提升
- ✅ 性能优化
- ✅ 代码重构
- ✅ 依赖升级
- ✅ 文档完善

---

## 2. 快速开始

### 2.1 基本使用

```python
from sprintcycle.agents import SelfEvolutionAgent

# 初始化
agent = SelfEvolutionAgent(project_path=".")

# 执行自进化
result = agent.evolve(mode="incremental")

# 检查结果
if result.success:
    print("进化成功!")
```

### 2.2 进化模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `incremental` | 增量进化 | 日常小幅改进 |
| `full` | 全量进化 | 重大版本升级 |
| `targeted` | 针对性进化 | 特定模块优化 |

---

## 3. 15 阶段自进化流程

### 3.1 流程概览

```
Phase 1: 框架能力分析
    ↓
Phase 2: 框架 PRD 生成
    ↓
Phase 3: Sprint 规划
    ↓
Phase 4: 任务执行
    ↓
Phase 5: 框架功能评估
    ↓
Phase 6: 自进化机制评估
    ↓
Phase 7: 问题修复与优化
    ↓
Phase 8: 集成测试
    ↓
Phase 9: 技术文档更新
    ↓
Phase 10: 用户文档更新
    ↓
Phase 11: SKILL.md 更新
    ↓
Phase 12: 性能优化
    ↓
Phase 13: 安全审计
    ↓
Phase 14: 发布准备
    ↓
Phase 15: 技能自进化
```

### 3.2 各阶段详解

#### Phase 1: 框架能力分析
- 分析当前架构和功能
- 识别已实现能力
- 识别待增强能力
- 产出: `evolution_reports/phase01/FRAMEWORK_ANALYSIS.md`

#### Phase 2: 框架 PRD 生成
- 生成新版本 PRD
- 包含功能需求
- 产出: `prd/sprintcycle_v0.8.0.yaml`

#### Phase 3: Sprint 规划
- 将 PRD 拆分为 Sprint
- 优先级排序
- 产出: `evolution_reports/phase03/SPRINT_PLAN.md`

#### Phase 4: 任务执行
- 执行优化任务
- 记录执行过程
- 产出: 代码变更 + 执行日志

#### Phase 5: 框架功能评估
- 评估功能完整度
- 综合评分
- 产出: `evolution_reports/phase05/FRAMEWORK_EVALUATION.md`

#### Phase 6: 自进化机制评估
- 评估自进化效果
- 识别改进点
- 产出: `evolution_reports/phase06/EVOLUTION_MECHANISM_EVALUATION.md`

#### Phase 7: 问题修复与优化
- 收集并修复问题
- 分类处理
- 产出: 修复记录

#### Phase 8: 集成测试
- 运行测试套件
- 验证覆盖率
- 产出: `evolution_reports/phase08/INTEGRATION_TEST_REPORT.md`

#### Phase 9-11: 文档更新
- 更新技术文档
- 更新用户文档
- 更新 SKILL.md

#### Phase 12: 性能优化
- 分析性能瓶颈
- 实施优化

#### Phase 13: 安全审计
- 检查依赖漏洞
- 代码安全检查

#### Phase 14: 发布准备
- 版本号更新
- 生成 CHANGELOG

#### Phase 15: 技能自进化
- 分析本次进化效果
- 优化进化机制

---

## 4. API 参考

### 4.1 SelfEvolutionAgent

```python
class SelfEvolutionAgent:
    def __init__(
        self,
        project_path: str = ".",
        data_dir: str = ".sprintcycle/evolution",
        dry_run: bool = False
    ):
        """
        初始化自进化 Agent
        
        Args:
            project_path: 项目路径
            data_dir: 数据存储目录
            dry_run: 是否仅模拟运行
        """
        
    def evolve(
        self,
        mode: str = "incremental",
        target_modules: Optional[List[str]] = None,
        max_iterations: int = 10
    ) -> EvolutionResult:
        """
        执行自进化
        
        Returns:
            EvolutionResult: 进化结果
        """
        
    def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化状态"""
        
    def rollback_to(self, snapshot_name: str) -> bool:
        """回滚到指定快照"""
```

### 4.2 EvolutionSnapshot

```python
@dataclass
class EvolutionSnapshot:
    phase: str              # analysis/planning/execution/validation/complete
    mode: str               # incremental/full/targeted
    status: str             # complete/failed/dry_run
    findings: List[Dict]    # 分析发现
    recommendations: List[Dict]  # 建议
    changes_made: List[str] # 执行的变更
    duration_seconds: float
    timestamp: str
```

### 4.3 EvolutionResult

```python
@dataclass
class EvolutionResult:
    success: bool
    snapshots: List[EvolutionSnapshot]
    metrics: Dict[str, Any]
    recommendations: List[str]
    errors: List[str]
```

---

## 5. 最佳实践

### 5.1 干运行优先

```python
# 先干运行验证
agent = SelfEvolutionAgent(dry_run=True)
result = agent.evolve(mode="incremental")

if result.success:
    # 确认结果后实际执行
    agent = SelfEvolutionAgent(dry_run=False)
    result = agent.evolve(mode="incremental")
```

### 5.2 针对性进化

```python
# 不要全量进化
result = agent.evolve(mode="full")  # ❌

# 使用针对性进化
result = agent.evolve(
    mode="targeted",
    target_modules=["server.py"]  # ✅
)
```

### 5.3 定期执行

```python
# 建议每周执行一次增量进化
# 每月执行一次全量进化
```

---

## 6. 故障排查

### 6.1 进化失败

```python
# 检查错误
result = agent.evolve(mode="incremental")
if not result.success:
    for error in result.errors:
        print(f"错误: {error}")
        
    # 查看失败的快照
    for snapshot in result.snapshots:
        if snapshot.status == "failed":
            print(f"失败阶段: {snapshot.phase}")
```

### 6.2 回滚

```python
# 列出可用的快照
import os
snapshots = os.listdir(".sprintcycle/evolution/snapshots/")

# 回滚到指定快照
agent.rollback_to(snapshots[-2])  # 回滚到上一个快照
```

---

## 7. 术语表

| 术语 | 说明 |
|------|------|
| SelfEvolutionAgent | 自进化 Agent |
| EvolutionSnapshot | 进化快照 |
| EvolutionResult | 进化结果 |
| 增量进化 | 小幅改进 |
| 全量进化 | 全面优化 |
| 针对性进化 | 指定模块优化 |

---

**文档版本**: v1.0  
**更新日期**: 2026-04-29  
**维护者**: SprintCycle Team
