# Golden 与模型切换回归（治理配套约定）

本文说明如何用 **pytest marker** 与 **`sprintcycle governance model-compare`** 做低成本「模型 / 环境切换」回归。

## 1. 推荐 marker

在需要纳入「模型对比必跑」的用例上增加 marker（需在 `pyproject.toml` 的 `[tool.pytest.ini_options]` 中注册 `markers`）：

```ini
[tool.pytest.ini_options]
markers = [
    "golden: 模型或环境切换时必须保持通过的用例",
]
```

```python
import pytest

@pytest.mark.golden
def test_core_api_contract():
    ...
```

日常 CI 可跑全量 `pytest`；模型发布流水线只跑 `pytest -m golden`。

## 2. `model-compare` 行为

命令：`sprintcycle governance model-compare [--quick] [--env1 KEY=VAL ...] [--env2 KEY=VAL ...] [--output path] [pytest 参数...]`

- 未写 `pytest` 参数时，默认 `tests/ -q --tb=no`；加 **`--quick`** 时默认 `tests/ -q --tb=no -m golden`（大仓库模型对比推荐）。
- 仍可直接在命令末尾写自定义 `pytest` 参数（此时 **`--quick` 不生效**）。
- 两遍均加 `--junitxml` 到临时文件，解析失败用例 **集合** 与 **退出码**；不一致则进程退出码为 `1`。
- 报告 JSON 默认写入 `<项目>/.sprintcycle/model_compare_last.json`（或由 `governance.report_dir` 决定根下的子目录）。

示例：

```bash
# 对比不同模型名（仅影响读环境变量的测试代码）
sprintcycle governance model-compare \
  --env1 LLM_MODEL=model-a \
  --env2 LLM_MODEL=model-b \
  -m golden -q
```

（注意：`pytest_args` 需跟在子命令之后；根级仍用 `-p` 指定项目路径。）

## 3. 与 `measurement` 的衔接（F-3）

Sprint 结束后的测量若已记录 `llm_model` / 相关字段，可将同次 `model-compare` 报告路径写入发布说明或 CI 制品，便于追溯「哪次模型升级引入了哪些用例差异」。
