import json
import sys
import subprocess
from pathlib import Path
import unittest
from unittest.mock import patch

from workspace import Workspace
from memory import add_entry, amend, encoded, promote, recover, validate_evidence, verify
from storage import RUNTIME, atomic_write, canonical_json, digest


class MemoryTests(Workspace):

    def prepare(self):
        task_name = ".ai-os/memory/tasks/example.md"
        task = self.write(task_name, "Branch: main\nActive plan: memory/plans/open.md\nTODO: keep this\n")
        self.write("src.py", "value = 1\n")
        self.write("note.md", "The module exports value = 1.")
        entry = add_entry(self.root, task_name, "note.md")
        evidence = verify(self.root, ["src.py"], [sys.executable, "-c", "assert open('src.py').read().strip() == 'value = 1'"])
        proposal = {"task": task_name, "task_sha256": entry["task_sha256"], "promotions": [
            {"entry_id": entry["entry_id"], "accepted": True, "evidence": evidence["evidence"],
             "destination": ".ai-os/memory/semantic/knowledge/example.md", "destination_sha256": None}]}
        self.write("proposal.json", json.dumps(proposal))
        return task, proposal

    def test_selective_drain_preserves_unresolved_work_and_plan_pointer(self):
        task, proposal = self.prepare()
        promote(self.root, "proposal.json")
        self.assertEqual(task.read_text(), "Branch: main\nActive plan: memory/plans/open.md\nTODO: keep this\n\n\n")
        destination = self.root / proposal["promotions"][0]["destination"]
        self.assertIn("The module exports", destination.read_text())
        self.assertIn("AIOS-PROVENANCE", destination.read_text())
        self.assertFalse((self.root / RUNTIME / "transaction.json").exists())

    def test_stale_failed_and_tampered_evidence_is_rejected(self):
        _, proposal = self.prepare()
        name = proposal["promotions"][0]["evidence"]
        self.write("src.py", "value = 2\n")
        with self.assertRaises(ValueError):
            validate_evidence(self.root, name)
        failed = verify(self.root, ["src.py"], [sys.executable, "-c", "raise SystemExit(1)"])
        self.assertFalse(failed["passed"])
        with self.assertRaises(ValueError):
            validate_evidence(self.root, failed["evidence"])
        path = self.root / failed["evidence"]
        record = json.loads(path.read_text())
        record["passed"] = True
        path.write_bytes(canonical_json(record))
        with self.assertRaises(ValueError):
            validate_evidence(self.root, failed["evidence"])

    def test_outdated_proposal_and_unresolved_entry_do_not_write(self):
        task, proposal = self.prepare()
        original = task.read_bytes()
        task.write_bytes(original + b"More notes\n")
        with self.assertRaises(ValueError):
            promote(self.root, "proposal.json")
        task.write_bytes(original.replace(b"The module", b"TODO: The module"))
        proposal["task_sha256"] = digest(task.read_bytes())
        self.write("proposal.json", json.dumps(proposal))
        with self.assertRaises(ValueError):
            promote(self.root, "proposal.json")
        self.assertFalse((self.root / proposal["promotions"][0]["destination"]).exists())

    def test_partial_write_failure_rolls_back_exact_bytes(self):
        task, proposal = self.prepare()
        original = task.read_bytes()
        def fail_task(path, raw):
            if path == task and raw != original:
                raise OSError("simulated interrupted write")
            atomic_write(path, raw)
        with patch("memory.atomic_write", side_effect=fail_task):
            with self.assertRaises(OSError):
                promote(self.root, "proposal.json")
        self.assertEqual(original, task.read_bytes())
        self.assertFalse((self.root / proposal["promotions"][0]["destination"]).exists())

    def test_recovery_refuses_outside_edits_and_context_blocks_pending_journal(self):
        from context import build_pack
        path = self.write(".ai-os/memory/tasks/example.md", "outside edit")
        journal = {"format": "AIOS-transaction/1", "state": "prepared", "files": [
            {"path": ".ai-os/memory/tasks/example.md", "before": encoded(b"old"), "after": encoded(b"new")}]}
        self.write(RUNTIME + "/transaction.json", json.dumps(journal))
        with self.assertRaises(ValueError):
            build_pack(self.root)
        with self.assertRaises(ValueError):
            recover(self.root)
        self.assertEqual(path.read_bytes(), b"outside edit")
        path.write_bytes(b"new")
        self.assertTrue(recover(self.root)["recovered"])
        self.assertEqual(path.read_bytes(), b"old")

    def test_dependency_changes_during_check_are_not_accepted(self):
        self.write("src.py", "old")
        result = verify(self.root, ["src.py"], [sys.executable, "-c", "open('src.py','w').write('new')"])
        self.assertFalse(result["passed"])

    def test_failed_verification_cli_returns_nonzero_with_inspectable_evidence(self):
        self.write("src.py", "current dependency")
        cli = Path(__file__).resolve().parents[1] / ".ai-os/scripts/ai_os.py"
        result = subprocess.run([sys.executable, "-B", str(cli), "--project", str(self.root),
                                 "verify", "--file", "src.py", "--", sys.executable, "-c", "raise SystemExit(7)"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["returncode"], 7)
        self.assertFalse(record["passed"])
        self.assertTrue((self.root / record["evidence"]).is_file())

    def test_reviewed_amendment_and_retraction_keep_other_memory(self):
        self.write("src.py", "value=2")
        evidence = verify(self.root, ["src.py"], [sys.executable, "-c", "assert open('src.py').read() == 'value=2'"])
        name = ".ai-os/memory/semantic/knowledge/example.md"
        destination = self.write(name, "Unrelated knowledge\nValue is 1.\n")
        self.write("correction.md", "Value is 2.")
        proposal = {"destination": name, "destination_sha256": digest(destination.read_bytes()),
                    "accepted": True, "evidence": evidence["evidence"], "old_text": "Value is 1.",
                    "replacement_file": "correction.md"}
        self.write("amendment.json", json.dumps(proposal))
        amend(self.root, "amendment.json")
        self.assertIn("Unrelated knowledge\nValue is 2.", destination.read_text())
        with self.assertRaises(ValueError):
            amend(self.root, "amendment.json")
        proposal.update(destination_sha256=digest(destination.read_bytes()), old_text="Value is 2.", replacement_file=None)
        self.write("amendment.json", json.dumps(proposal))
        amend(self.root, "amendment.json")
        self.assertNotIn("Value is 2.", destination.read_text())
        self.assertIn("Unrelated knowledge", destination.read_text())
        log = self.root / ".ai-os/memory/episodic/decisions.jsonl"
        for line in log.read_text().splitlines():
            self.assertEqual(set(json.loads(line)), {"ts", "type", "what", "why", "files"})

    def test_knowledge_index_can_use_the_same_transaction(self):
        _, proposal = self.prepare()
        index = self.write(".ai-os/memory/semantic/project_knowledge.md", "# Existing index\n")
        proposal["promotions"][0].update(destination=".ai-os/memory/semantic/project_knowledge.md",
                                          destination_sha256=digest(index.read_bytes()))
        self.write("proposal.json", json.dumps(proposal))
        promote(self.root, "proposal.json")
        self.assertTrue(index.read_text().startswith("# Existing index\n"))
        self.assertIn("The module exports", index.read_text())
