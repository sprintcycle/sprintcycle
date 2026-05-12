#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
EXPECTED_DOCKER_CONTEXT="${DOCKER_CONTEXT:-${EXPECTED_DOCKER_CONTEXT:-desktop-linux}}"
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

compose_cmd() {
  local file
  file="$(compose_file)"
  [[ -n "$file" ]] || { usage; exit 1; }
  docker compose -f "$file" --env-file "$ENV_FILE" "$@"
}

check_context() {
  local current_context
  current_context="$(docker context show 2>/dev/null || true)"
  if [[ -n "$EXPECTED_DOCKER_CONTEXT" && -n "$current_context" && "$current_context" != "$EXPECTED_DOCKER_CONTEXT" ]]; then
    echo "WARN: expected docker context '$EXPECTED_DOCKER_CONTEXT' but current context is '$current_context'" >&2
    echo "Hint: docker context use $EXPECTED_DOCKER_CONTEXT" >&2
  fi
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

  echo "== Docker daemon =="
  if docker info >/dev/null 2>&1; then
    echo "OK: Docker daemon reachable"
  else
    echo "ERROR: Docker daemon not reachable." >&2
    current_context="$(docker context show 2>/dev/null || true)"
    if [[ -n "$current_context" ]]; then
      echo "Current docker context: $current_context" >&2
    fi
    echo "Expected docker context: $EXPECTED_DOCKER_CONTEXT" >&2
    echo "Available docker contexts:" >&2
    docker context ls >&2 || true
    echo "" >&2
    if [[ "$OSTYPE" == darwin* ]]; then
      echo "macOS checks:" >&2
      echo "  1. Open Docker Desktop" >&2
      echo "  2. Wait until it says Docker is running" >&2
      echo "  3. Retry: docker info" >&2
      echo "  4. If using Colima/Rancher Desktop, run: docker context ls" >&2
      echo "  5. Switch to the correct context, then retry" >&2
    elif [[ "$OSTYPE" == linux* ]]; then
      echo "Linux checks:" >&2
      echo "  1. sudo systemctl start docker" >&2
      echo "  2. sudo usermod -aG docker \$USER" >&2
      echo "  3. Log out and back in, or run: newgrp docker" >&2
      echo "  4. Retry: docker info" >&2
    fi
    if [[ -S /var/run/docker.sock ]]; then
      echo "docker.sock exists at /var/run/docker.sock" >&2
      ls -l /var/run/docker.sock >&2 || true
    else
      echo "docker.sock not found at /var/run/docker.sock" >&2
    fi
    echo "" >&2
    echo "If Docker Desktop is running but inaccessible, try restarting Docker Desktop and this terminal." >&2
    exit 1
  fi

  if [[ "$current_context" != "$EXPECTED_DOCKER_CONTEXT" ]]; then
    echo "NOTE: current context '$current_context' does not match expected '$EXPECTED_DOCKER_CONTEXT'." >&2
  fi
  echo

  echo "== Compose file =="
  compose_cmd config >/dev/null
  echo "OK: compose config validated"

  echo
  echo "== Ports =="
  if command -v lsof >/dev/null 2>&1; then
    for port in 3000 8000; do
      if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "WARN: port $port is already in use"
      else
        echo "OK: port $port is free"
      fi
    done
  fi
}

main() {
  [[ -n "$MODE" ]] || { usage; exit 1; }
  [[ "$MODE" == "local" || "$MODE" == "prod" ]] || { usage; exit 1; }

  require_docker
  check_context

  case "$ACTION" in
    doctor)
      doctor
      ;;
    up)
      compose_cmd up -d
      ;;
    down)
      compose_cmd down
      ;;
    restart)
      compose_cmd restart
      ;;
    build)
      compose_cmd build --pull
      ;;
    logs)
      compose_cmd logs -f
      ;;
    status)
      compose_cmd ps
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
