"""
SprintCycle 自我进化使用示例
"""

import asyncio


async def basic_usage():
    """基础使用示例"""
    from sprintcycle.evolution.engine import EvolutionEngine
    from sprintcycle.evolution.config import EvolutionEngineConfig
    
    config = EvolutionEngineConfig()
    engine = EvolutionEngine(config)
    
    # 进化 SprintCycle 自身的代码文件
    result = await engine.evolve_code(
        target="sprintcycle/config.py",
        goal="优化配置解析性能"
    )
    
    if result.success:
        print(f"✅ 进化成功: {result.selected_genes[0].metadata.get('file', 'unknown')}")


async def sprint_integration():
    """Sprint 集成示例"""
    from sprintcycle.evolution.config import EvolutionEngineConfig
    from sprintcycle.integrations import SprintEvolutionIntegration
    
    integration = SprintEvolutionIntegration(EvolutionEngineConfig())
    
    sprint_metrics = {
        "sprint_number": 5,
        "success_rate": 0.65,  # 低于 0.7，触发进化
        "error_count": 12,
    }
    
    results = await integration.trigger_after_sprint(sprint_metrics)
    print(f"进化完成: {len([r for r in results if r.success])}/{len(results)}")


def main():
    print("SprintCycle 自我进化模块")
    print("=" * 40)
    print("示例代码已就绪，请配置 DEEPSEEK_API_KEY 后运行")
    print("=" * 40)


if __name__ == "__main__":
    main()
