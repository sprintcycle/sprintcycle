"""SprintCycle CLI — click-based command-line interface."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import click

from .api import SprintCycle
from .results import (
    DiagnoseResult,
    PlanResult,
    RollbackResult,
    RunResult,
    StatusResult,
    StopResult,
)


@click.group()
@click.option("-p", "--project-path", default=".", help="Project path")
@click.pass_context
def cli(ctx: click.Context, project_path: str) -> None:
    """SprintCycle — intelligent software iteration framework."""
    ctx.ensure_object(dict)
    ctx.obj["project_path"] = os.path.abspath(project_path)


@cli.command()
@click.argument("intent", required=False, default="")
@click.option("-m", "--mode", default="auto", help="Execution mode")
@click.pass_context
def plan(ctx: click.Context, intent: str, mode: str) -> None:
    """Plan: intent → Release Plan YAML."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.plan(intent=intent, mode=mode)
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


@cli.command()
@click.argument("intent", required=False, default="")
@click.option("-m", "--mode", default="auto", help="Execution mode")
@click.option("--resume", default="", help="Execution ID to resume")
@click.pass_context
def run(ctx: click.Context, intent: str, mode: str, resume: str) -> None:
    """Run: execute a plan or resume an existing execution."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.run(intent=intent, mode=mode, resume=resume)
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


@cli.command()
@click.option("--execution-id", default="", help="Execution ID")
@click.pass_context
def status(ctx: click.Context, execution_id: str) -> None:
    """Status: show execution state."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.status(execution_id=execution_id)
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


@cli.command()
@click.option("--execution-id", default="", help="Execution ID")
@click.pass_context
def stop(ctx: click.Context, execution_id: str) -> None:
    """Stop: halt a running execution."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.stop(execution_id=execution_id)
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


@cli.command()
@click.pass_context
def diagnose(ctx: click.Context) -> None:
    """Diagnose: inspect project health."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.diagnose()
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


@cli.command()
@click.option("--execution-id", required=True, help="Execution ID to rollback")
@click.pass_context
def rollback(ctx: click.Context, execution_id: str) -> None:
    """Rollback: revert an execution."""
    sc = SprintCycle(project_path=ctx.obj["project_path"])
    result = sc.rollback(execution_id=execution_id)
    click.echo(result.to_dict() if hasattr(result, "to_dict") else str(result))


if __name__ == "__main__":
    cli()
