"""
ExecutionEngine - 统一执行引擎

根据 PRD 模式选择对应的执行策略，所有策略共用 SprintExecutor。
EvolutionEngine 被注入到 SprintExecutor 中，作为 Sprint 的增强能力。
"""

import logging
from typing import Dict, Any, Optional

from ..prd.models import PRD, ExecutionMode
from .sprint_executor import SprintExecutor
from .strategies import ExecutionStrategy, NormalStrategy, EvolutionStrategy, ExecutionResult, get_strategy

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    统一执行引擎
    
    核心架构（方案 A）：
    ┌─────────────────────────────────────────────────────┐
    │              ExecutionEngine（统一引擎）             │
    │                                                     │
    │  execute(prd):                                     │
    │    strategy = self.get_strategy(prd.mode)          │
    │    return strategy.execute(prd)                    │
    └─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   NormalStrategy  EvolutionStrategy  FutureStrategy
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   SprintExecutor    │
              │   (统一实现)        │
              │         │           │
              │         ▼           │
              │  EvolutionEngine   │
              │  (内部增强)         │
              └─────────────────────┘
    
    使用方式：
    ```python
    engine = ExecutionEngine()
    result = await engine.execute(prd)
    ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化执行引擎
        
        Args:
            config: 可选配置
        """
        self.config = config or {}
        
        # v0.9.0: EvolutionPipeline replaces legacy engine
        from ..evolution.pipeline import EvolutionPipeline
        from ..evolution.prd_source import ManualPRDSource
        self._evolution_pipeline = EvolutionPipeline(prd_source=ManualPRDSource())
        
        # 创建共享的 SprintExecutor（注入 EvolutionEngine）
        mv = int(self.config.get("max_verify_fix_rounds", 3))
        self.sprint_executor = SprintExecutor(
            evolution_engine=self._evolution_pipeline,
            max_verify_fix_rounds=mv,
        )
        
        # 策略缓存
        self._strategies: Dict[ExecutionMode, ExecutionStrategy] = {}
        
        # 初始化默认策略
        self._init_strategies()
    
    def _init_strategies(self):
        """初始化策略实例"""
        self._strategies = {
            ExecutionMode.NORMAL: NormalStrategy(self.sprint_executor),
            ExecutionMode.EVOLUTION: EvolutionStrategy(self.sprint_executor),
        }
    
    def get_strategy(self, mode: ExecutionMode) -> ExecutionStrategy:
        """
        根据模式获取策略
        
        Args:
            mode: 执行模式
            
        Returns:
            ExecutionStrategy: 对应的策略实例
        """
        return get_strategy(mode, self.sprint_executor)
    
    async def execute(self, prd: PRD) -> ExecutionResult:
        """
        执行 PRD - 统一入口
        
        Args:
            prd: PRD 对象
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.info(f"🚀 ExecutionEngine 开始执行: {prd.project.name}")
        logger.info(f"   模式: {prd.mode.value}")
        logger.info(f"   Sprint 数: {len(prd.sprints)}")
        logger.info(f"   任务数: {prd.total_tasks}")
        
        # 根据模式选择策略
        strategy = self.get_strategy(prd.mode)
        
        # 执行
        result = await strategy.execute(prd)
        
        # 记录结果
        self._record_result(prd, result)
        
        return result
    
    def _record_result(self, prd: PRD, result: ExecutionResult):
        """记录执行结果（可用于反馈闭环）"""
        logger.info(f"📊 执行结果: {'成功' if result.success else '失败'}")
        logger.info(f"   完成 Sprint: {result.completed_sprints}/{result.total_sprints}")
        logger.info(f"   完成任务: {result.completed_tasks}/{result.total_tasks}")
        logger.info(f"   耗时: {result.duration:.2f}s")
    
    def register_agent_executor(self, agent_type: str, executor):
        """
        注册自定义 Agent 执行器
        
        Args:
            agent_type: Agent 类型
            executor: 执行器函数
        """
        self.sprint_executor.register_agent_executor(agent_type, executor)
        logger.info(f"✅ 注册 Agent 执行器: {agent_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "mode": "统一执行引擎",
            "strategies": list(self._strategies.keys()),
            "agent_executors": list(self.sprint_executor._agent_executors.keys()),
        }
