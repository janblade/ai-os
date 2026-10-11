import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".ai-os/scripts"))

from context import build_pack, create_task, diff_packs, load_snapshot, render_pack, save_snapshot, task_key, task_path
from storage import canonical_json, workspace_path


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write(".ai-os/BOOT.md", "Governance\n")
        self.write(".ai-os/manifest.json", json.dumps({"ai_os_version": "test", "installed_skills": ["test.sk"]}))
        self.write(".ai-os/registry/index.json", json.dumps({"skills": [{"id": "test.sk", "entrypoint": "registry/test.sk/SKILL.md"}]}))
        self.write(".ai-os/registry/test.sk/SKILL.md", "Test procedure")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def test_stable_selection_order_and_byte_identical_render(self):
        self.write("a.md", "A\b\f\n")
        self.write("z.md", "Z")
        before = build_pack(self.root, "main", ["test.sk"], ["z.md", "a.md", "a.md"])
        after = build_pack(self.root, "main", ["test.sk"], ["a.md", "z.md"])
        self.assertEqual(canonical_json(before), canonical_json(after))
        self.assertEqual(render_pack(before), render_pack(after))
        self.assertEqual([item["source"] for item in before["items"]],
                         [".ai-os/BOOT.md", ".ai-os/registry/test.sk/SKILL.md", "a.md", "z.md"])

    def test_branch_collisions_and_windows_reserved_names_are_distinct(self):
        names = ["feature/a", "feature_a", "FEATURE/A", "main", "MAIN", "CON"]
        self.assertEqual(len(names), len({task_key(name).casefold() for name in names}))
        for name in names:
            self.assertEqual(create_task(self.root, name), task_path(self.root, name))

    def test_legacy_task_requires_matching_original_branch(self):
        legacy = self.write(".ai-os/memory/tasks/feature_a.md", "Branch: feature/a\nNotes")
        self.assertEqual(task_path(self.root, "feature/a"), legacy)
        with self.assertRaises(ValueError):
            task_path(self.root, "feature_a")
        legacy.write_text("No identity", encoding="utf-8")
        with self.assertRaises(ValueError):
            task_path(self.root, "feature/a")

    def test_task_and_active_plan_are_selected(self):
        task = create_task(self.root, "main")
        with task.open("a", encoding="utf-8") as stream:
            stream.write("Active plan: `.ai-os/memory/plans/example.md` (0/1)\n")
        self.write(".ai-os/memory/plans/example.md", "[ ] Deliver")
        pack = build_pack(self.root, "main")
        self.assertEqual(pack["items"][-1]["source"], ".ai-os/memory/plans/example.md")

    def test_snapshot_replay_survives_changed_sources_and_detects_tampering(self):
        self.write("a.md", "old")
        old = build_pack(self.root, "main", files=["a.md"])
        snapshot = save_snapshot(self.root, old)
        self.write("a.md", "new")
        self.assertEqual(render_pack(load_snapshot(snapshot)), render_pack(old))
        new = build_pack(self.root, "main", files=["a.md"])
        self.assertEqual(diff_packs(old, new)["changed"][0]["id"], "a.md")
        changed = json.loads(snapshot.read_text())
        changed["items"][0]["content"] = "Tampered"
        snapshot.write_text(json.dumps(changed))
        with self.assertRaises(ValueError):
            load_snapshot(snapshot)

    def test_invalid_inputs_and_missing_governance_fail_closed(self):
        for name in ["../outside", ".env", ".ai-os/memory/runtime/private.json"]:
            with self.assertRaises((ValueError, OSError)):
                build_pack(self.root, "main", files=[name])
        with self.assertRaises(ValueError):
            build_pack(self.root, "main", skills=["unknown"])
        (self.root / ".ai-os/BOOT.md").unlink()
        with self.assertRaises(OSError):
            build_pack(self.root, "main")

    def test_symlink_traversal_is_rejected(self):
        target = self.write("target.md", "data")
        link = self.root / "link.md"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("Host does not permit creating symlinks")
        with self.assertRaises(ValueError):
            workspace_path(self.root, "link.md")


if __name__ == "__main__":
    unittest.main()
