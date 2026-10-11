# Reproducible AI-OS context

AI-OS can assemble its own context payload with Python 3.10+ and the standard
library. This borrows PACT's stable identity, deterministic rendering, and snapshot
ideas; it does not claim full PACT conformance or control over the host's entire prompt.

Run commands from the project root:

```sh
python .ai-os/scripts/ai_os.py task --name feature/login --create
python .ai-os/scripts/ai_os.py pack --skill core.testing.sk --file src/login.py --snapshot
python .ai-os/scripts/ai_os.py pack --render
```

The pack always includes the boot digest, followed by the active task and its
`Active plan:` file when present. Requested skills and explicitly selected files
follow in stable order. Each item records its source, selection reason, content,
and SHA-256. Selection never changes the original memory files.

Task filenames include a hash of the complete original identity. Branches such as
`feature/a` and `feature_a`, including names differing only in case on Windows,
therefore use distinct files. Existing task files remain in place. A legacy file
is selected automatically only with an exact `Branch: <original name>` header;
verify its ownership before adding that header. No automatic rename or purge occurs.

`--task` on `pack` selects a named branch/ad-hoc task. In a detached or non-Git
workspace, name the task explicitly. `--file` paths must stay inside the workspace;
symlinks, private environment/key files, and runtime state are rejected. Review
selected sources for secrets before including them; filename checks are not a
complete secret scanner.

Snapshots are content-addressed files under `.ai-os/memory/runtime/snapshots/`.
Keep the entire runtime directory ignored: snapshots contain the selected text,
including working notes, and belong to local inspection rather than shared memory.
The snapshot filename is the SHA-256 of its canonical JSON bytes. Inspect or replay:

```sh
python .ai-os/scripts/ai_os.py replay .ai-os/memory/runtime/snapshots/<hash>.json
python .ai-os/scripts/ai_os.py diff <older-snapshot-path> <newer-snapshot-path>
```

Replay reads the stored content, not the current files. It reproduces the AI-OS
payload, not the complete provider input or the model's answer. A memory write lock
prevents context assembly during cooperating mutations; an unfinished transaction
blocks assembly until recovered. Other programs must use the same tooling to participate.

Run the checks with `python -B -m unittest discover -s tests -v`.

## Selective memory promotion

Record explicit dependency files and a check, then create an identified task note:

```sh
python .ai-os/scripts/ai_os.py verify --file src/login.py -- python -m unittest tests.test_login
python .ai-os/scripts/ai_os.py entry --task .ai-os/memory/tasks/<task-file>.md --file reviewed-note.md
```

`verify` executes the given arguments without a shell and records exit status,
dependency hashes, commit identity, and output hashes. It does not store raw command
arguments or test output. A failed check or a dependency/commit change during the
check cannot pass. Declare all relevant dependencies: evidence only covers the
listed files, and a passing check does not prove that the note's claim is correct.

Review a proposal file before executing `promote proposal.json`:

```json
{
  "task": ".ai-os/memory/tasks/<task-file>.md",
  "task_sha256": "<current raw file hash>",
  "promotions": [{
    "entry_id": "<ID from entry>",
    "accepted": true,
    "destination": ".ai-os/memory/semantic/knowledge/known_gotchas.md",
    "destination_sha256": "<current raw file hash, or null if absent>",
    "evidence": ".ai-os/memory/runtime/evidence/<hash>.json"
  }]
}
```

Only selected entry blocks move. Other notes, unresolved entries, and active-plan
pointers remain byte-for-byte. Entries beginning with `TODO`, `FIXME`, `BUG`, `WIP`,
or an unchecked checkbox cannot be promoted. Existing destinations and tasks must
match their reviewed hashes. Evidence must still match the current commit and
dependency files. Destination entries retain task/entry/evidence provenance, and
the decision log is part of the transaction. Entry IDs prevent repeated promotion
to the same destination; reviewing semantic duplicates still requires judgment.

`accepted: true` records the review decision, **not proof of human approval**.
Follow existing user authorization and host approval requirements. These files
are editable by the same user; hashes detect drift, not a malicious writer.

Writes use a cooperative lock, atomic file replacements, and a recovery journal.
An interrupted multi-file write blocks context assembly. Run `recover` to roll
back a prepared transaction or retain a committed one. Recovery refuses to
overwrite outside edits. If a process crashed while holding `write.lock`, verify
that no writer is active before removing that lock and recovering. This is not
global filesystem atomicity for programs that ignore the lock. Keep runtime
evidence, snapshots, and journals private and ignored.
