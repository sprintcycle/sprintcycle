from .rule import Rule
from .rule_set import RuleSet


def default_production_rules() -> RuleSet:
    rules = [
        Rule(id="prod:zero_errors", name="zero errors", category="production", severity="error", applies_to=["production"]),
        Rule(id="prod:strict_types", name="strict type safety", category="production", severity="error", applies_to=["production"]),
    ]
    return RuleSet(name="production", rules=rules)
