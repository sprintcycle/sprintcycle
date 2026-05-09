from .rule import Rule
from .rule_set import RuleSet


def default_review_rules() -> RuleSet:
    rules = [
        Rule(id="review:deal", name="contract checks", category="review", applies_to=["review"]),
        Rule(id="review:bandit", name="security checks", category="review", applies_to=["review"]),
        Rule(id="review:arch", name="architecture checks", category="review", applies_to=["review"]),
    ]
    return RuleSet(name="review", rules=rules)
