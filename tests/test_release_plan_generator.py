"""
Tests for PRD Generator module.

Coverage targets:
- sprintcycle/release_plan/generator.py
"""

from pathlib import Path

import pytest

from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.intent.parser import ActionType, ParsedIntent
from sprintcycle.release_plan.generator import (
    IntentPRDGenerator,
    PRDEvolutionParams,
    ExecutionMode,
)
from sprintcycle.release_plan.models import PRD


class TestIntentPRDGenerator:
    """IntentPRDGenerator tests"""

    def test_basic_creation(self):
        gen = IntentPRDGenerator()
        assert gen is not None

    def test_generate_from_parsed_intent(self):
        gen = IntentPRDGenerator()
        intent = ParsedIntent(
            action=ActionType.BUILD,
            description="add user authentication",
            target="src/auth.py",
        )
        prd = IntentPRDGenerator.generate(intent)
        assert isinstance(prd, PRD)


class TestPRDEvolutionParams:
    """PRDEvolutionParams tests"""

    def test_basic_creation(self):
        params = PRDEvolutionParams(
            targets=["sprintcycle/"],
            goals=["improve coverage"],
        )
        assert params.targets == ["sprintcycle/"]
        assert params.goals == ["improve coverage"]

    def test_defaults(self):
        params = PRDEvolutionParams()
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
        prd = IntentPRDGenerator.generate(
            intent, config=cfg, anchor_project_path=str(tmp_path)
        )
        expected = (tmp_path / "products" / "acme-pay").resolve()
        assert Path(prd.project.path).resolve() == expected
        assert expected.is_dir()
        assert prd.project.name == "acme-pay"

    def test_self_evolution_uses_framework_root(self, tmp_path):
        intent = ParsedIntent(
            action=ActionType.BUILD,
            description="优化 sprintcycle 自身代码",
        )
        prd = IntentPRDGenerator.generate(
            intent, config=RuntimeConfig(), anchor_project_path=str(tmp_path)
        )
        assert prd.project.name == "sprintcycle"
        assert Path(prd.project.path).resolve() == IntentPRDGenerator._get_sprintcycle_root().resolve()

    def test_evolve_without_product_raises(self, tmp_path):
        intent = ParsedIntent(
            action=ActionType.EVOLVE,
            description="generic optimize wording without product slug",
        )
        with pytest.raises(ValueError, match="product"):
            IntentPRDGenerator.generate(
                intent,
                config=RuntimeConfig(),
                anchor_project_path=str(tmp_path),
            )
