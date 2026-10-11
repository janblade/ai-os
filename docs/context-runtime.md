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
