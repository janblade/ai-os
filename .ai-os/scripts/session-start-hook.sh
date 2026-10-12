#!/usr/bin/env bash
# Preserve the installed entry point; share assembly and validation with the CLI.
set -euo pipefail
exec bash "$(dirname "$0")/ai-os.sh" hook "${1:-SessionStart}"
