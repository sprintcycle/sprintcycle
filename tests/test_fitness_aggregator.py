from sprintcycle.domain.fitness import FitnessAggregator, FitnessEvaluator
from sprintcycle.domain.interfaces import EvaluatorAgentProtocol


class MockEvaluatorAgent(EvaluatorAgentProtocol):
    """测试用的 Mock 评估器代理"""
    
    def evaluate(self, payload):
        return {
            "success": True,
            "data": {
                "verdict": "pending",
                "reason": "test agent",
            }
        }


def test_aggregator_supports_weight_reason_metadata():
    aggregator = FitnessAggregator()
    result = aggregator.aggregate(
        [
            {
                "name": "ruff",
                "score": 90,
                "weight": 0.5,
                "reason": "lint is clean",
                "metadata": {
                    "core": {"source": "ruff", "files": 12},
                    "extra": {"rules": ["E", "F"]},
                },
            },
            {
                "name": "coverage",
                "score": 70,
                "weight": 0.5,
                "reason": "coverage is acceptable",
                "metadata": {"source": "coverage", "branch": "main"},
            },
        ]
    )

    data = result["data"]
    assert data["total_score"] == 80.0
    assert data["summary"]["status"] == "healthy"
    assert len(data["dimensions"]) == 2
    assert data["dimensions"][0]["metadata"]["core"]["source"] == "ruff"
    assert data["dimensions"][0]["metadata"]["extra"]["rules"] == ["E", "F"]
    assert data["dimensions"][1]["metadata"]["core"] == {}
    assert data["dimensions"][1]["metadata"]["extra"]["source"] == "coverage"
    assert data["weighted_contributions"][0]["reason"] == "lint is clean"


def test_evaluator_uses_dimensions_when_present():
    evaluator = FitnessEvaluator(evaluator_agent=MockEvaluatorAgent())
    result = evaluator.evaluate(
        {
            "dimensions": [
                {"name": "ruff", "score": 100, "weight": 1, "reason": "ok"},
                {"name": "bandit", "score": 0, "weight": 0, "reason": "ignored"},
            ],
            "contract": {},
        }
    )

    data = result["data"]
    assert data["total_score"] == 100.0
    assert data["summary"]["dimension_count"] == 2


def test_evaluator_derives_dimensions_from_legacy_payload():
    evaluator = FitnessEvaluator(evaluator_agent=MockEvaluatorAgent())
    result = evaluator.evaluate(
        {
            "events": [{"type": "task_complete"}, {"type": "task_failed"}],
            "suggestions": [{"status": "promoted"}],
            "executions": [{"status": "succeeded"}],
            "runtimes": [{"status": "running"}],
            "contract": {},
        }
    )

    data = result["data"]
    assert "verdict" in data
    assert "reason" in data
