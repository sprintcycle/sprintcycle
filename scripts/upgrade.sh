#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-prod}"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"

if [[ "$MODE" != "local" && "$MODE" != "prod" ]]; then
  echo "Usage: scripts/upgrade.sh [local|prod]" >&2
  exit 1
fi

bash "$ROOT/scripts/deploy.sh" "$MODE" build
bash "$ROOT/scripts/deploy.sh" "$MODE" up
