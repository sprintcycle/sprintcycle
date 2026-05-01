"""
SprintCycle CLI - 单一意图参数入口

核心原则：一切皆 PRD
用户意图 → IntentParser → PRDGenerator → 执行引擎
"""

import sys
import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import click

from sprintcycle.intent.parser import IntentParser, ActionType
from sprintcycle.prd.generator import IntentPRDGenerator
from sprintcycle.prd.parser import PRDParser, PRDParseError, YAMLError
from sprintcycle.scheduler.dispatcher import TaskDispatcher, ExecutionStatus
from sprintcycle.intent.base import IntentResult


def setup_logging(
    log_file: str = ".sprintcycle/logs/sprintcycle.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志系统，支持文件轮转
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)


logger = setup_logging()


def _resolve_intent(intent: Optional[str], args: tuple) -> str:
    """解析意图来源：--intent 参数或位置参数"""
    if not intent and args:
        intent = ' '.join(args)
    if not intent:
        click.echo(click.get_current_context().get_help())
        sys.exit(0)
    return intent


def _parse_and_show(intent: str, project: Optional[str], target: Optional[str],
                    mode: str, constraints: tuple) -> Any:
    """解析意图并显示结果"""
    parser = IntentParser()
    parsed = parser.parse(
        intent,
        project=project,
        target=target,
        mode=mode,
        constraints=list(constraints),
    )
    click.echo(f"📋 解析意图: {parsed.action.value}")
    if parsed.target:
        click.echo(f"   目标: {parsed.target}")
    if parsed.project:
        click.echo(f"   项目: {parsed.project}")
    return parsed


def _handle_run_action(parsed, dry_run: bool, verbose: bool):
    """处理 RUN action：直接执行 PRD 文件"""
    prd_file = parsed.prd_file or parsed.target
    if not prd_file:
        click.echo("❌ 未指定 PRD 文件")
        sys.exit(1)
    _run_prd_file(prd_file, dry_run, verbose)


def _generate_and_execute(parsed, dry_run: bool):
    """生成 PRD 并执行（非 RUN action）"""
    generator = IntentPRDGenerator()
    prd = generator.generate(parsed)
    
    if dry_run:
        click.echo("\n📄 生成的 PRD:")
        click.echo(prd.to_yaml())
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


def _show_status():
    """显示状态信息"""
    click.echo("📊 SprintCycle 状态")
    
    state_dir = Path(".sprintcycle/state")
    if not state_dir.exists():
        click.echo("   状态目录不存在")
        return
    
    click.echo(f"   状态目录: {state_dir}")


def _init_project(init_path: str):
    """初始化项目"""
    click.echo(f"🚀 初始化项目: {init_path}")
    
    path = Path(init_path)
    if path.exists():
        click.echo(f"   目录已存在: {path}")
    else:
        path.mkdir(parents=True)
        click.echo(f"   创建目录: {path}")
    
    state_dir = path / ".sprintcycle" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"   创建状态目录: {state_dir}")
    
    click.echo("\n✅ 项目初始化完成")


def _run_prd_file(prd_file: str, dry_run: bool, verbose: bool):
    """执行 PRD 文件"""
    try:
        parser = PRDParser()
        prd = parser.parse_file(prd_file)
        
        click.echo(f"📄 PRD 文件: {prd_file}")
        click.echo(f"   项目: {prd.project.name}")
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

    except PRDParseError as e:
        click.echo(f"❌ PRD 解析错误: {e}")
        sys.exit(1)
    except YAMLError as e:
        click.echo(f"❌ YAML 错误: {e}")
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


# CLI 入口点 - 使用 click 装饰器
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
@click.version_option(version='0.7.0', prog_name='sprintcycle')
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
    
    if status:
        _show_status()
        return
    
    if init_path:
        _init_project(init_path)
        return
    
    intent = _resolve_intent(intent, args)
    
    try:
        parsed = _parse_and_show(intent, project, target, mode, constraints)
        
        if parsed.action == ActionType.RUN:
            _handle_run_action(parsed, dry_run, verbose)
        else:
            _generate_and_execute(parsed, dry_run)
            
    except YAMLError as e:
        click.echo(f"❌ YAML 解析错误: {e}")
        sys.exit(1)
    except PRDParseError as e:
        click.echo(f"❌ PRD 解析错误: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 执行错误: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()  # Use click's auto-discovery
