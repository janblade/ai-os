import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".ai-os/scripts"))


class Workspace(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.addCleanup(self.temporary.cleanup)
        self.write(".ai-os/BOOT.md", "Governance\n")
        self.write(".ai-os/manifest.json", json.dumps({"ai_os_version": "test", "installed_skills": ["test.sk"]}))
        self.write(".ai-os/registry/index.json", json.dumps({"skills": [{"id": "test.sk", "entrypoint": "registry/test.sk/SKILL.md"}]}))
        self.write(".ai-os/registry/test.sk/SKILL.md", "Test procedure")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path
