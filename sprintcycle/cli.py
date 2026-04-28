"""
SprintCycle CLI - 单一意图参数入口

核心原则：一切皆 PRD
用户意图 → IntentParser → PRDGenerator → 执行引擎
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

import click

from sprintcycle.intent.parser import IntentParser, ActionType
from sprintcycle.prd.generator import PRDGenerator
from sprintcycle.prd.parser import PRDParser, PRDParseError, YAMLError
from sprintcycle.scheduler.dispatcher import TaskDispatcher, ExecutionStatus
from sprintcycle.intent.base import IntentResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--intent', '-i', type=str, help='用户意图描述')
@click.option('--project', '-p', type=str, help='项目路径')
@click.option('--target', '-t', type=str, help='目标文件')
@click.option('--mode', '-m', type=click.Choice(['auto', 'evolution', 'normal', 'fix', 'test']),
              default='auto', help='执行模式')
@click.option('--constraints', '-c', multiple=True, help='约束条件')
@click.option('--dry-run', is_flag=True, help='仅生成 PRD，不执行')
@click.option('--status', is_flag=True, help='查看状态')
@click.option('--init', 'init_path', type=click.Path(), help='初始化项目')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.argument('args', nargs=-1)  # 捕获所有剩余参数作为意图
@click.version_option(version='0.6.0', prog_name='sprintcycle')
def cli(
    intent: Optional[str],
    project: Optional[str],
    target: Optional[str],
    mode: str,
    constraints: tuple,
    dry_run: bool,
    status: bool,
    init_path: Optional[str],
    verbose: bool,
    args: tuple,
):
    """
    SprintCycle - PRD 驱动的自我进化框架
    
    一切皆 PRD: 意图 → PRD 生成器 → PRD 文件 → 执行引擎
    
    \b
    示例：
        sprintcycle "优化 engine.py 的性能"
        sprintcycle -i "优化 engine.py" -t engine.py -m evolution --dry-run
        sprintcycle --status
        sprintcycle --init ./my-project
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理特殊命令
    if status:
        _show_status()
        return
    
    if init_path:
        _init_project(init_path)
        return
    
    # 优先使用 --intent 参数，否则使用位置参数
    if not intent and args:
        intent = ' '.join(args)
    
    if not intent:
        click.echo("请提供意图描述，使用 --help 查看帮助")
        sys.exit(1)
    
    try:
        # 解析意图
        parser = IntentParser()
        parsed = parser.parse(
            intent,
            project=project,
            target=target,
            mode=mode,
            constraints=list(constraints),
        )
        
        # 显示解析结果
        click.echo(f"📋 解析意图: {parsed.action.value}")
        if parsed.target:
            click.echo(f"   目标: {parsed.target}")
        if parsed.project:
            click.echo(f"   项目: {parsed.project}")
        
        # 检查是否是 run 命令
        if parsed.action == ActionType.RUN:
            prd_file = parsed.prd_file or parsed.target
            if not prd_file:
                click.echo("❌ 未指定 PRD 文件")
                sys.exit(1)
            _run_prd_file(prd_file, dry_run, verbose)
            return
        
        # 生成 PRD
        generator = PRDGenerator()
        prd = generator.generate(parsed)
        
        if dry_run:
            click.echo("\n📄 生成的 PRD:")
            click.echo(prd.to_yaml())
            return
        
        # 执行
        click.echo(f"\n🚀 开始执行...")
        result = _execute_prd(prd)
        
        if result.success:
            click.echo(f"\n✅ 执行成功")
            click.echo(f"   完成 Sprint: {result.completed_sprints}/{result.total_sprints}")
            click.echo(f"   完成任务: {result.completed_tasks}/{result.total_tasks}")
        else:
            click.echo(f"\n❌ 执行失败: {result.error}")
            sys.exit(1)
            
    except YAMLError as e:
        click.echo(f"❌ YAML 解析错误: {e}")
        sys.exit(1)
    except PRDParseError as e:
        click.echo(f"❌ PRD 解析错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("执行失败")
        click.echo(f"❌ 错误: {e}")
        sys.exit(1)


def _show_status():
    """显示状态"""
    click.echo("📊 SprintCycle v0.6.0")
    click.echo("   模式: PRD 驱动")
    click.echo("")
    click.echo("意图类型:")
    click.echo("   evolution - 进化优化")
    click.echo("   normal    - 普通构建")
    click.echo("   fix       - Bug 修复")
    click.echo("   test      - 测试验证")
    click.echo("   run       - 执行 PRD 文件")


def _init_project(path: str):
    """初始化项目"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    
    sprintcycle_dir = p / ".sprintcycle"
    sprintcycle_dir.mkdir(exist_ok=True)
    
    sample_prd_path = sprintcycle_dir / "sample.yaml"
    sample_prd_content = PRDGenerator.sample_prd()
    sample_prd_path.write_text(sample_prd_content, encoding="utf-8")
    
    click.echo(f"✅ 项目初始化完成: {path}")
    click.echo(f"   创建了 .sprintcycle 目录")
    click.echo(f"   创建了示例 PRD: {sample_prd_path}")


def _run_prd_file(prd_file: str, dry_run: bool, verbose: bool):
    """执行 PRD 文件"""
    parser = PRDParser()
    click.echo(f"📄 解析 PRD: {prd_file}")
    prd = parser.parse_file(prd_file)
    
    click.echo(f"✅ 项目: {prd.project.name}")
    click.echo(f"   模式: {prd.mode.value}")
    click.echo(f"   Sprint 数: {len(prd.sprints)}")
    click.echo(f"   任务数: {prd.total_tasks}")
    
    if dry_run:
        click.echo("\n✅ PRD 验证通过（dry-run 模式）")
        return
    
    click.echo(f"\n🚀 开始执行...")
    result = _execute_prd(prd)
    
    if result.success:
        click.echo(f"\n✅ 执行成功")
        click.echo(f"   完成 Sprint: {result.completed_sprints}/{result.total_sprints}")
        click.echo(f"   完成任务: {result.completed_tasks}/{result.total_tasks}")
    else:
        click.echo(f"\n❌ 执行失败: {result.error}")
        sys.exit(1)


def _execute_prd(prd) -> IntentResult:
    """执行 PRD"""
    dispatcher = TaskDispatcher()
    sprint_results = asyncio.run(dispatcher.execute_prd(prd, max_concurrent=3))
    
    success = all(
        r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        for r in sprint_results
    )
    
    completed_sprints = sum(
        1 for r in sprint_results 
        if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
    )
    completed_tasks = sum(r.success_count for r in sprint_results)
    
    return IntentResult(
        success=success,
        prd=prd,
        completed_sprints=completed_sprints,
        completed_tasks=completed_tasks,
        total_sprints=len(sprint_results),
        total_tasks=prd.total_tasks,
        error=None if success else "部分任务失败",
        sprint_results=sprint_results,
    )


if __name__ == '__main__':
    cli()
