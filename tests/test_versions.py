"""Tag/Release consistency: core VERSION, SKILL, both plugin manifests and CHANGELOG must agree."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "agent-handoff-manager" / "scripts"))
import handoff


class VersionConsistencyTests(unittest.TestCase):
    def base(self):
        return handoff.VERSION.split("-")[0]

    def test_manifests_match_core_version(self):
        paths = [".claude-plugin/plugin.json", "plugin.json"]
        for rel in paths:
            self.assertEqual(self.base(), json.loads((ROOT / rel).read_text(encoding="utf-8"))["version"], rel)
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        copilot = json.loads((ROOT / ".github/plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(self.base(), claude["plugins"][0]["version"])
        self.assertEqual(self.base(), copilot["plugins"][0]["version"])
        self.assertEqual(self.base(), copilot["metadata"]["version"])

    def test_changelog_top_entry_is_current_version(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        first = re.search(r"^## \[(\d+\.\d+\.\d+[^\]]*)\]", text, re.M)
        self.assertIsNotNone(first)
        self.assertEqual(handoff.VERSION, first.group(1))

    def test_marketplaces_do_not_share_a_name_or_format(self):
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        copilot = json.loads((ROOT / ".github/plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertNotEqual(claude["name"], copilot["name"])
        self.assertIsInstance(claude["plugins"][0]["source"], str)   # Claude: path string
        self.assertIsInstance(copilot["plugins"][0]["source"], dict)  # Copilot: source object
        self.assertIn("$schema", json.loads((ROOT / "plugin.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
