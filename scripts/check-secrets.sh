#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PATTERN='(DEEPSEEK_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|API_KEY|SECRET|TOKEN)'

if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!.venv' --glob '!dist' --glob '!build' -e "$PATTERN" "$ROOT" || true
else
  echo "rg is required for secret scanning" >&2
  exit 1
fi
