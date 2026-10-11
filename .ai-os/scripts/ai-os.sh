#!/usr/bin/env bash
# Shared launcher; keep stdin intact for hook JSON.
set -euo pipefail
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
for runtime in python3 python; do
    if command -v "$runtime" >/dev/null 2>&1 && "$runtime" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
        exec "$runtime" -B "$PROJECT_DIR/.ai-os/scripts/ai_os.py" --project "$PROJECT_DIR" "$@"
    fi
done
echo 'AI-OS requires Python 3.10+ on PATH; no weaker hook fallback is available.' >&2
exit 2
