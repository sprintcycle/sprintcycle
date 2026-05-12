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

compose_cmd() {
  local file
  file="$(compose_file)"
  [[ -n "$file" ]] || { usage; exit 1; }
  docker compose -f "$file" --env-file "$ENV_FILE" "$@"
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
    if [[ "$OSTYPE" == darwin* ]]; then
      echo "Hint (macOS): open Docker Desktop and wait until it reports 'Docker is running'." >&2
      echo "Hint (macOS): if it is already running, try restarting Docker Desktop or your terminal." >&2
      echo "Hint (macOS): if you're using Colima or Rancher Desktop, make sure the current Docker context is correct." >&2
    elif [[ "$OSTYPE" == linux* ]]; then
      echo "Hint (Linux): ensure the docker service is running and your user is in the docker group." >&2
      echo "  sudo systemctl start docker" >&2
      echo "  sudo usermod -aG docker \$USER" >&2
      echo "  newgrp docker" >&2
    fi
    if [[ -S /var/run/docker.sock ]]; then
      echo "docker.sock exists at /var/run/docker.sock" >&2
    else
      echo "docker.sock not found at /var/run/docker.sock" >&2
    fi
    exit 1
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

  case "$ACTION" in
    doctor)
      doctor
      ;;
    up)
      compose_cmd up -d --build
      ;;
    down)
      compose_cmd down
      ;;
    restart)
      compose_cmd restart
      ;;
    build)
      compose_cmd build
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
