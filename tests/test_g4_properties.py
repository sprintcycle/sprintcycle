"""
G4 补充：pytest + Hypothesis 属性测试（V4.0 §6.4）。

与 ``test_architecture_imports``（import-linter）互补；不替代 CI 中的契约检查。
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from sprintcycle.infrastructure.adapters.generic.config import flatten_sprintcycle_toml
from sprintcycle.infrastructure.adapters.generic.config.quality import (
    QUALITY_LEVELS,
    QUALITY_PROFILES,
    normalize_quality_level,
    normalize_quality_profile,
    resolve_effective_quality_level,
)
from sprintcycle.domain.generic.models.release_plan.parser import ReleasePlanParser


@settings(max_examples=50)
@given(st.text())
def test_normalize_quality_level_always_in_ladder(raw: str) -> None:
    out = normalize_quality_level(raw)
    assert out in QUALITY_LEVELS


@settings(max_examples=40)
@given(st.text())
def test_normalize_quality_profile_always_known(raw: str) -> None:
    out = normalize_quality_profile(raw)
    assert out in QUALITY_PROFILES


@settings(max_examples=80)
@given(st.text())
def test_resolve_default_tracks_normalize_level(level: str) -> None:
    assert resolve_effective_quality_level("default", level) == normalize_quality_level(level)


@settings(max_examples=20)
@given(st.text())
def test_resolve_off_always_l0(_level: str) -> None:
    assert resolve_effective_quality_level("off", _level) == "L0"


@settings(max_examples=20)
@given(st.text())
def test_resolve_fast_always_l1(_level: str) -> None:
    assert resolve_effective_quality_level("fast", _level) == "L1"


@settings(max_examples=20)
@given(st.text())
def test_resolve_strict_always_l3(_level: str) -> None:
    assert resolve_effective_quality_level("strict", _level) == "L3"


_minimal_plan_dict = st.fixed_dictionaries(
    {
        "project": st.fixed_dictionaries(
            {
                "name": st.text(
                    alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="\\"),
                    min_size=1,
                    max_size=80,
                ),
                "path": st.text(
                    alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="\\"),
                    min_size=1,
                    max_size=120,
                ),
            }
        ),
        "mode": st.just("normal"),
        "sprints": st.lists(
            st.fixed_dictionaries(
                {
                    "name": st.text(
                        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="\\"),
                        min_size=1,
                        max_size=40,
                    ),
                    "tasks": st.lists(
                        st.fixed_dictionaries(
                            {
                                "description": st.text(
                                    alphabet=st.characters(
                                        min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="\\"
                                    ),
                                    min_size=12,
                                    max_size=400,
                                ),
                                "agent": st.sampled_from(["coder", "tester", "architect"]),
                            }
                        ),
                        min_size=1,
                        max_size=4,
                    ),
                }
            ),
            min_size=1,
            max_size=3,
        ),
    }
)


@settings(max_examples=25, deadline=None)
@given(_minimal_plan_dict)
def test_release_plan_parse_dict_roundtrip_invariants(data: dict) -> None:
    parser = ReleasePlanParser()
    plan = parser.parse_dict(data, source_path="<hypothesis>")
    assert plan.project.name == data["project"]["name"]
    assert plan.project.path == data["project"]["path"]
    assert len(plan.sprints) == len(data["sprints"])
    assert plan.total_tasks == sum(len(s["tasks"]) for s in data["sprints"])


@settings(max_examples=30)
@given(
    st.sampled_from(["L0", "L1", "L2", "L3"]),
    st.sampled_from(["default", "off", "fast", "strict"]),
    st.floats(min_value=0.0, max_value=100.0),
)
def test_flatten_quality_preserves_level_and_profile(level: str, profile: str, cov: float) -> None:
    nested = {"quality": {"level": level, "profile": profile, "min_coverage_percent": cov}}
    flat = flatten_sprintcycle_toml(nested)
    assert flat["quality_level"] == level
    assert flat["quality_profile"] == profile
    assert flat["min_coverage_percent"] == cov
