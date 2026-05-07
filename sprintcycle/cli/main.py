"""Click 根命令 ``cli`` 与各子模块注册。"""

from __future__ import annotations

import click

from sprintcycle.cli._common import (
    _ensure_rich_traceback,
    _package_version,
    _print_result,
    console,
)
from sprintcycle.cli.config import register as register_config
from sprintcycle.cli.dashboard import register as register_dashboard
from sprintcycle.cli.evolve import register as register_evolve
from sprintcycle.cli.governance import register as register_governance
from sprintcycle.cli.hitl_product import register as register_hitl_product
from sprintcycle.logging_setup import configure_sprintcycle_logging


@click.group(invoke_without_command=True)
@click.option("-p", "--project", default=".", help="项目路径")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.version_option(version=_package_version(), prog_name="sprintcycle")
@click.pass_context
def cli(ctx: click.Context, project: str, fmt: str, verbose: bool) -> None:
    """SprintCycle — 意图驱动 + 敏捷 Sprint 闭环（执行计划 YAML，Scrum 对齐见文档）

    意图 → Release Plan（YAML）→ 编排执行

    \b
    快捷用法:
      sprintcycle "优化性能"              # 等同于 sprintcycle run
    """
    _ensure_rich_traceback()
    configure_sprintcycle_logging(
        stderr_level="DEBUG" if verbose else "INFO",
    )
    ctx.ensure_object(dict)
    # 从包命名空间解析，便于测试 ``patch('sprintcycle.cli.SprintCycle', ...)``
    from sprintcycle.cli import SprintCycle as _SprintCycle

    ctx.obj["sc"] = _SprintCycle(project_path=project)
    ctx.obj["fmt"] = fmt
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        args = ctx.args
        if args:
            result = ctx.obj["sc"].run(intent=" ".join(args))
            _print_result(result, fmt)
        else:
            console.print(ctx.get_help())


register_config(cli)
register_dashboard(cli)
register_evolve(cli)
register_governance(cli)
register_hitl_product(cli)


if __name__ == "__main__":
    cli()
