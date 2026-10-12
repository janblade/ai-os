import json
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
from pathlib import Path

from workspace import Workspace
from installation import install_hooks


class InstallationTests(Workspace):

    def setUp(self):
        super().setUp()
        runtime = patch("installation.subprocess.run", return_value=CompletedProcess([], 0, "2.1.296 (Claude Code)", ""))
        runtime.start()
        self.addCleanup(runtime.stop)

    def template(self, host):
        name = "claude-code-hooks.json" if host == "claude" else "codex-hooks.json"
        return Path(__file__).resolve().parents[1] / ".ai-os-installer/templates" / name

    def test_merge_preserves_permissions_other_hooks_and_is_idempotent(self):
        for host, name in [("claude", ".claude/settings.json"), ("codex", ".codex/hooks.json")]:
            other = {"matcher": "Bash", "hooks": [{"type": "command", "command": "user-check"}]}
            self.write(name, json.dumps({"permissions": {"deny": ["Bash(dangerous)"]}, "hooks": {"PreToolUse": [other]}}))
            self.write(".gitattributes", "docs/*.md text eol=crlf\n")
            result = install_hooks(self.root, host, self.template(host))
            self.assertTrue(result["changed"])
            self.assertEqual((self.root / ".gitattributes").read_text(),
                             "docs/*.md text eol=crlf\n.ai-os/scripts/*.sh text eol=lf\n")
            config = json.loads((self.root / name).read_text())
            self.assertEqual(config["permissions"], {"deny": ["Bash(dangerous)"]})
            self.assertEqual(config["hooks"]["PreToolUse"][0], other)
            self.assertEqual(len(config["hooks"]["PreToolUse"]), 2)
            self.assertFalse(install_hooks(self.root, host, self.template(host))["changed"])

    def test_refresh_owned_hooks_preserves_narrowed_subagent_matcher(self):
        name = ".claude/settings.json"
        old = {"hooks": {"SubagentStart": [{"matcher": "Plan", "hooks": [
            {"type": "command", "command": 'bash "${CLAUDE_PROJECT_DIR}/.ai-os/scripts/session-start-hook.sh" SubagentStart'}]}]}}
        self.write(name, json.dumps(old))
        install_hooks(self.root, "claude", self.template("claude"))
        config = json.loads((self.root / name).read_text())
        self.assertEqual(len(config["hooks"]["SubagentStart"]), 1)
        self.assertEqual(config["hooks"]["SubagentStart"][0]["matcher"], "Plan")

    def test_unrecognized_command_does_not_write_host_settings(self):
        template = json.loads(self.template("codex").read_text())
        template["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = "unexpected writer"
        path = self.write("untrusted.json", json.dumps(template))
        with self.assertRaises(ValueError):
            install_hooks(self.root, "codex", path)
        self.assertFalse((self.root / ".codex/hooks.json").exists())

    def test_old_claude_version_cannot_install_fail_open_gates(self):
        with patch("installation.subprocess.run", return_value=CompletedProcess([], 0, "2.1.294", "")):
            with self.assertRaises(ValueError):
                install_hooks(self.root, "claude", self.template("claude"))
        self.assertFalse((self.root / ".claude/settings.json").exists())

    def test_claude_template_cannot_silently_use_powershell_for_bash_wrappers(self):
        template = json.loads(self.template("claude").read_text())
        template["hooks"]["PreToolUse"][0]["hooks"][0]["shell"] = "powershell"
        path = self.write("wrong-shell.json", json.dumps(template))
        with self.assertRaises(ValueError):
            install_hooks(self.root, "claude", path)
        self.assertFalse((self.root / ".claude/settings.json").exists())
