#!/usr/bin/env bash
# Continue ci-fix-loop when session flag is set and CI has not passed yet.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ACTIVE="${ROOT}/.cursor/.ci-fix-loop-active"
EXIT_FILE="${ROOT}/.cursor/.ci-local-last-exit"
LOOP_FILE="${ROOT}/.cursor/.ci-fix-loop-iterations"
MAX_ITERATIONS="${CI_FIX_LOOP_MAX:-12}"

# Consume stdin (stop hook payload)
cat >/dev/null || true

if [[ ! -f "${ACTIVE}" ]]; then
  exit 0
fi

iter=0
if [[ -f "${LOOP_FILE}" ]]; then
  iter="$(cat "${LOOP_FILE}" 2>/dev/null || echo 0)"
fi
iter=$((iter + 1))
mkdir -p "${ROOT}/.cursor"
echo "${iter}" > "${LOOP_FILE}"

if [[ "${iter}" -gt "${MAX_ITERATIONS}" ]]; then
  rm -f "${ACTIVE}" "${LOOP_FILE}"
  echo '{"followup_message": "ci-fix-loop 已达最大轮次 '"${MAX_ITERATIONS}"'。请停止自动续跑，汇总 blocker 并等待人工决策。"}'
  exit 0
fi

if [[ -f "${EXIT_FILE}" ]] && [[ "$(cat "${EXIT_FILE}")" == "0" ]]; then
  rm -f "${ACTIVE}" "${LOOP_FILE}"
  exit 0
fi

MSG='CI 仍未通过（iteration '"${iter}"'/'"${MAX_ITERATIONS}"'）。请继续 /ci-fix-loop：\
1) 运行 `bash scripts/import-smoke.sh` 或 `make ci-smoke`（import 阶段）\
2) import 失败时**优先假设为目录/文件路径迁移**：用 git 历史定位新路径，更新 import 指向最终模块，禁止 shim/重导出\
3) 每轮只修一个失败簇，修完重跑相关阶段\
4) 运行 `make ci-local-quick` 或 `make ci-local` 并确认 `.cursor/.ci-local-last-exit` 为 0\
5) 连续 3 轮相同 blocker → 停止并报告'

python3 -c 'import json,sys; print(json.dumps({"followup_message": sys.argv[1]}))' "${MSG}"
