#!/usr/bin/env python3
"""Small, standard-library-only command entry point for AI-OS."""

import argparse
import sys
from pathlib import Path

from context import build_pack, create_task, diff_packs, load_snapshot, render_pack, save_snapshot, task_path
from storage import canonical_json, workspace_path


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
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
    return result


def run(arguments):
    root = arguments.project.resolve()
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
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("AI-OS: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
