#!/usr/bin/env bash
# Fast import / architecture smoke before full pytest
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"

if [[ ! -x "${PY}" ]]; then
  echo "Missing .venv — run: python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 2
fi

echo "[import-smoke] lint-imports"
"${ROOT}/.venv/bin/lint-imports"

echo "[import-smoke] pytest tests/test_architecture_imports.py"
"${PY}" -m pytest tests/test_architecture_imports.py -q --tb=short

echo "[import-smoke] pytest --collect-only (import surface)"
if ! "${PY}" -m pytest tests/ --collect-only -q 2>&1; then
  echo "[import-smoke] collect-only failed — fix imports before full pytest" >&2
  exit 1
fi

echo "[import-smoke] OK"
