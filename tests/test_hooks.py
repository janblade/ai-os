import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from workspace import Workspace
from context import create_task
from hooks import hook, session_pointer
from storage import RUNTIME, memory_lock


class HookTests(Workspace):

    def body(self, event, **extra):
        return {"hook_event_name": event, "session_id": "test-session", **extra}

    def start(self):
        return hook(self.root, "SessionStart", self.body("SessionStart"))

    def pre(self, tool="Bash", **data):
        return hook(self.root, "PreToolUse", self.body("PreToolUse", tool_name=tool, tool_input=data))

    def test_unchanged_context_emits_no_additional_payload(self):
        self.assertIn("Governance", self.start()["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.pre(command="git status"), {})
        self.assertEqual(self.pre(command="git status"), {})

    def test_changed_task_emits_only_delta(self):
        from unittest.mock import patch
        task = create_task(self.root, "main")
        with patch("context.current_identity", return_value="main"):
            self.start()
            task.write_text(task.read_text() + "new note\n", encoding="utf-8")
            changed = self.pre(command="git status")["hookSpecificOutput"]["additionalContext"]
            self.assertIn("new note", changed)
            self.assertNotIn("Governance", changed)
            self.assertEqual(self.pre(command="git status"), {})

    def test_missing_startup_and_corrupt_snapshot_block_mutations(self):
        self.assertEqual(self.pre()["hookSpecificOutput"]["permissionDecision"], "deny")
        self.start()
        pointer = session_pointer(self.root, self.body("SessionStart"))
        snapshot = self.root / json.loads(pointer.read_text())["snapshot"]
        snapshot.write_text("{}")
        with self.assertRaises(ValueError):
            self.pre()

    def test_memory_bypass_and_task_note_destruction_are_blocked(self):
        self.start()
        with self.assertRaises(ValueError):
            self.pre("Write", file_path=".ai-os/memory/semantic/knowledge/file.md", content="unverified")
        with self.assertRaises(ValueError):
            self.pre("Write", file_path=RUNTIME + "/fake.json", content="{}")
        task = self.write(".ai-os/memory/tasks/test.md", "<!-- AIOS-ENTRY: " + "a" * 32 + " -->\nTODO: unresolved\n<!-- /AIOS-ENTRY -->\n")
        with self.assertRaises(ValueError):
            self.pre("Write", file_path=str(task), content="cleared")
        with self.assertRaises(ValueError):
            self.pre("Edit", file_path=str(task), old_string="TODO: unresolved", new_string="accepted")
        self.assertEqual(self.pre("Write", file_path=str(task), content=task.read_text() + "More notes"), {})

    def test_unknown_invalid_and_traversing_hook_inputs_fail(self):
        self.start()
        for body in [[], {}, self.body("Other"), self.body("PreToolUse", tool_name="Write", tool_input={})]:
            with self.assertRaises((ValueError, KeyError)):
                hook(self.root, "PreToolUse", body)
        with self.assertRaises(ValueError):
            self.pre("Write", file_path="../outside.md", content="outside")

    def test_pending_transaction_and_lock_gate_mutation_and_completion(self):
        self.start()
        self.write(RUNTIME + "/transaction.json", "{}")
        with self.assertRaises(ValueError):
            self.pre()
        self.assertEqual(hook(self.root, "Stop", self.body("Stop"))["decision"], "block")
        with memory_lock(self.root):
            with self.assertRaises(ValueError):
                hook(self.root, "Stop", self.body("Stop"))

    def test_subagent_context_is_recorded_separately(self):
        child = self.body("SubagentStart", agent_id="child")
        self.assertEqual(hook(self.root, "SubagentStart", child)["hookSpecificOutput"]["hookEventName"], "SubagentStart")
        body = self.body("PreToolUse", agent_id="child", tool_name="Bash", tool_input={"command": "git status"})
        self.assertEqual(hook(self.root, "PreToolUse", body), {})
        self.assertEqual(self.pre()["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_codex_patch_operations_are_bounded_and_gate_memory(self):
        self.start()
        self.assertEqual(self.pre("apply_patch", command="*** Begin Patch\n*** Add File: src.py\n+value=1\n*** End Patch"), {})
        for name in ["../outside.md", ".ai-os/memory/semantic/knowledge/file.md", RUNTIME + "/fake.json"]:
            with self.assertRaises(ValueError):
                self.pre("apply_patch", command="*** Begin Patch\n*** Add File: " + name + "\n+unverified\n*** End Patch")
        with self.assertRaises(ValueError):
            self.pre("apply_patch", command="*** Begin Patch\n*** Update File: src.py\n*** Move to: ../outside.py\n*** End Patch")

    def test_codex_and_claude_sessions_do_not_share_a_pointer(self):
        body = self.body("SessionStart", ai_os_host="codex")
        hook(self.root, "SessionStart", body)
        self.assertEqual(self.pre()["hookSpecificOutput"]["permissionDecision"], "deny")
        body = self.body("PreToolUse", ai_os_host="codex", tool_name="Bash", tool_input={"command": "git status"})
        self.assertEqual(hook(self.root, "PreToolUse", body), {})

    def test_real_launcher_emits_valid_json_and_nonzero_on_invalid_governance(self):
        package = Path(__file__).resolve().parents[1]
        source = package / ".ai-os/scripts"
        destination = self.root / ".ai-os/scripts"
        destination.mkdir(parents=True, exist_ok=True)
        for file in source.glob("*"):
            if file.is_file():
                shutil.copyfile(file, destination / file.name)
        bash = shutil.which("bash")
        if os.name == "nt":
            git_bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
            bash = str(git_bash) if git_bash.exists() else None
        if not bash:
            self.skipTest("Bash is unavailable")
        environment = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        # Ensure the known Python interpreter is discoverable, without touching the host PATH.
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
        command = [bash, (destination / "session-start-hook.sh").as_posix()]
        result = subprocess.run(command, input=json.dumps(self.body("SessionStart")), text=True,
                                capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"], "SessionStart")
        (self.root / ".ai-os/BOOT.md").unlink()
        result = subprocess.run(command + ["PreToolUse"], input=json.dumps(self.body("PreToolUse", tool_name="Bash", tool_input={})),
                                text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_hook_stdin_is_utf8_even_with_legacy_python_console_encoding(self):
        package = Path(__file__).resolve().parents[1]
        cli = package / ".ai-os/scripts/ai_os.py"
        environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        command = [sys.executable, "-B", str(cli), "--project", str(self.root), "hook"]
        body = self.body("SessionStart")
        result = subprocess.run(command + ["SessionStart"], input=json.dumps(body).encode("utf-8"),
                                capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write(".ai-os/memory/tasks/\u4efb\u52a1.md", "<!-- AIOS-ENTRY: " + "a" * 32 + " -->\nUnresolved\n<!-- /AIOS-ENTRY -->")
        body = self.body("PreToolUse", tool_name="apply_patch", tool_input={"command":
            "*** Begin Patch\n*** Delete File: .ai-os/memory/tasks/\u4efb\u52a1.md\n*** End Patch"})
        result = subprocess.run(command + ["PreToolUse"], input=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                capture_output=True, env=environment)
        self.assertEqual(result.returncode, 2, result.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell hook contract")
    def test_codex_windows_command_keeps_exit_2_and_resolves_root_from_subdirectory(self):
        package = Path(__file__).resolve().parents[1]
        destination = self.root / ".ai-os/scripts"
        destination.mkdir(parents=True)
        for file in (package / ".ai-os/scripts").glob("*"):
            if file.is_file():
                shutil.copyfile(file, destination / file.name)
        subprocess.run(["git", "init", str(self.root)], capture_output=True, check=True)
        child = self.root / "child"
        child.mkdir()
        template = json.loads((package / ".ai-os-installer/templates/codex-hooks.json").read_text())
        environment = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}
        for event in ["SessionStart", "PreToolUse"]:
            command = template["hooks"][event][0]["hooks"][0]["commandWindows"]
            body = self.body(event)
            if event == "PreToolUse":
                body.update(tool_name="apply_patch", tool_input={"command":
                    "*** Begin Patch\n*** Add File: .ai-os/memory/semantic/knowledge/fake.md\n+unverified\n*** End Patch"})
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                                    cwd=child, input=json.dumps(body).encode("utf-8"), capture_output=True, env=environment)
            self.assertEqual(result.returncode, 0 if event == "SessionStart" else 2, result.stderr)
            if event == "SessionStart":
                self.assertIn("Governance", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_shell_script_checkout_keeps_lf_with_autocrlf_enabled(self):
        package = Path(__file__).resolve().parents[1]
        self.write(".gitattributes", (package / ".gitattributes").read_text())
        source = package / ".ai-os/scripts/session-start-hook.sh"
        destination = self.root / ".ai-os/scripts/session-start-hook.sh"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(source.read_bytes())
        subprocess.run(["git", "init", str(self.root)], capture_output=True, check=True)
        command = ["git", "-C", str(self.root), "-c", "core.autocrlf=true"]
        subprocess.run(command + ["add", ".gitattributes", ".ai-os/scripts/session-start-hook.sh"], capture_output=True, check=True)
        subprocess.run(command + ["checkout-index", "--force", "--", ".ai-os/scripts/session-start-hook.sh"], capture_output=True, check=True)
        self.assertNotIn(b"\r\n", destination.read_bytes())
        self.assertEqual(destination.read_bytes(), source.read_bytes())
