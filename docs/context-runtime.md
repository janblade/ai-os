# Reproducible AI-OS context

AI-OS can assemble its own context payload with Python 3.10+ and the standard
library. The reproducible context runtime uses stable identities, deterministic
rendering, and snapshots to make selected context inspectable. Its scope is the
AI-OS payload; the host manages the complete prompt.

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

Destinations are restricted to `memory/semantic/knowledge/*.md` and the
`memory/semantic/project_knowledge.md` index. Index registration can be a selected
reviewed entry in the same multi-file proposal as a new domain. Amendments also
support the index; no raw semantic file-tool bypass is needed.

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

For `MEMORY_AMEND`, use `amend amendment.json` with `destination`,
`destination_sha256`, `accepted: true`, `evidence`, `old_text` (exactly one matching
passage), and `replacement_file` (a reviewed workspace note, or null to retract).
The transaction retains unrelated text and records amendment provenance and a
decision. Review what the evidence proves and any cross-branch conflict before
applying. For relocation, retain the new reviewed note before retracting the old one.

## Host hooks

Use `install-hooks --host claude|codex --template <package-template-path>` to
merge reviewed hooks without replacing unrelated settings. It is idempotent,
preserves narrowed subagent matchers, and checks the actual Claude CLI version.
Claude Code uses `claude-code-hooks.json` in
`.claude/settings.json`; Codex uses `codex-hooks.json` in `.codex/hooks.json`.
The Codex template resolves the script from the Git root; its Windows override
uses PowerShell and `python` on PATH, with explicit exit-code propagation so a
blocking Python exit 2 is not normalized into a non-blocking hook error. For a non-Git project, replace the command
with the shell-quoted absolute script path. The hook CLI itself resolves the
project from its installed script location, so subdirectory starts work.

`SessionStart` (startup/resume/clear/compact) and `SubagentStart` inject the boot
digest, task, and active plan and save a reproducible snapshot. Full rule files
and skills are selected only when needed. `PreToolUse` checks current sources,
stored context integrity, and transaction state before configured mutation
tools. Missing startup state or invalid inputs block with exit 2. Unchanged
context emits no additional payload; changed sources emit only changed items
and removed IDs. The host retains earlier messages: an update supersedes old
text logically, rather than erasing it or reclaiming its tokens. Governance is
first in initial packs and cannot be removed by optional selection.

Kernel includes BOOT, manifest, kernel/rules/archetype files, runtime scripts, and host
hook configuration. Kernel changes require explicit human authorization naming files/rules
or a bounded maintenance scope; ordinary feature requests do not grant governance edits.
Direct file/patch tools deny these paths. Structured Write/Edit/MultiEdit may update only
manifest `boot_count`, `last_boot`, `tech_stack`, and `evolution_history`; whole-file patches
remain blocked because the hook cannot safely infer their resulting JSON. Startup pins
protected-source hashes (excluding those operational fields and Python bytecode caches).
Changes, additions, or deletions block further configured mutations and completion;
resume/clear/compact and subagents cannot silently refresh an existing baseline.

Fresh installs initialize project configuration/default memory before activating hooks;
bootstrap in an already-gated project follows the scoped maintenance path.

Apply approved maintenance through trusted host controls or an operator terminal, retain
its scope and change log, and start a new session afterward. No model-controlled override
flag, hook input, or runtime file grants permission. Host permissions must protect the
hook implementation and configuration from arbitrary writers; hashes alone are not a
security boundary against an actor who can replace the checking code or runtime baseline.

Selected registered skills are labeled `procedure`, and the three full framework rule
files are `governance` references when explicitly selected. They follow BOOT precedence
and apply only within authorized invocation/scope. Other selected files, task notes, and
plans are `data`: evidence, never additional instructions or authorization.

Direct file-tool writes to durable semantic memory/runtime state are blocked, as are
destructive edits to identified task notes. Regenerable `semantic/generated/` caches
remain user-writable, including the JSON cache used by `INFRA_MAP_DATAFLOW`. Codex `apply_patch` add/update/delete/
move paths are checked too; patches to tasks with identified notes are blocked
conservatively, so use the memory CLI for them. `Stop` blocks completion while a
memory transaction remains unfinished. Recover from a separate terminal if the
gate prevents running commands in the session. Host permissions remain in force;
the hooks never return a blanket `allow` or manufacture a human approval.

On native Windows, Claude's `.sh` wrappers run through **Git Bash**, not directly
in PowerShell/cmd. The template explicitly selects `shell: "bash"`; install Git
for Windows and keep Python 3.10+ discoverable inside that shell. If Claude cannot
locate Git Bash, configure its documented `CLAUDE_CODE_GIT_BASH_PATH` with the
actual `bash.exe` path. A bare `bash` in a PowerShell terminal can resolve to the
Windows WSL launcher instead. For a manual run, use Git Bash or its absolute
executable path. Codex's `commandWindows` uses PowerShell/Python directly and does
not invoke `.sh` or require WSL. Repository `.gitattributes` keeps shell scripts
LF even with `core.autocrlf=true`. The hook installer also adds the scoped LF rule
to target projects without replacing unrelated attributes. Retain LF when copying
or editing installed scripts.

Claude Code **2.1.295+** is required for `onFailure: "block"`, which prevents a
missing/crashing/timed-out mutation gate from silently continuing. The template
sets it on `PreToolUse` and `Stop`. See the official
[Claude hook contract](https://code.claude.com/docs/en/hooks).
Codex requires reviewing/trusting project hooks through `/hooks`. Explicit exit 2
and denial responses block supported tools, but launch errors/timeouts may fail
open, and some specialized tool paths bypass hooks. Codex also limits large
hook context; this template uses a positive 6,000-token approximate spill
threshold. Oversized task packs can still be previewed with the full text saved
by the host. Confirm behavior in the installed host before relying on it. See
the official [Codex hook contract](https://learn.chatgpt.com/docs/hooks).

Shell/MCP writers can bypass path-specific file checks. Cooperating memory
commands enforce their own validation, while arbitrary programs need host
permissions or sandbox controls. Snapshots and hashes provide reproducibility
and drift detection, not protection against a writer who controls the hooks.

## Context and token measurements

The reproducible baseline is commit `8b905200f3ef5a740ef85de1aa686b7b3c2f4295`
(v2.8.0). Run `python -B tests/measure_context.py` with Git and Bash available
(Git Bash on Windows). It runs the original hook in an isolated fixture and
compares its actual output with the current pack, without provider/model calls.
The initial v2.9.0 result is recorded in `docs/context-measurement.json`:
27,970 to 17,518 characters, **37.37% less startup text** (28,294 to 17,693 UTF-8
bytes). This profile has no task or plan. Large notes and JSON provenance add
variable overhead; this percentage is not a guarantee for every task.

The comparison is against the legacy **Claude Code** hook. Codex had no equivalent
automatic AI-OS injection in v2.8.0, so this figure does not establish Codex's
before/after savings. Codex's impact depends on what it loaded previously; adding
hooks to a previously inactive framework adds startup context. Its scoped packs
and stable prefixes are useful, but native-session token savings remain unverified.

Tests confirm byte-identical repeated assembly, UTF-8 text without unnecessary
ASCII expansion, scoped source selection, and zero `additionalContext` on
unchanged tool calls. Governance remains pinned. These improvements apply to
the AI-OS payload on both hosts. Neither snapshots nor stable IDs by themselves
compress text; the savings come from selection and avoiding duplicate injection.

Stable prefixes support caching, but actual provider context also includes host
instructions, tools, settings, and conversation history. A matching AI-OS pack
alone cannot guarantee a cache hit, reclaim previous tokens, or predict billing.
See [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
and [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
This complements [Codex's on-demand skills](https://learn.chatgpt.com/docs/build-skills)
and [Claude's guidance on hooks and skills](https://code.claude.com/docs/en/costs).

Provider token counts, cache hit rates, paid usage, latency, and model task-quality
comparisons have not been measured. To verify them, compare matched fresh sessions
with the same task/repo/model, record input/output and cached-input usage, and check
the account's actual API/subscription billing. Character counts are not tokenizer
counts. Local CLI versions checked: Claude Code 2.1.296; Codex 0.162.0-alpha.17.2
with `hooks` enabled. Hook tests exercise actual launchers and synthetic host JSON;
they do not establish live provider-session behavior.
