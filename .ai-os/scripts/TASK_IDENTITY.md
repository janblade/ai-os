# Optional collision-safe task identities

Use Python 3.8+ to explicitly create/resolve a task:

```text
python .ai-os/scripts/task_identity.py --name feature/a_b --create
```

Omit --name to use the current Git branch. Detached/non-Git work needs a user-identified
task. Without --create, lookup is read-only. New files use a readable slug and full SHA-256
of the original identity. Canonical files take precedence when already present.

Legacy continuity: headerless main.md, master.md, develop.md and other lossless names
(letters/digits/dots/hyphens, starting with a letter/digit) are reused in place when stored
filename case matches exactly. --create does not overwrite them or create a competing file.
Names with underscores, slash substitutions, or case mismatches need one exact Branch:
header to establish ownership. Ambiguous files warn, remain untouched, and require review;
never automatically move, delete, or attribute their notes to another task.

BOOT and its default filename instructions are unchanged. This is an opt-in tool, not a
framework-wide migration: use the returned path consistently for an opted-in task. The
startup hook recognizes canonical and safe legacy files. Until the owner approves any
BOOT integration, ordinary boot flows on other hosts can still create sanitized filenames.
No claim of universal collision prevention or repository-owner authorization is made.

Keep identity headers when draining canonical tasks; do not infer ownership by reversing a
slug/hash. Creation is exclusive and lookup errors do not block startup governance. No
locks, journals, mutation/Stop gates or new authorization rules are introduced.
