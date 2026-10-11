#!/usr/bin/env python3
"""Small, standard-library-only command entry point for AI-OS."""

import argparse
import json
import sys
from pathlib import Path

from context import build_pack, create_task, diff_packs, load_snapshot, render_pack, save_snapshot, task_path
from storage import canonical_json, workspace_path
from memory import add_entry, amend, promote, recover, verify
from hooks import hook
from installation import install_hooks


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path)
    commands = result.add_subparsers(dest="command", required=True)
    task = commands.add_parser("task", help="Resolve or create task memory without renaming legacy files")
    task.add_argument("--name", required=True)
    task.add_argument("--create", action="store_true")
    pack = commands.add_parser("pack", help="Assemble a reproducible context payload")
    pack.add_argument("--task")
    pack.add_argument("--skill", action="append", default=[])
    pack.add_argument("--file", action="append", default=[])
    pack.add_argument("--snapshot", action="store_true")
    pack.add_argument("--render", action="store_true")
    replay = commands.add_parser("replay", help="Render a stored payload without reading current sources")
    replay.add_argument("snapshot")
    diff = commands.add_parser("diff", help="Inspect changes between context snapshots")
    diff.add_argument("before")
    diff.add_argument("after")
    evidence = commands.add_parser("verify", help="Record a check against explicit dependency files")
    evidence.add_argument("--file", action="append", required=True)
    evidence.add_argument("argv", nargs=argparse.REMAINDER)
    entry = commands.add_parser("entry", help="Append an identified task note")
    entry.add_argument("--task", required=True)
    entry.add_argument("--file", required=True)
    promotion = commands.add_parser("promote", help="Apply a reviewed selective promotion proposal")
    promotion.add_argument("proposal")
    amendment = commands.add_parser("amend", help="Apply a reviewed semantic correction or retraction")
    amendment.add_argument("proposal")
    commands.add_parser("recover", help="Recover an interrupted memory transaction")
    host_hook = commands.add_parser("hook", help="Process host hook input on stdin")
    host_hook.add_argument("event", choices=["SessionStart", "SubagentStart", "PreToolUse", "Stop"])
    host_hook.add_argument("--host", choices=["claude", "codex"], default="claude")
    installation = commands.add_parser("install-hooks", help="Merge reviewed AI-OS hooks without replacing unrelated settings")
    installation.add_argument("--host", choices=["claude", "codex"], required=True)
    installation.add_argument("--template", type=Path, required=True)
    return result


def run(arguments):
    default_root = Path(__file__).resolve().parents[2] if arguments.command == "hook" else Path.cwd()
    root = (arguments.project or default_root).resolve()
    if arguments.command == "hook":
        body = json.load(sys.stdin)
        if not isinstance(body, dict):
            raise ValueError("Expected a host hook object")
        body["ai_os_host"] = arguments.host
        return hook(root, arguments.event, body)
    if arguments.command == "install-hooks":
        return install_hooks(root, arguments.host, arguments.template)
    if arguments.command == "verify":
        argv = arguments.argv[1:] if arguments.argv[:1] == ["--"] else arguments.argv
        return verify(root, arguments.file, argv)
    if arguments.command == "entry":
        return add_entry(root, arguments.task, arguments.file)
    if arguments.command == "promote":
        return promote(root, arguments.proposal)
    if arguments.command == "amend":
        return amend(root, arguments.proposal)
    if arguments.command == "recover":
        return recover(root)
    if arguments.command == "task":
        path = create_task(root, arguments.name) if arguments.create else task_path(root, arguments.name)
        return path.relative_to(root).as_posix()
    if arguments.command == "pack":
        pack = build_pack(root, arguments.task, arguments.skill, arguments.file)
        if arguments.snapshot:
            save_snapshot(root, pack)
        return render_pack(pack) if arguments.render else pack
    if arguments.command == "replay":
        return render_pack(load_snapshot(workspace_path(root, arguments.snapshot)))
    if arguments.command == "diff":
        before = load_snapshot(workspace_path(root, arguments.before))
        after = load_snapshot(workspace_path(root, arguments.after))
        return diff_packs(before, after)
    raise ValueError("Unknown AI-OS command")


def main():
    try:
        result = run(parser().parse_args())
        sys.stdout.buffer.write(result.encode("utf-8") if isinstance(result, str)
                                else canonical_json(result))
        sys.stdout.buffer.write(b"\n")
        return 1 if isinstance(result, dict) and result.get("passed") is False else 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        print("AI-OS: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
