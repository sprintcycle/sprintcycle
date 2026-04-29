# SprintCycle Evolution Module
# 
# 自进化核心模块，提供严格约束的自进化执行能力
#
# 严格约束原则：
# 1. 真实测量：所有指标必须来自真实工具（pytest --cov、radon cc、mypy等）
# 2. 实际修改：执行阶段必须实际修改sprintcycle/目录下的.py文件
# 3. 变更验证：每个执行阶段完成后，通过 git diff --stat 验证确实产生了代码变更
# 4. 测试守护：修改后跑 pytest 确认测试通过
# 5. Git提交：每个阶段产生实际变更后git commit
# 6. 无变更=失败：整个流程没有代码变更则FAILED

from .stage_executor import (
    StageExecutor,
    EvolutionStage,
    StageResult,
    EvolutionReport,
    StrictEvolutionConfig,
    EvolutionMetrics
)

# 兼容旧版本导入 - 使用 StageExecutor 作为 EvolutionEngine
EvolutionEngine = StageExecutor

__all__ = [
    "StageExecutor",
    "EvolutionStage",
    "StageResult",
    "EvolutionReport",
    "StrictEvolutionConfig",
    "EvolutionMetrics",
    "EvolutionEngine"
]
