"""Resolve task memory without locks, hooks, or destructive legacy migration."""

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path


TASKS = Path(".ai-os/memory/tasks")


def task_key(name):
    if not name or name != name.strip() or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError("Task identity must be nonempty text without edge whitespace or controls")
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", name)[:20]
    return "task-" + slug + "-" + hashlib.sha256(name.encode("utf-8")).hexdigest()


def checked_path(root, filename):
    path = root / TASKS / filename
    if path.resolve() != path:
        raise ValueError("Task path must not traverse symlinks or junctions")
    return path


def task_path(root, name):
    root = Path(root).resolve()
    canonical = checked_path(root, task_key(name) + ".md")
    if canonical.exists():
        return canonical
    # Old agents sanitized characters; the shell hook's tr sanitized UTF-8 bytes.
    legacy_names = dict.fromkeys((re.sub(r"[^A-Za-z0-9._-]", "_", name),
                                 re.sub(rb"[^A-Za-z0-9._-]", b"_", name.encode("utf-8")).decode("ascii")))
    for legacy_name in legacy_names:
        if len(legacy_name) > 240:
            continue
        legacy = checked_path(root, legacy_name + ".md")
        if not legacy.is_file():
            continue
        headers = re.findall(r"^Branch:[ \t]*(.*)$", legacy.read_text(encoding="utf-8-sig"), re.MULTILINE)
        if len(headers) == 1 and headers[0].strip() == name:
            return legacy
        # No underscore means sanitization could not have collapsed another identity.
        # Check stored case as well, since Windows file lookup is case-insensitive.
        if (not headers and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", name)
                and any(entry.name == legacy.name for entry in legacy.parent.iterdir())):
            return legacy
        print("AI-OS: ambiguous legacy task " + legacy.name +
              "; preserved and skipped. Review ownership before adding an exact Branch: header.", file=sys.stderr)
    return canonical


def create_task(root, name):
    path = task_path(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("# Task\n\nTask-ID: " + task_key(name) + "\nBranch: " + name + "\n\n")
    except FileExistsError:
        if not path.is_file():
            raise
    return path


def current_identity(root):
    result = subprocess.run(["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"],
                            capture_output=True, encoding="utf-8", timeout=5)
    return result.stdout.strip() if result.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--name", help="Original branch or user-supplied task identity; defaults to current branch")
    parser.add_argument("--create", action="store_true", help="Create only if absent; never overwrite legacy notes")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        name = args.name if args.name is not None else current_identity(root)
        if name is None:
            if args.create:
                raise ValueError("No branch identity; supply --name for a user-named task")
            return 0
        path = create_task(root, name) if args.create else task_path(root, name)
        print(path.relative_to(root).as_posix())
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        print("AI-OS task lookup: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
