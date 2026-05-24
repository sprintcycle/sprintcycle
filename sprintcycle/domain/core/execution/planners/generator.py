"""
从意图生成 Release Plan（执行计划）

将 ParsedIntent 转换为 ``ReleasePlan`` 内存模型。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from sprintcycle.domain.core.evolution.context import EvolutionContext
from sprintcycle.domain.supporting.intent.parser import ActionType, ParsedIntent
from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.domain.generic.models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


class IntentReleasePlanGenerator:
    """将 ParsedIntent 转换为 ``ReleasePlan``。"""

    EVOLUTION_PROJECT_KEYWORDS = ["sprintcycle", "sprint cycle", "self", "自身", "自己"]
    EVOLUTION_ACTION_KEYWORDS = [
        "进化",
        "evolve",
        "优化",
        "optimize",
        "improve",
        "增强",
        "enhance",
        "重构",
        "refactor",
        "self-evolution",
    ]

    @staticmethod
    def generate(
        parsed: ParsedIntent,
        *,
        config: Optional[RuntimeConfig] = None,
        anchor_project_path: Optional[str] = None,
        evolution_context: Optional[dict[str, Any]] = None,
    ) -> ReleasePlan:
        cfg = config or RuntimeConfig()
        anchor = anchor_project_path or os.getcwd()
        evo_ctx = EvolutionContext.from_dict(evolution_context or {}) if evolution_context else None

        if parsed.description:
            inferred_mode = IntentReleasePlanGenerator._infer_mode_from_intent(parsed.description)
            if inferred_mode == ExecutionMode.EVOLUTION:
                return IntentReleasePlanGenerator._from_evolve(parsed, cfg, anchor, evo_ctx)

        if evo_ctx and evo_ctx.decision and evo_ctx.decision.should_replan:
            return IntentReleasePlanGenerator._from_evolve(parsed, cfg, anchor, evo_ctx)

        if parsed.action == ActionType.EVOLVE:
            return IntentReleasePlanGenerator._from_evolve(parsed, cfg, anchor, evo_ctx)
        if parsed.action == ActionType.FIX:
            return IntentReleasePlanGenerator._from_fix(parsed, anchor)
        if parsed.action == ActionType.TEST:
            return IntentReleasePlanGenerator._from_test(parsed, anchor)
        if parsed.action == ActionType.RUN:
            return IntentReleasePlanGenerator._from_run(parsed, anchor)
        return IntentReleasePlanGenerator._from_build(parsed, anchor)

    @staticmethod
    def _infer_mode_from_intent(description: str) -> Optional[ExecutionMode]:
        if not description:
            return None
        desc_lower = description.lower()
        has_project = any(kw in desc_lower for kw in IntentReleasePlanGenerator.EVOLUTION_PROJECT_KEYWORDS)
        has_action = any(kw in desc_lower for kw in IntentReleasePlanGenerator.EVOLUTION_ACTION_KEYWORDS)
        return ExecutionMode.EVOLUTION if has_project and has_action else None

    @staticmethod
    def _is_self_evolution_intent(description: Optional[str]) -> bool:
        return (
            bool(description)
            and IntentReleasePlanGenerator._infer_mode_from_intent(description) == ExecutionMode.EVOLUTION
        )

    @staticmethod
    def _sanitize_product_slug(raw: str) -> str:
        s = raw.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", s):
            raise ValueError(
                "产品名须为英文标识（字母开头，仅含字母、数字、下划线与连字符）；"
                f"在意图中写明 product: YourName 或传入 product=...，当前无效: {raw!r}"
            )
        return s

    @staticmethod
    def _resolve_product_code_root(cfg: RuntimeConfig, anchor: str) -> Path:
        raw = (cfg.product_code_root or ".").strip() or "."
        p = Path(raw)
        if p.is_absolute():
            return p.resolve()
        return (Path(anchor).expanduser().resolve() / p).resolve()

    @staticmethod
    def _safe_products_subdir(cfg: RuntimeConfig) -> str:
        sub = (cfg.products_subdir or "products").strip().replace("\\", "/").strip("/")
        if not sub or ".." in Path(sub).parts:
            raise ValueError("无效的 products_subdir 配置（须为非空相对路径片段，不能含 ..）")
        return sub

    @staticmethod
    def _infer_mode_from_target(target: Optional[str], project: Optional[str]) -> ExecutionMode:
        return ExecutionMode.NORMAL

    @staticmethod
    def _get_sprintcycle_root() -> Path:
        return Path(__file__).parent.parent.parent

    @staticmethod
    def _from_evolve(
        parsed: ParsedIntent,
        config: RuntimeConfig,
        anchor_project_path: str,
        evolution_context: Optional[EvolutionContext] = None,
    ) -> ReleasePlan:
        if IntentReleasePlanGenerator._is_self_evolution_intent(parsed.description):
            project_path_str = str(parsed.project or IntentReleasePlanGenerator._get_sprintcycle_root())
            project_name = "sprintcycle"
            version = "v0.6.0"
        else:
            slug_raw = (parsed.product or "").strip()
            if not slug_raw:
                raise ValueError(
                    "非自进化类的进化意图须指定英文产品名：在意图中写明 product: YourName，"
                    "或使用 API/CLI 的 product 参数。代码将写入 <product_code_root>/<products_subdir>/YourName/。"
                )
            slug = IntentReleasePlanGenerator._sanitize_product_slug(slug_raw)
            base = IntentReleasePlanGenerator._resolve_product_code_root(config, anchor_project_path)
            sub = IntentReleasePlanGenerator._safe_products_subdir(config)
            dest = base / sub / slug
            dest.mkdir(parents=True, exist_ok=True)
            project_path_str = str(dest.resolve())
            project_name = slug
            version = "v1.0.0"

        project = ProductAnchor(name=project_name, path=project_path_str, version=version)

        goals = [parsed.description]
        constraints = list(parsed.constraints)
        evo_meta: dict[str, Any] = {}
        if evolution_context is not None:
            if evolution_context.historical_goals:
                goals = list(evolution_context.historical_goals[-3:]) + goals
            for item in evolution_context.historical_constraints:
                if item not in constraints:
                    constraints.append(item)
            evo_meta = {
                "target_type": evolution_context.target.target_type,
                "strategy_profile": evolution_context.strategy_profile,
                "decision": evolution_context.decision.to_dict() if evolution_context.decision else None,
                "risk_level": evolution_context.risk_level,
            }

        evolution = EvolutionParams(
            targets=[parsed.target] if parsed.target else [],
            goals=goals,
            constraints=constraints,
            max_variations=5,
            iterations=3,
        )

        plan = ReleasePlan(project=project, mode=ExecutionMode.EVOLUTION, evolution=evolution, sprints=[])
        if evo_meta:
            plan.metadata["evolution_summary"] = evo_meta
        return plan

    @staticmethod
    def _from_build(parsed: ParsedIntent, anchor_project_path: str) -> ReleasePlan:
        project_path = parsed.project or anchor_project_path or os.getcwd()
        project_path = str(Path(project_path).expanduser().resolve())
        project_name = os.path.basename(project_path)
        project = ProductAnchor(name=project_name, path=project_path, version="v1.0.0")
        sprint = SprintDefinition(
            name="Feature Development",
            goals=[parsed.description],
            tasks=[
                SprintBacklogItem(
                    description=parsed.description, agent="coder", target=parsed.target, constraints=parsed.constraints
                )
            ],
        )
        return ReleasePlan(project=project, mode=ExecutionMode.NORMAL, sprints=[sprint])

    @staticmethod
    def _from_fix(parsed: ParsedIntent, anchor_project_path: str) -> ReleasePlan:
        error_info = IntentReleasePlanGenerator._parse_error_info(parsed.description)
        target_file = parsed.target or error_info.get("file")
        project_path = parsed.project or anchor_project_path or os.getcwd()
        project_path_str = str(Path(project_path).expanduser().resolve())
        project_name = os.path.basename(project_path_str)
        project = ProductAnchor(name=project_name, path=project_path_str, version="v1.0.0")
        fix_goal = f"修复错误: {parsed.description}"
        if error_info.get("error_type"):
            fix_goal = f"修复 {error_info['error_type']}: {error_info.get('error_msg', parsed.description)}"
        evolution = EvolutionParams(
            targets=[target_file] if target_file else [],
            goals=[fix_goal],
            constraints=parsed.constraints,
            max_variations=5,
            iterations=3,
        )
        return ReleasePlan(project=project, mode=ExecutionMode.EVOLUTION, evolution=evolution, sprints=[])

    @staticmethod
    def _parse_error_info(error_text: str) -> dict[str, Any]:
        info: dict[str, Any] = {}
        if not error_text:
            return info
        patterns = {
            "file": r'File "([^"]+)"',
            "line": r", line (\d+)",
            "error_type": r"^(\w+Error|\w+Exception):",
            "error_msg": r": (.+)$",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, error_text, re.MULTILINE)
            if match:
                info[key] = match.group(1)
        if not info.get("error_type"):
            simple_match = re.match(r"(\w+Error|\w+Exception):?\s*(.*)", error_text)
            if simple_match:
                info["error_type"] = simple_match.group(1)
                if simple_match.group(2):
                    info["error_msg"] = simple_match.group(2)
        return info

    @staticmethod
    def _from_test(parsed: ParsedIntent, anchor_project_path: str) -> ReleasePlan:
        return IntentReleasePlanGenerator._from_build(parsed, anchor_project_path)

    @staticmethod
    def _from_run(parsed: ParsedIntent, anchor_project_path: str) -> ReleasePlan:
        return IntentReleasePlanGenerator._from_build(parsed, anchor_project_path)

    @staticmethod
    def sample_release_plan() -> ReleasePlan:
        project = ProductAnchor(name="demo", path="./demo", version="v1.0.0")
        sprint = SprintDefinition(
            name="Sprint 1",
            goals=["实现基础功能"],
            tasks=[
                SprintBacklogItem(description="实现用户认证", agent="coder"),
                SprintBacklogItem(description="编写单元测试", agent="tester"),
            ],
        )
        return ReleasePlan(project=project, mode=ExecutionMode.NORMAL, sprints=[sprint])
