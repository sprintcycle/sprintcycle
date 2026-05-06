"""稳定 prompt 模板摘要（与 Coder/Analyzer 共用模板）。"""

from sprintcycle.prompt_sources import (
    compute_prompt_sources_fingerprint,
    format_analyzer_bug_llm_prompt,
    format_coder_generation_prompt,
    stable_prompt_registry,
)


def test_format_coder_generation_prompt_matches_arch_optional():
    s = format_coder_generation_prompt("python", "fix bug", None)
    assert "fix bug" in s
    assert "python" in s
    # 静态「要求」条目中可出现「架构设计」字样；仅当传入架构正文时才插入架构块标题行
    assert "架构设计指导：\n" not in s
    s2 = format_coder_generation_prompt("python", "x", "layered")
    assert "架构设计指导：\n" in s2
    assert "layered" in s2


def test_format_analyzer_includes_json_skeleton():
    p = format_analyzer_bug_llm_prompt("err", "ctx")
    assert "错误日志" in p
    assert "err" in p
    assert "ctx" in p
    assert '"error_type"' in p


def test_compute_prompt_sources_fingerprint_stable():
    fp = compute_prompt_sources_fingerprint()
    assert fp["prompt_sources_schema"] == 1
    assert len(fp["prompt_sources_aggregate_sha256"]) == 64
    dig = fp["prompt_source_digests"]
    assert len(dig) == len(stable_prompt_registry())
    for sid, h in dig.items():
        assert len(h) == 64
        assert sid.startswith("execution.agents.")
