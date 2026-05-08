"""SprintCycle CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import click

from .config import RuntimeConfig
from .execution.project_write import ProjectWriteStrategy


@click.group()
def cli() -> None:
    """SprintCycle 命令行入口。"""


@cli.command()
@click.argument("intent")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--reference", "references", multiple=True, type=click.Path(path_type=Path), help="参考项目路径，可重复")
@click.option("--write-policy", type=click.Choice(["create", "incremental", "safe"], case_sensitive=False), default="incremental", show_default=True)
def run(intent: str, project: Path, references: List[Path], write_policy: str) -> None:
    """统一运行入口：新建、增量修改、参考生成。"""
    config = RuntimeConfig(project_path=str(project), reference_projects=[str(p) for p in references], write_policy=write_policy)
    strategy = ProjectWriteStrategy(str(project), [str(p) for p in references], write_policy=config.write_policy)
    plan = strategy.build_plan(intent)
    applied = strategy.apply_template(plan)
    summary = strategy.write_summary(applied)
    click.echo(json.dumps({"project": str(project), "references": [str(p) for p in references], "write_policy": write_policy, "target_exists": applied.target_exists, "created_files": applied.created_files, "modified_files": applied.modified_files, "skipped_files": applied.skipped_files, "backups": [b.__dict__ for b in applied.backups], "git": applied.git.__dict__ if applied.git else None, "summary": str(summary)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
