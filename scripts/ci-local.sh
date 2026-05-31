#!/usr/bin/env bash
# Local CI mirror — matches .github/workflows/ci.yml
# Usage:
#   bash scripts/ci-local.sh              # full pipeline
#   CI_LOCAL_SKIP_E2E=1 bash scripts/ci-local.sh
#   CI_LOCAL_PHASE=arch|ruff|pytest|frontend|e2e bash scripts/ci-local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PHASE="${CI_LOCAL_PHASE:-all}"
SKIP_E2E="${CI_LOCAL_SKIP_E2E:-0}"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[ci-local]${NC} $*"; }
ok()  { echo -e "${GREEN}[ci-local] OK${NC} $*"; }
fail() {
  local code="${1:-1}"
  shift || true
  echo -e "${RED}[ci-local] FAIL${NC} $*" >&2
  record_exit "${code}"
  exit "${code}"
}

record_exit() {
  mkdir -p "${ROOT}/.cursor"
  echo "$1" > "${ROOT}/.cursor/.ci-local-last-exit"
}

require_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "Missing uv — install: https://docs.astral.sh/uv/getting-started/installation" >&2
    fail 2
  fi
}

require_dev_setup_marker() {
  if [[ ! -f "${ROOT}/docs-dev/dev-setup.sh" ]]; then
    fail 2 "docs-dev/dev-setup.sh missing (CI gate)"
  fi
}

run_arch_gate() {
  log "architecture-gate: lint-imports"
  if ! uv run lint-imports 2>&1; then
    fail 1 "lint-imports"
  fi
  ok "lint-imports"
}

run_ruff() {
  log "ruff check sprintcycle tests"
  if ! uv run ruff check sprintcycle tests 2>&1; then
    fail 1 "ruff"
  fi
  ok "ruff"
}

run_pytest() {
  log "pytest tests/"
  if ! uv run pytest tests/ -q --tb=short 2>&1; then
    fail 1 "pytest"
  fi
  ok "pytest"
}

run_frontend() {
  log "frontend: npm ci, openapi:sync, build, lint"
  require_dev_setup_marker
  (
    cd "${ROOT}/frontend"
    npm ci
    npm run openapi:sync
    npm run build
    npm run lint
  ) || fail 1 "frontend"
  ok "frontend"
}

run_e2e() {
  if [[ "${SKIP_E2E}" == "1" ]]; then
    log "skipping Playwright (CI_LOCAL_SKIP_E2E=1)"
    return 0
  fi
  log "playwright (dashboard smoke)"
  (
    cd "${ROOT}/frontend"
    npx playwright install --with-deps chromium
    npx playwright test
  ) || fail 1 "playwright"
  ok "playwright"
}

ensure_deps() {
  require_uv
  log "ensure uv sync --extra dev --extra dashboard"
  uv sync --extra dev --extra dashboard
}

main() {
  LOG_FILE="${ROOT}/.cursor/ci-local-last.log"
  mkdir -p "${ROOT}/.cursor"
  : > "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1

  ensure_deps

  case "${PHASE}" in
    all)
      run_arch_gate
      run_ruff
      run_pytest
      run_frontend
      run_e2e
      ;;
    arch) run_arch_gate ;;
    ruff) run_ruff ;;
    pytest) run_pytest ;;
    frontend) run_frontend ;;
    e2e)
      run_frontend
      run_e2e
      ;;
    *)
      echo "Unknown CI_LOCAL_PHASE=${PHASE} (use: all|arch|ruff|pytest|frontend|e2e)" >&2
      fail 2
      ;;
  esac

  record_exit 0
  ok "ci-local complete (log: .cursor/ci-local-last.log)"
}

main "$@"
