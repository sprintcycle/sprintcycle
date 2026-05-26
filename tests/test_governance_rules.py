"""治理检查测试 - 覆盖governance rules执行和违规拦截"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.governance.quality_spec.rules.rule import Rule
from sprintcycle.domain.core.governance.quality_spec.rules.rule_set import RuleSet
from sprintcycle.domain.core.governance.quality_spec.rules.rule_registry import RuleRegistry
from sprintcycle.domain.core.governance.core.runner import GovernanceRunner


class TestRule:
    """测试单个规则的基本功能"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = Rule(
            id="rule-001",
            name="Test Rule",
            category="security",
            severity="error",
            enabled=True,
            thresholds={"min_score": 70},
            applies_to=["review", "planning"],
        )

        assert rule.id == "rule-001"
        assert rule.name == "Test Rule"
        assert rule.category == "security"
        assert rule.severity == "error"
        assert rule.enabled is True
        assert rule.thresholds == {"min_score": 70}
        assert rule.applies_to == ["review", "planning"]

    def test_rule_to_dict(self):
        """测试规则转换为字典"""
        rule = Rule(
            id="rule-001",
            name="Test Rule",
            category="security",
            severity="warning",
            enabled=False,
            thresholds={"max_errors": 5},
            applies_to=["review"],
            metadata={"author": "test"},
        )

        result = rule.to_dict()

        assert result["id"] == "rule-001"
        assert result["name"] == "Test Rule"
        assert result["category"] == "security"
        assert result["severity"] == "warning"
        assert result["enabled"] is False
        assert result["thresholds"] == {"max_errors": 5}
        assert result["applies_to"] == ["review"]
        assert result["metadata"] == {"author": "test"}

    def test_rule_from_dict(self):
        """测试从字典创建规则"""
        data = {
            "id": "rule-002",
            "name": "Another Rule",
            "category": "quality",
            "severity": "info",
            "enabled": True,
            "thresholds": {"coverage": 80},
            "applies_to": ["planning", "review"],
            "metadata": {"version": "1.0"},
        }

        rule = Rule.from_dict(data)

        assert rule.id == "rule-002"
        assert rule.name == "Another Rule"
        assert rule.category == "quality"
        assert rule.severity == "info"
        assert rule.enabled is True
        assert rule.thresholds == {"coverage": 80}
        assert rule.applies_to == ["planning", "review"]
        assert rule.metadata == {"version": "1.0"}

    def test_rule_applies_to_gate(self):
        """测试规则是否适用于特定gate"""
        rule_all = Rule(id="r1", name="All", category="test", applies_to=[])
        rule_review = Rule(id="r2", name="Review", category="test", applies_to=["review"])
        rule_planning = Rule(id="r3", name="Planning", category="test", applies_to=["planning"])
        rule_both = Rule(id="r4", name="Both", category="test", applies_to=["review", "planning"])

        assert rule_all.applies_to_gate("review") is True
        assert rule_all.applies_to_gate("planning") is True
        assert rule_all.applies_to_gate("production") is True

        assert rule_review.applies_to_gate("review") is True
        assert rule_review.applies_to_gate("planning") is False
        assert rule_review.applies_to_gate("production") is False

        assert rule_planning.applies_to_gate("review") is False
        assert rule_planning.applies_to_gate("planning") is True
        assert rule_planning.applies_to_gate("production") is False

        assert rule_both.applies_to_gate("review") is True
        assert rule_both.applies_to_gate("planning") is True
        assert rule_both.applies_to_gate("production") is False

    def test_rule_validate_thresholds(self):
        """测试阈值验证"""
        rule = Rule(id="r1", name="Test", category="test")
        rule.thresholds = {"key": "value"}
        rule.validate_thresholds()

        rule.thresholds = None
        with pytest.raises(ValueError, match="thresholds must be a dict"):
            rule.validate_thresholds()


class TestRuleSet:
    """测试规则集合"""

    def test_rule_set_creation(self):
        """测试规则集创建"""
        rules = [
            Rule(id="r1", name="Rule 1", category="test"),
            Rule(id="r2", name="Rule 2", category="test"),
        ]
        rule_set = RuleSet(name="test-set", rules=rules, metadata={"version": "1.0"})

        assert rule_set.name == "test-set"
        assert len(rule_set.rules) == 2
        assert rule_set.metadata == {"version": "1.0"}

    def test_rule_set_add_rule(self):
        """测试添加规则"""
        rule_set = RuleSet(name="test-set")
        rule = Rule(id="r1", name="Rule 1", category="test")

        rule_set.add_rule(rule)

        assert len(rule_set.rules) == 1
        assert rule_set.rules[0].id == "r1"

    def test_rule_set_extend_rules(self):
        """测试批量添加规则"""
        rule_set = RuleSet(name="test-set")
        rules = [
            Rule(id="r1", name="Rule 1", category="test"),
            Rule(id="r2", name="Rule 2", category="test"),
        ]

        rule_set.extend_rules(rules)

        assert len(rule_set.rules) == 2

    def test_rule_set_filter_enabled(self):
        """测试过滤启用的规则"""
        rules = [
            Rule(id="r1", name="Rule 1", category="test", enabled=True),
            Rule(id="r2", name="Rule 2", category="test", enabled=False),
            Rule(id="r3", name="Rule 3", category="test", enabled=True),
        ]
        rule_set = RuleSet(name="test-set", rules=rules)

        filtered = rule_set.filter_enabled()

        assert len(filtered.rules) == 2
        assert {r.id for r in filtered.rules} == {"r1", "r3"}

    def test_rule_set_for_gate(self):
        """测试获取特定gate的规则"""
        rules = [
            Rule(id="r1", name="Review Rule", category="test", applies_to=["review"]),
            Rule(id="r2", name="Planning Rule", category="test", applies_to=["planning"]),
            Rule(id="r3", name="Both Rule", category="test", applies_to=["review", "planning"]),
            Rule(id="r4", name="All Rule", category="test", applies_to=[]),
        ]
        rule_set = RuleSet(name="test-set", rules=rules)

        review_rules = rule_set.for_gate("review")

        assert review_rules.name == "test-set:review"
        assert len(review_rules.rules) == 3
        assert {r.id for r in review_rules.rules} == {"r1", "r3", "r4"}


class TestRuleRegistry:
    """测试规则注册中心"""

    def test_registry_register(self):
        """测试注册规则"""
        registry = RuleRegistry()
        rule = Rule(id="r1", name="Rule 1", category="test")

        registry.register(rule)

        assert registry.get("r1") == rule

    def test_registry_register_many(self):
        """测试批量注册规则"""
        registry = RuleRegistry()
        rules = [
            Rule(id="r1", name="Rule 1", category="test"),
            Rule(id="r2", name="Rule 2", category="test"),
        ]

        registry.register_many(rules)

        assert len(registry.list()) == 2
        assert registry.get("r1") is not None
        assert registry.get("r2") is not None

    def test_registry_get_nonexistent(self):
        """测试获取不存在的规则"""
        registry = RuleRegistry()

        result = registry.get("nonexistent")

        assert result is None

    def test_registry_for_gate(self):
        """测试获取特定gate的规则"""
        registry = RuleRegistry()
        registry.register_many([
            Rule(id="r1", name="Review", category="test", applies_to=["review"]),
            Rule(id="r2", name="Planning", category="test", applies_to=["planning"]),
            Rule(id="r3", name="Both", category="test", applies_to=["review", "planning"]),
        ])

        review_rules = registry.for_gate("review")

        assert len(review_rules) == 2
        assert {r.id for r in review_rules} == {"r1", "r3"}

    def test_registry_clear(self):
        """测试清空注册表"""
        registry = RuleRegistry()
        registry.register(Rule(id="r1", name="Rule 1", category="test"))

        registry.clear()

        assert len(registry.list()) == 0


class TestGovernanceRunner:
    """测试治理检查执行器"""

    def test_runner_initialization(self):
        """测试执行器初始化"""
        config = {"governance": {"enabled": True}}
        runner = GovernanceRunner(config)

        assert runner is not None

    def test_runner_with_empty_config(self):
        """测试空配置"""
        runner = GovernanceRunner({})

        assert runner is not None
