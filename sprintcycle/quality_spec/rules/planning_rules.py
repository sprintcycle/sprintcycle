from .rule import Rule
from .rule_set import RuleSet


def default_planning_rules() -> RuleSet:
    rules = [
        Rule(id="planning:spec_refs", name="spec refs required", category="planning", applies_to=["planning"]),
        Rule(id="planning:acceptance_refs", name="acceptance refs required", category="planning", applies_to=["planning"]),
        Rule(id="planning:rollback_plan", name="rollback plan required", category="planning", applies_to=["planning"]),
    ]
    return RuleSet(name="planning", rules=rules)
