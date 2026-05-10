"""计划 / 执行 / 向导 / 知识检索等核心子命令。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click
import questionary
from questionary import Choice
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from sprintcycle.api import SprintCycle
from sprintcycle.entrypoints.cli._common import (
    _print_result,
    _require_tty_for_interactive,
    console,
    err_console,
)


def register(cli: click.Group) -> None:
    @cli.command("wizard")
    @click.pass_context
    def wizard(ctx: click.Context) -> None:
        """交互式向导：多步选择后执行 plan / run / diagnose / status"""
        if ctx.obj["fmt"] == "json":
            raise click.UsageError("wizard 不支持 --format json（交互仅面向人类可读终端）")
        _require_tty_for_interactive("wizard")

        questionary.print("SprintCycle — 交互式向导\n", style="bold")

        action = questionary.select(
            "要执行的操作？",
            choices=[
                Choice("生成执行计划（不执行）", value="plan"),
                Choice("执行 Sprint（run）", value="run"),
                Choice("项目体检（diagnose）", value="diagnose"),
                Choice("查看执行状态 / 历史（status）", value="status"),
            ],
        ).ask()

        if action is None:
            raise SystemExit(1)

        sc: SprintCycle = ctx.obj["sc"]
        fmt = ctx.obj["fmt"]

        if action == "diagnose":
            _print_result(sc.diagnose(), fmt)
            return

        if action == "status":
            eid = questionary.text(
                "执行 ID（留空列出全部历史）:",
                default="",
            ).ask()
            if eid is None:
                raise SystemExit(1)
            eid = (eid or "").strip() or None
            _print_result(sc.status(execution_id=eid), fmt)
            return

        intent = questionary.text(
            "意图描述（自然语言）:",
            validate=lambda t: bool(str(t).strip()) or "请输入非空意图",
        ).ask()
        if intent is None:
            raise SystemExit(1)

        mode = questionary.select(
            "模式:",
            choices=["auto", "evolution", "normal", "fix", "test"],
            default="auto",
        ).ask()
        if mode is None:
            raise SystemExit(1)

        target = questionary.text("目标文件或模块（可选，直接回车跳过）:", default="").ask()
        if target is None:
            raise SystemExit(1)
        target = (target or "").strip() or None

        product = questionary.text(
            "进化模式产品英文名 -P（可选，直接回车跳过）:",
            default="",
        ).ask()
        if product is None:
            raise SystemExit(1)
        product = (product or "").strip() or None

        if not questionary.confirm("确认执行？", default=True).ask():
            console.print("[dim]已取消。[/dim]")
            return

        if action == "plan":
            _print_result(
                sc.plan(
                    intent=intent.strip(),
                    mode=mode,
                    target=target,
                    product=product,
                    release_plan_path=None,
                ),
                fmt,
            )
        else:
            _print_result(
                sc.run(
                    intent=intent.strip(),
                    mode=mode,
                    target=target,
                    product=product,
                    release_plan_path=None,
                    release_plan_yaml=None,
                    resume=False,
                    execution_id=None,
                    confirm_knowledge=False,
                ),
                fmt,
            )

    @cli.command()
    @click.argument("intent")
    @click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
    @click.option("-t", "--target", default=None, help="目标文件/模块")
    @click.option(
        "-P",
        "--product",
        default=None,
        help="进化模式下的英文产品名（与意图中 product: Name 等价）；代码写入 products/<name>/",
    )
    @click.option(
        "--reference",
        "reference_paths",
        multiple=True,
        help="参考项目路径（可重复）；只读借鉴，写入仍在全局 -p 目标项目",
    )
    @click.option(
        "--write-policy",
        "write_policy",
        type=click.Choice(["auto", "create", "incremental", "safe"]),
        default="auto",
        help="写入策略：auto 按目标是否存在推断 | create 骨架优先 | incremental 增量 | safe 仅新增不改已有文件",
    )
    @click.option(
        "--release-plan",
        "release_plan_path",
        default=None,
        help="已有执行计划 YAML 文件路径（.yaml/.yml）",
    )
    @click.pass_context
    def plan(
        ctx: click.Context,
        intent: str,
        mode: str,
        target: Optional[str],
        product: Optional[str],
        reference_paths: tuple[str, ...],
        write_policy: str,
        release_plan_path: Optional[str],
    ) -> None:
        """生成 Sprint 执行计划（不执行）"""
        result = ctx.obj["sc"].plan(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_path=release_plan_path,
            product=product,
            reference_paths=list(reference_paths) if reference_paths else None,
            write_policy=write_policy,
        )
        _print_result(result, ctx.obj["fmt"])

    @cli.command()
    @click.argument("intent", required=False)
    @click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
    @click.option("-t", "--target", default=None, help="目标文件/模块")
    @click.option(
        "-P",
        "--product",
        default=None,
        help="进化模式下的英文产品名（与意图中 product: Name 等价）",
    )
    @click.option(
        "--release-plan",
        "release_plan_path",
        default=None,
        help="执行计划 YAML 文件路径",
    )
    @click.option(
        "--release-plan-yaml",
        "release_plan_yaml",
        default=None,
        help="执行计划 YAML 文本（与 plan 返回的 release_plan_yaml 同形）",
    )
    @click.option(
        "--reference",
        "reference_paths",
        multiple=True,
        help="参考项目路径（可重复）；只读借鉴，写入仍在全局 -p 目标项目",
    )
    @click.option(
        "--write-policy",
        "write_policy",
        type=click.Choice(["auto", "create", "incremental", "safe"]),
        default="auto",
        help="写入策略：auto | create | incremental | safe（仅新增不改已有文件）",
    )
    @click.option("--resume", is_flag=True, help="断点续跑")
    @click.option("--execution-id", default=None, help="执行 ID（resume 时使用）")
    @click.option(
        "--yes",
        "confirm_knowledge",
        is_flag=True,
        help="在 require_knowledge_injection_confirm 开启时确认知识注入并继续执行",
    )
    @click.pass_context
    def run(
        ctx: click.Context,
        intent: Optional[str],
        mode: str,
        target: Optional[str],
        product: Optional[str],
        reference_paths: tuple[str, ...],
        write_policy: str,
        release_plan_path: Optional[str],
        release_plan_yaml: Optional[str],
        resume: bool,
        execution_id: Optional[str],
        confirm_knowledge: bool,
    ) -> None:
        """执行 Sprint"""
        result = ctx.obj["sc"].run(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_path=release_plan_path,
            release_plan_yaml=release_plan_yaml,
            resume=resume,
            execution_id=execution_id,
            confirm_knowledge=confirm_knowledge,
            product=product,
            reference_paths=list(reference_paths) if reference_paths else None,
            write_policy=write_policy,
        )
        _print_result(result, ctx.obj["fmt"])

    @cli.command()
    @click.pass_context
    def diagnose(ctx: click.Context) -> None:
        """诊断项目健康状态"""
        result = ctx.obj["sc"].diagnose()
        _print_result(result, ctx.obj["fmt"])

    @cli.command()
    @click.argument("execution_id", required=False)
    @click.pass_context
    def status(ctx: click.Context, execution_id: Optional[str]) -> None:
        """查询执行状态（不传 ID 则列出所有记录）"""
        result = ctx.obj["sc"].status(execution_id=execution_id)
        _print_result(result, ctx.obj["fmt"])

    @cli.command()
    @click.argument("execution_id")
    @click.pass_context
    def rollback(ctx: click.Context, execution_id: str) -> None:
        """回滚到执行前的状态"""
        result = ctx.obj["sc"].rollback(execution_id=execution_id)
        _print_result(result, ctx.obj["fmt"])

    @cli.command()
    @click.argument("execution_id")
    @click.pass_context
    def stop(ctx: click.Context, execution_id: str) -> None:
        """停止正在执行的 Sprint"""
        result = ctx.obj["sc"].stop(execution_id=execution_id)
        _print_result(result, ctx.obj["fmt"])

    @cli.command("execution-events")
    @click.argument("execution_id")
    @click.option("--limit", default=200, type=int, help="最多返回条数（上限由实现裁剪）")
    @click.pass_context
    def execution_events_cmd(ctx: click.Context, execution_id: str, limit: int) -> None:
        """只读：列出已持久化到 SQLite MQ 的执行事件（execution_event_backend=sqlite 时才有数据）"""
        sc: SprintCycle = ctx.obj["sc"]
        data = sc.execution_events(execution_id, limit=limit)
        if ctx.obj["fmt"] == "json":
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
            return
        if not data.get("success"):
            err_console.print(f"[red]失败[/red] {escape(str(data.get('error', '')))}")
            raise SystemExit(1)
        msg = data.get("message")
        if msg:
            console.print(Panel.fit(escape(str(msg)), title="execution-events"))
        rows = data.get("data") or []
        if not rows:
            console.print("暂无事件记录（检查 execution_event_backend 与 .sprintcycle/data/exec_events.sqlite）")
            return
        t = Table(title="执行事件（时间正序）")
        t.add_column("时间", max_width=22)
        t.add_column("类型", max_width=28)
        t.add_column("摘要", max_width=48)
        for r in rows:
            if not isinstance(r, dict):
                continue
            d = r.get("data") if isinstance(r.get("data"), dict) else {}
            hint = ""
            for k in ("description", "sprint_index", "status", "message"):
                v = d.get(k)
                if v is not None and str(v):
                    hint = f"{k}={str(v)[:40]}"
                    break
            t.add_row(
                str(r.get("timestamp") or r.get("created_at") or "")[:20],
                str(r.get("event_type", "")),
                escape(hint or "(no data)"),
            )
        console.print(t)

    @cli.command("import-state")
    @click.option(
        "--json-dir",
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        required=True,
        help="原 JSON StateStore 目录（含 *.json）",
    )
    @click.option(
        "--sqlite",
        "sqlite_db",
        type=click.Path(path_type=Path),
        required=True,
        help="目标 SQLite 数据库文件路径",
    )
    @click.pass_context
    def import_state(ctx: click.Context, json_dir: Path, sqlite_db: Path) -> None:
        """将 JSON 执行状态导入 SQLite（与 storage.backend=sqlite 共用库）"""
        from sprintcycle.persistence.import_json_state import import_json_executions_to_sqlite

        n = import_json_executions_to_sqlite(json_dir, sqlite_db)
        console.print(
            Panel.fit(
                f"已导入 [bold green]{n}[/bold green] 条执行记录\n→ {escape(str(sqlite_db))}",
                title="[bold green]✅ import-state[/bold green]",
            )
        )

    @cli.group("knowledge")
    def knowledge_group() -> None:
        """知识卡片检索（P1）"""

    @knowledge_group.command("search")
    @click.option("-q", "--query", default="", help="关键词（匹配 domain/body/outcome）")
    @click.option("--tag", multiple=True, help="标签（可重复，全部匹配）")
    @click.option("--limit", default=50, type=int)
    @click.pass_context
    def knowledge_search(ctx: click.Context, query: str, tag: tuple[str, ...], limit: int) -> None:
        """检索知识卡片"""
        data = ctx.obj["sc"].knowledge_search(query=query, tags=list(tag), limit=limit)
        if ctx.obj["fmt"] == "json":
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
            return

        cards = data.get("cards", [])[:20]
        t = Table(title=f"知识卡片 [dim]({data.get('count', 0)} 条，展示前 {len(cards)} 条)[/dim]")
        t.add_column("ID", style="dim", max_width=12)
        t.add_column("领域")
        t.add_column("摘要", max_width=72)
        for c in cards:
            cid = str(c.get("id", ""))
            cid_show = (cid[:8] + "…") if len(cid) > 9 else cid
            body = (c.get("body") or "")[:80]
            t.add_row(escape(cid_show), escape(str(c.get("domain", ""))), escape(body))
        console.print(t)
