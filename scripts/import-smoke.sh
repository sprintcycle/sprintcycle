#!/usr/bin/env bash
# Fast import / architecture smoke before full pytest
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "Missing uv — install: https://docs.astral.sh/uv/getting-started/installation" >&2
  exit 2
fi

echo "[import-smoke] lint-imports"
uv run lint-imports

echo "[import-smoke] pytest tests/test_architecture_imports.py"
uv run pytest tests/test_architecture_imports.py -q --tb=short

echo "[import-smoke] pytest --collect-only (import surface)"
if ! uv run pytest tests/ --collect-only -q 2>&1; then
  echo "[import-smoke] collect-only failed — fix imports before full pytest" >&2
  exit 1
fi

echo "[import-smoke] OK"
