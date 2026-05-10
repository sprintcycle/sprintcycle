#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-up}"
project_name="${SPRINTCYCLE_PROJECT_NAME:-sprintcycle}"
compose_file="${SPRINTCYCLE_COMPOSE_FILE:-docker-compose.yml}"

case "$cmd" in
  build)
    docker compose -f "$compose_file" -p "$project_name" build
    ;;
  up)
    docker compose -f "$compose_file" -p "$project_name" up -d --build
    ;;
  down)
    docker compose -f "$compose_file" -p "$project_name" down
    ;;
  restart)
    docker compose -f "$compose_file" -p "$project_name" restart
    ;;
  logs)
    docker compose -f "$compose_file" -p "$project_name" logs -f
    ;;
  status)
    docker compose -f "$compose_file" -p "$project_name" ps
    ;;
  *)
    echo "Usage: $0 {build|up|down|restart|logs|status}"
    exit 1
    ;;
esac
