"""Compare actual legacy hook output with current AI-OS text, without model calls."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".ai-os/scripts"))
from context import build_pack, render_pack
from hooks import hook


BASELINE = "8b905200f3ef5a740ef85de1aa686b7b3c2f4295"


def measure():
    repository = Path(__file__).resolve().parents[1]
    bash = shutil.which("bash")
    if os.name == "nt":
        bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        if not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise ValueError("Measurement fixture is outside the temporary directory")
        old, new = root / "old", root / "new"
        for project in [old, new]:
            (project / ".ai-os/rules").mkdir(parents=True)
        for name in ["BOOT.md", "rules/ultimate_rules.md", "scripts/session-start-hook.sh", "manifest.json"]:
            raw = subprocess.run(["git", "-C", str(repository), "show", BASELINE + ":.ai-os/" + name],
                                 capture_output=True, check=True).stdout
            path = old / ".ai-os" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for name in ["BOOT.md", "manifest.json", "registry/index.json"]:
            path = new / ".ai-os" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((repository / ".ai-os" / name).read_bytes())
        result = subprocess.run([bash, (old / ".ai-os/scripts/session-start-hook.sh").as_posix()],
                                env={**os.environ, "CLAUDE_PROJECT_DIR": str(old)}, capture_output=True, check=True)
        before = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        after = render_pack(build_pack(new))
        hook(new, "SessionStart", {"session_id": "measurement", "hook_event_name": "SessionStart"})
        unchanged = hook(new, "PreToolUse", {"session_id": "measurement", "hook_event_name": "PreToolUse",
                                              "tool_name": "Bash", "tool_input": {"command": "git status"}})
        return {"baseline_commit": BASELINE, "baseline_host": "claude", "baseline_version": json.loads((old / ".ai-os/manifest.json").read_bytes())["ai_os_version"],
                "current_version": json.loads((new / ".ai-os/manifest.json").read_bytes())["ai_os_version"],
                "profile": "governance only; no task or plan", "baseline_characters": len(before), "current_characters": len(after),
                "character_reduction_percent": round((1 - len(after) / len(before)) * 100, 2),
                "baseline_utf8_bytes": len(before.encode("utf-8")), "current_utf8_bytes": len(after.encode("utf-8")),
                "identical_repeated_render": after == render_pack(build_pack(new)),
                "unchanged_tool_additional_context_characters": len(unchanged.get("hookSpecificOutput", {}).get("additionalContext", "")),
                "provider_token_counts_or_billing_measured": False}


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2))
