"""治理门禁、validate 别名与 model-compare。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import click
from rich.markup import escape
from rich.panel import Panel

from sprintcycle.api import SprintCycle
from sprintcycle.entrypoints.cli._common import console, err_console


def _governance_check_run_and_print(ctx: click.Context, gate: str) -> None:
    """执行门禁、落盘、打印；失败时 ``sys.exit(1)``。"""
    from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
    from sprintcycle.governance.runner import run_governance_check_and_persist

    sc: SprintCycle = ctx.obj["sc"]
    cfg = RuntimeConfig.from_project(sc.project_path)
    planning_report, review_report, fail = run_governance_check_and_persist(sc.project_path, cfg, gate)

    if ctx.obj["fmt"] == "json":
        out: dict[str, Any] = {}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        out["should_fail_ci"] = fail
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if planning_report is not None:
            console.print(Panel.fit(f"[bold]Planning[/bold] violations={len(planning_report.violations)}", title="治理"))
            for v in planning_report.violations[:15]:
                console.print(f"  [{v.severity}] {escape(v.rule_id)}: {escape(v.message[:200])}")
        if review_report is not None:
            console.print(Panel.fit(f"[bold]Review[/bold] violations={len(review_report.violations)}", title="治理"))
            for v in review_report.violations[:15]:
                console.print(f"  [{v.severity}] {escape(v.rule_id)}: {escape(v.message[:200])}")
        if fail:
            err_console.print("[red]根据 governance_block_on 配置，本次检查视为失败。[/red]")

    if fail:
        raise SystemExit(1)


def register(cli: click.Group) -> None:
    @cli.group("governance")
    def governance_group() -> None:
        """代码治理与质量门禁（见 docs/GOVERNANCE_ENGINEERING.md）"""

    @governance_group.command("check")
    @click.option(
        "--gate",
        type=click.Choice(["review", "planning", "both"]),
        default="review",
        help="执行的检查包",
    )
    @click.pass_context
    def governance_check(ctx: click.Context, gate: str) -> None:
        """对项目根执行 Review / Planning 治理（不跑完整 Sprint）。

        成功后写入 ``governance_report_dir`` 下 ``governance_planning_last.json`` / ``governance_last.json``；
        若 ``[governance] cli_emit_events = true``，另向执行事件后端派发 ``GOVERNANCE_GATE``（与 Dashboard SSE 对齐）。
        """
        _governance_check_run_and_print(ctx, gate)

    @cli.command("validate")
    @click.option(
        "--gate",
        type=click.Choice(["review", "planning", "both"]),
        default="review",
        help="执行的检查包（与 ``governance check`` 相同）",
    )
    @click.pass_context
    def validate_cmd(ctx: click.Context, gate: str) -> None:
        """与 ``sprintcycle governance check`` 等价（v1 多源方案文档中的 validate 入口）。"""
        _governance_check_run_and_print(ctx, gate)

    @governance_group.command("model-compare")
    @click.option(
        "--env1",
        multiple=True,
        default=(),
        help="第一遍 pytest 前附加的环境变量 KEY=VALUE（可重复）",
    )
    @click.option(
        "--env2",
        multiple=True,
        default=(),
        help="第二遍 pytest 前附加的环境变量 KEY=VALUE（可重复）",
    )
    @click.option(
        "--output",
        "out_path",
        type=click.Path(path_type=Path),
        default=None,
        help="写入 JSON 报告路径；默认 <report_dir>/model_compare_last.json",
    )
    @click.option(
        "--quick",
        is_flag=True,
        default=False,
        help="未传 pytest 参数时使用 tests/ -q --tb=no -m golden（大仓库模型对比更快）",
    )
    @click.argument("pytest_args", nargs=-1)
    @click.pass_context
    def governance_model_compare(
        ctx: click.Context,
        env1: tuple[str, ...],
        env2: tuple[str, ...],
        out_path: Optional[Path],
        quick: bool,
        pytest_args: tuple[str, ...],
    ) -> None:
        """同一仓库连续跑两遍 pytest（junitxml），对比失败用例集合与退出码。

        用于切换 ``LLM_MODEL`` 等环境后的回归基线对比。未传 pytest 参数时默认 ``tests/ -q --tb=no``；
        使用 ``--quick`` 时默认追加 ``-m golden``（见 ``docs/GOVERNANCE_GOLDEN.md``）。
        """
        from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
        from sprintcycle.governance.model_compare import run_model_compare

        sc: SprintCycle = ctx.obj["sc"]
        cfg = RuntimeConfig.from_project(sc.project_path)
        if pytest_args:
            args = list(pytest_args)
        elif quick:
            args = ["tests/", "-q", "--tb=no", "-m", "golden"]
        else:
            args = ["tests/", "-q", "--tb=no"]
        rep = run_model_compare(Path(sc.project_path), args, env1, env2)

        rel = getattr(cfg, "governance_report_dir", None) or ".sprintcycle"
        root = Path(sc.project_path).resolve()
        out_dir = root / rel if not Path(rel).is_absolute() else Path(rel)
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_path or (out_dir / "model_compare_last.json")
        dest.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

        diff_failures = not rep.get("failure_sets_equal", True)
        diff_exit = rep.get("exit_code_run1") != rep.get("exit_code_run2")
        fail = diff_failures or diff_exit

        if ctx.obj["fmt"] == "json":
            out = dict(rep)
            out["report_path"] = str(dest)
            out["should_fail_ci"] = fail
            click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            console.print(
                Panel.fit(
                    f"run1 exit={rep.get('exit_code_run1')} failures={rep.get('failed_count_run1')}\n"
                    f"run2 exit={rep.get('exit_code_run2')} failures={rep.get('failed_count_run2')}\n"
                    f"failure_sets_equal={rep.get('failure_sets_equal')}\n"
                    f"报告 → {escape(str(dest))}",
                    title="[bold]model-compare[/bold]",
                )
            )
            if rep.get("failed_only_run1"):
                console.print("[yellow]仅在 run1 失败:[/yellow]", escape(str(rep["failed_only_run1"][:10])))
            if rep.get("failed_only_run2"):
                console.print("[yellow]仅在 run2 失败:[/yellow]", escape(str(rep["failed_only_run2"][:10])))

        if fail:
            err_console.print("[red]两次运行结果不一致（退出码或失败用例集合）。[/red]")
            raise SystemExit(1)
