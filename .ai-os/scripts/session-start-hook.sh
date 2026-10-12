#!/usr/bin/env bash
# Claude Code boot-state injection hook for the AI OS Framework (MaiKS).
#
# Injects the verbatim content of BOOT.md and rules/ultimate_rules.md directly
# into context via hookSpecificOutput.additionalContext, instead of just telling
# the agent to go re-read them. A printed reminder still depends on the agent
# choosing to act on it afterward; this makes boot state present unconditionally,
# the moment the hook fires.
#
# Usage: session-start-hook.sh [HOOK_EVENT_NAME]   (default: SessionStart)
#
# Serves two events (EP-60). SessionStart covers startup/clear/compact for the
# main thread. SubagentStart covers dispatched agents, which inherit none of the
# parent thread's context — they are separate hook events precisely because
# session context does not propagate, so a subagent without this runs ungoverned:
# no R1 pre-mutation security review, no R21 claim verification, no R13 logging,
# and its output arrives in the parent looking identical to governed work.
#
# Also injects the active branch's task file (EP-78) — BOOT.md §2 step 4 only
# loads it at a real boot; a mid-session `compact` event doesn't re-run the boot
# sequence at all, so without this the hook re-injects governance but silently
# drops accumulated working-context (findings, the Active plan: pointer) at
# exactly the moment the host's own compaction is most likely to paraphrase it
# away. Best-effort: no git repo / no task file yet →
# skip; ambiguous legacy files warn, but never fail the hook over task lookup.
#
# One script, not two: the escape/emit logic below is the only copy. A second
# script duplicating it would drift from this one, the two-copies-of-one-fact
# failure known_gotchas.md already records.
set -euo pipefail

HOOK_EVENT="${1:-SessionStart}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
BOOT_FILE="${PROJECT_DIR}/.ai-os/BOOT.md"
RULES_FILE="${PROJECT_DIR}/.ai-os/rules/ultimate_rules.md"

boot_content=$(cat "$BOOT_FILE" 2>&1 || echo "Error reading BOOT.md")
rules_content=$(cat "$RULES_FILE" 2>&1 || echo "Error reading ultimate_rules.md")

# Shared resolver keeps branch collisions and ambiguous legacy files out of context.
# Lookup is read-only and best-effort; errors must never suppress governance injection.
task_content=""
task_relative=""
python_command=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
        python_command="$candidate"
        break
    fi
done
if [ -n "$python_command" ]; then
    task_relative=$("$python_command" -X utf8 "${PROJECT_DIR}/.ai-os/scripts/task_identity.py" --root "$PROJECT_DIR" || true)
    if [ -n "$task_relative" ] && [ -f "${PROJECT_DIR}/${task_relative}" ]; then
        task_content=$(cat "${PROJECT_DIR}/${task_relative}" 2>/dev/null || true)
    fi
else
    printf '%s\n' 'AI-OS: Python 3.8+ unavailable; task injection skipped. Governance remains loaded.' >&2
fi

# Escape for JSON embedding via bash parameter substitution (single C-level
# pass per replacement, not a character-by-character loop).
escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

boot_escaped=$(escape_for_json "$boot_content")
rules_escaped=$(escape_for_json "$rules_content")

task_section=""
if [ -n "$task_content" ]; then
    task_escaped=$(escape_for_json "$task_content")
    task_section="\n\n--- ${task_relative} ---\n${task_escaped}"
fi

context="<AI_OS_BOOT_STATE>\nThis project is governed by the AI OS Framework (MaiKS). Below is the full, verbatim content of .ai-os/BOOT.md and .ai-os/rules/ultimate_rules.md, injected directly so boot state is present from the first message without depending on a manual re-read: on session start it survives /clear and compaction, and on subagent spawn it supplies governance the parent thread does not pass down. You are bound by these rules for the whole of this thread, dispatched work included. When present below, the active branch's task file is included too, so a mid-session compaction doesn't silently drop accumulated working-context.\n\n--- .ai-os/BOOT.md ---\n${boot_escaped}\n\n--- .ai-os/rules/ultimate_rules.md ---\n${rules_escaped}${task_section}\n</AI_OS_BOOT_STATE>"

# Pure JSON on stdout only - additionalContext is fed directly into the context
# of whichever thread the event fired for.
printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "%s",\n    "additionalContext": "%s"\n  }\n}\n' "$HOOK_EVENT" "$context"

exit 0
