"""
Tests for ReleasePlan Generator module.

Coverage targets:
- sprintcycle/release_plan/generator.py
"""

from pathlib import Path

import pytest

from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.domain.intent.parser import ActionType, ParsedIntent
from sprintcycle.execution.planners.generator import (
    IntentReleasePlanGenerator,
    EvolutionParams,
    ExecutionMode,
)
from sprintcycle.domain.generic.models import ReleasePlan


class TestIntentReleasePlanGenerator:
    """IntentReleasePlanGenerator tests"""

    def test_basic_creation(self):
        gen = IntentReleasePlanGenerator()
        assert gen is not None

    def test_generate_from_parsed_intent(self):
        gen = IntentReleasePlanGenerator()
        intent = ParsedIntent(
            action=ActionType.BUILD,
            description="add user authentication",
            target="src/auth.py",
        )
        plan = IntentReleasePlanGenerator.generate(intent)
        assert isinstance(plan, ReleasePlan)


class TestEvolutionParams:
    """EvolutionParams tests"""

    def test_basic_creation(self):
        params = EvolutionParams(
            targets=["sprintcycle/"],
            goals=["improve coverage"],
        )
        assert params.targets == ["sprintcycle/"]
        assert params.goals == ["improve coverage"]

    def test_defaults(self):
        params = EvolutionParams()
        assert isinstance(params.targets, list)
        assert isinstance(params.goals, list)


class TestActionType:
    """ActionType enum tests"""

    def test_all_types_exist(self):
        assert ActionType.BUILD == ActionType.BUILD
        assert ActionType.EVOLVE == ActionType.EVOLVE
        assert ActionType.FIX == ActionType.FIX
        assert ActionType.RUN == ActionType.RUN
        assert ActionType.TEST == ActionType.TEST


class TestExecutionMode:
    """ExecutionMode enum tests"""

    def test_all_modes_exist(self):
        assert ExecutionMode.NORMAL == ExecutionMode.NORMAL
        assert ExecutionMode.EVOLUTION == ExecutionMode.EVOLUTION


class TestEvolveProductLayout:
    """非自进化进化意图：产品目录落在可配置 code_root/products/<slug>/"""

    def test_non_self_evolution_creates_products_subdirectory(self, tmp_path):
        cfg = RuntimeConfig()
        cfg.product_code_root = "."
        cfg.products_subdir = "products"
        intent = ParsedIntent(
            action=ActionType.EVOLVE,
            description="optimize payment module",
            product="acme-pay",
        )
        plan = IntentReleasePlanGenerator.generate(
            intent, config=cfg, anchor_project_path=str(tmp_path)
        )
        expected = (tmp_path / "products" / "acme-pay").resolve()
        assert Path(plan.project.path).resolve() == expected
        assert expected.is_dir()
        assert plan.project.name == "acme-pay"

    def test_self_evolution_uses_framework_root(self, tmp_path):
        intent = ParsedIntent(
            action=ActionType.BUILD,
            description="优化 sprintcycle 自身代码",
        )
        plan = IntentReleasePlanGenerator.generate(
            intent, config=RuntimeConfig(), anchor_project_path=str(tmp_path)
        )
        assert plan.project.name == "sprintcycle"
        assert Path(plan.project.path).resolve() == IntentReleasePlanGenerator._get_sprintcycle_root().resolve()

    def test_evolve_without_product_raises(self, tmp_path):
        intent = ParsedIntent(
            action=ActionType.EVOLVE,
            description="generic optimize wording without product slug",
        )
        with pytest.raises(ValueError, match="product"):
            IntentReleasePlanGenerator.generate(
                intent,
                config=RuntimeConfig(),
                anchor_project_path=str(tmp_path),
            )
