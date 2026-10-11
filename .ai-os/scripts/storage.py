"""Workspace-bounded storage shared by AI-OS commands and hooks."""

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path


RUNTIME = ".ai-os/memory/runtime"


def canonical_json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def workspace_path(root, name):
    root = Path(root).resolve()
    path = Path(name)
    if not name or ".." in path.parts:
        raise ValueError("Expected a workspace path without traversal")
    path = path if path.is_absolute() else root / path
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Path is outside the project")
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0)
                                 & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("Linked paths are not supported")
    return resolved


def read_json(path):
    return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".aios-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def memory_lock(root):
    lock = workspace_path(root, RUNTIME + "/write.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError("AI-OS memory is busy; check recovery before removing a stale lock") from error
    os.close(descriptor)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def git_value(root, *arguments):
    result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, check=False)
    return result.stdout.decode("utf-8").strip() if result.returncode == 0 else None
