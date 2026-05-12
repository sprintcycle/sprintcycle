#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
MODE="${1:-}"
ACTION="${2:-up}"

usage() {
  cat <<'EOF'
Usage:
  scripts/deploy.sh <local|prod> [up|down|restart|build|logs|status]

Environment variables:
  ENV_FILE   Path to env file (default: ./ .env)
EOF
}

require_docker() {
  command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 1; }
  docker compose version >/dev/null 2>&1 || { echo "docker compose is required" >&2; exit 1; }
}

compose_file() {
  case "$MODE" in
    local) echo "$ROOT/docker-compose.local.yml" ;;
    prod) echo "$ROOT/docker-compose.prod.yml" ;;
    *) echo "" ;;
  esac
}

compose_cmd() {
  local file
  file="$(compose_file)"
  [[ -n "$file" ]] || { usage; exit 1; }
  printf '%s\n' docker compose -f "$file" --env-file "$ENV_FILE"
}

main() {
  [[ -n "$MODE" ]] || { usage; exit 1; }
  [[ "$MODE" == "local" || "$MODE" == "prod" ]] || { usage; exit 1; }

  require_docker

  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing env file: $ENV_FILE" >&2
    exit 1
  fi

  # shellcheck disable=SC2207
  local cmd=( $(compose_cmd) )

  case "$ACTION" in
    up)
      "${cmd[@]}" up -d --build
      ;;
    down)
      "${cmd[@]}" down
      ;;
    restart)
      "${cmd[@]}" restart
      ;;
    build)
      "${cmd[@]}" build
      ;;
    logs)
      "${cmd[@]}" logs -f
      ;;
    status)
      "${cmd[@]}" ps
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
