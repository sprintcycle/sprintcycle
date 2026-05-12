#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git config core.hooksPath "$ROOT/.githooks"
echo "Git hooks installed: $(git config core.hooksPath)"
