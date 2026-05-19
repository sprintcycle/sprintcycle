# Quickstart: API layering refactor verification

## Prerequisites

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

## Smoke (full façade)

Requires a working import chain for `sprintcycle.api`. If import fails, use the targeted service tests below.

```bash
.venv/bin/python -c "
from sprintcycle.api import SprintCycle
sc = SprintCycle(project_path='.')
assert sc.platform_spec()['success']
r = sc.normalize_lifecycle_request(execution_id='e1', task_id='t1')
assert 'request' in r and 'contract' in r
w = sc.orchestrate_web_request(execution_id='e1', task_id='t1', execute=False)
assert w['success'] and 'plan' in w['data']
print('smoke ok')
"
```

## Targeted tests (refactor services)

Validates extracted orchestration without full platform import chain:

```bash
.venv/bin/python -m pytest tests/test_api_layering_services.py -q
```

## Lifecycle integration (when import chain is healthy)

```bash
.venv/bin/python -m pytest tests/test_lifecycle_end_to_end.py -q
.venv/bin/python -m pytest tests/test_persistence_and_knowledge.py::test_api_knowledge_search -q
```

## Manual checks

1. `normalize_lifecycle_request` → `request` + `contract` with `validation_refs.normalized`.
2. `orchestrate_web_request(..., execute=False)` → `plan`, `prepare`, `decompose`, `lifecycle_contract`.
3. `lifecycle_contract(execution_id)` → `data.final_snapshot` when execution detail exists.

## Review artifacts

- `data-model.md` — method ownership map
- `contracts/facade-boundary.md`, `contracts/service-boundaries.md`
- `review-phase4.md` — T018 findings and import fixes
