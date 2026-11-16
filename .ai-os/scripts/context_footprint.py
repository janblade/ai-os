"""Report what the framework puts in context before any work starts. Read-only.

Usage: python .ai-os/scripts/context_footprint.py [--root DIR] [--json]

Runtime token use is host-owned and not measurable from here (R5). File sizes are, so this
counts the fixed part: the files every boot reads, what the Claude Code / Codex hook
injects per session start and per subagent spawn, the bridge files, and the generated
skill-pointer descriptions. Token figures are characters / 4 -- an estimate, not a
tokenizer count.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Mirrors the Caps paragraph of core.infra.sk "Environment Facts", the source of truth.
# Change both together.
FACT_MAX_ENTRIES = 4
FACT_MAX_CHARS = 600
BRIDGE_FILES = ("AGENTS.md", "CLAUDE.md", ".agents/AGENTS.md", ".github/copilot-instructions.md",
                ".cursor/rules/ai-os.md", ".windsurfrules")
UNRESOLVED_ARCHETYPES = ("", "auto", None)


def chars(path):
    try:
        return len(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError):
        return None


def load_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def task_file(root):
    """The open task file for the current branch, or None. Never raises."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from task_identity import current_identity, task_path
        name = current_identity(root)
        path = task_path(root, name) if name else None
        return path if path and path.is_file() else None
    except (ImportError, OSError, ValueError, subprocess.SubprocessError):
        return None  # best-effort, same stance and exception set as codex-context-hook.py
    finally:
        sys.path.pop(0)


def pointer_descriptions(root):
    """Text the host keeps loaded per skill pointer: '{pointer_description} Commands: {..}.'"""
    total = 0
    for skill in load_json(root / ".ai-os/registry/index.json").get("skills", []):
        commands = skill.get("commands", []) + skill.get("backs_builtin_commands", [])
        lead = skill.get("pointer_description") or skill.get("description", "")
        total += len("%s Commands: %s." % (lead, ", ".join(commands)))
    return total


def group(root, relative_paths):
    items = []
    for relative in relative_paths:
        size = chars(root / relative)
        if size is not None:
            items.append({"path": relative, "chars": size})
    return {"items": items, "chars": sum(item["chars"] for item in items)}


def archetype_files(manifest):
    """BOOT.md section 2 step 2: a named archetype loads its file; `auto` reads the index to
    resolve one, then loads that one too -- which one is unknown until boot runs."""
    archetype = manifest.get("project_archetype", "auto")
    if archetype in UNRESOLVED_ARCHETYPES:
        return [".ai-os/genome/archetypes/index.json"], True
    return [".ai-os/genome/archetypes/%s.json" % archetype], False


def measure(root):
    root = Path(root).resolve()
    aios = root / ".ai-os"
    task = task_file(root)
    task_relative = [task.relative_to(root).as_posix()] if task else []
    archetype_relative, unresolved = archetype_files(load_json(aios / "manifest.json"))
    facts = load_json(aios / "genome/project_genome.json").get("environment_facts", [])
    if not isinstance(facts, list):
        facts = []
    fact_chars = sum(len(str(fact.get("fact", ""))) for fact in facts if isinstance(fact, dict))
    report = {
        "boot_read": group(root, [".ai-os/BOOT.md", ".ai-os/manifest.json",
                                  ".ai-os/genome/project_genome.json"] + archetype_relative
                           + [".ai-os/memory/episodic/last_session.json"] + task_relative),
        "hook_payload": group(root, [".ai-os/BOOT.md", ".ai-os/rules/ultimate_rules.md"]
                              + task_relative),
        "governance": group(root, [".ai-os/BOOT.md", ".ai-os/rules/ultimate_rules.md"]),
        "bridge_files": group(root, BRIDGE_FILES),
        "skill_pointers": {"items": [], "chars": pointer_descriptions(root)},
        "environment_facts": {"entries": len(facts), "chars": fact_chars,
                              "over_cap": len(facts) > FACT_MAX_ENTRIES
                              or fact_chars > FACT_MAX_CHARS},
    }
    report["boot_read"]["archetype_unresolved"] = unresolved
    for name, value in report.items():
        if "chars" in value and name != "environment_facts":
            value["tokens_estimate"] = value["chars"] // 4
    return report


def render(report):
    lines = []

    def section(label, key, note=None):
        data = report[key]
        lines.append("%s\n  %d chars, ~%d tokens (chars/4 estimate)"
                     % (label, data["chars"], data["tokens_estimate"]))
        if note:
            lines.append("  " + note)
        lines.extend("    %7d  %s" % (item["chars"], item["path"]) for item in data["items"])

    section("Boot read (every host, every session)", "boot_read",
            "+ one archetype file once `auto` resolves (about 0.8 KB)"
            if report["boot_read"]["archetype_unresolved"] else None)
    section("Hook payload (Claude Code / Codex: per session start AND per subagent spawn)",
            "hook_payload", "file contents only; the hook's own wrapper text is not counted")
    lines.append("Bridge files present (each host loads one of these, not all)")
    lines.extend("    %7d  %s  (~%d tokens)" % (item["chars"], item["path"], item["chars"] // 4)
                 for item in report["bridge_files"]["items"])
    section("Skill-pointer descriptions (Claude Code, always loaded)", "skill_pointers")
    facts = report["environment_facts"]
    lines.append("Environment facts: %d of %d entries, %d of %d chars%s"
                 % (facts["entries"], FACT_MAX_ENTRIES, facts["chars"], FACT_MAX_CHARS,
                    "  <-- OVER CAP, trim (core.infra.sk)" if facts["over_cap"] else ""))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure(args.root)
    print(json.dumps(report, indent=2) if args.json else render(report))


if __name__ == "__main__":
    main()
