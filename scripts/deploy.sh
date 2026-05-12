#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
MODE="${1:-}"
ACTION="${2:-up}"

usage() {
  cat <<'EOF'
Usage:
  scripts/deploy.sh <local|prod> [up|down|restart|build|logs|status|doctor]

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

compose() {
  local file
  file="$(compose_file)"
  [[ -n "$file" ]] || { usage; exit 1; }
  docker compose -f "$file" --env-file "$ENV_FILE"
}

doctor() {
  echo "== Docker =="
  docker --version || true
  docker compose version || true
  echo

  echo "== Env file =="
  if [[ -f "$ENV_FILE" ]]; then
    echo "OK: $ENV_FILE exists"
  else
    echo "Missing env file: $ENV_FILE" >&2
    exit 1
  fi
  echo

  echo "== Permissions =="
  if docker info >/dev/null 2>&1; then
    echo "OK: Docker daemon reachable"
  else
    echo "ERROR: Docker daemon not reachable. Start Docker Desktop or fix /var/run/docker.sock permissions." >&2
    exit 1
  fi
  echo

  echo "== Compose file =="
  compose config >/dev/null
  echo "OK: compose config validated"
}

main() {
  [[ -n "$MODE" ]] || { usage; exit 1; }
  [[ "$MODE" == "local" || "$MODE" == "prod" ]] || { usage; exit 1; }

  require_docker

  case "$ACTION" in
    doctor)
      doctor
      ;;
    up)
      compose up -d --build
      ;;
    down)
      compose down
      ;;
    restart)
      compose restart
      ;;
    build)
      compose build
      ;;
    logs)
      compose logs -f
      ;;
    status)
      compose ps
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
