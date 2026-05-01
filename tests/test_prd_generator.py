"""
Tests for PRD Generator module.

Coverage targets:
- sprintcycle/prd/generator.py
"""

import pytest
from sprintcycle.prd.generator import (
    IntentPRDGenerator,
    PRDEvolutionParams,
    ActionType,
    ExecutionMode,
)
from sprintcycle.prd.models import PRD


class TestIntentPRDGenerator:
    """IntentPRDGenerator tests"""

    def test_basic_creation(self):
        gen = IntentPRDGenerator()
        assert gen is not None

    def test_generate_from_parsed_intent(self):
        from sprintcycle.intent.parser import ParsedIntent, ActionType
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
