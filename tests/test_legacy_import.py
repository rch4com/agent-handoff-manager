import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "legacy" / "2026-07-09-1530-pdf-export-fix.md"


class LegacyImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".handoffs").mkdir()
        self.legacy = self.root / ".handoffs" / FIXTURE.name
        shutil.copyfile(FIXTURE, self.legacy)
        self.original = self.legacy.read_bytes()

    def test_import_is_lossless_and_leaves_original_untouched(self):
        result = handoff.import_legacy(self.root)
        self.assertEqual(1, len(result["imported"]))
        self.assertEqual(self.original, self.legacy.read_bytes())
        records = handoff.list_records(self.root)
        self.assertEqual(1, len(records))
        rec = records[0]
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), rec["legacy_import"]["source_sha256"])
        self.assertEqual(self.original.decode("utf-8"), rec["legacy_import"]["original_text"])
        self.assertEqual(FIXTURE.name, rec["legacy_import"]["source_file"])
        p = rec["payload"]
        self.assertEqual("claude-code", p["agent"])
        self.assertIn("PDF export", p["mission"])
        self.assertIn("render.py:88", p["next_action"])
        self.assertEqual(["reproduced the bug with a 12-column table"], p["completed"])
        self.assertEqual(["patching `render_table` (half done)"], p["in_progress"])
        self.assertEqual(["waiting for the font license answer"], p["blocked"])
        self.assertEqual(["src/pdf/render.py"], [c["path"] for c in p["changed_files"]])
        self.assertEqual("open", rec["status"])
        self.assertTrue(rec["claims_are_unverified"])
        self.assertTrue(handoff.doctor(self.root)["ok"])
        self.assertIn("session", handoff.resume(self.root, rec["id"]))

    def test_import_is_idempotent(self):
        handoff.import_legacy(self.root)
        again = handoff.import_legacy(self.root)
        self.assertEqual([], again["imported"])
        self.assertEqual("already_imported", again["skipped"][0]["reason"])
        self.assertEqual(1, len(handoff.list_records(self.root)))

    def test_dry_run_writes_nothing(self):
        result = handoff.import_legacy(self.root, dry_run=True)
        self.assertEqual(1, len(result["would_import"]))
        self.assertFalse((self.root / ".handoffs" / "sessions").exists())

    def test_secret_bearing_file_is_skipped_not_copied(self):
        bad = self.root / ".handoffs" / "2026-07-09-1600-leak.md"
        bad.write_text(FIXTURE.read_text(encoding="utf-8") + "\napi_key = abcdefgh12345678\n", encoding="utf-8")
        result = handoff.import_legacy(self.root)
        self.assertEqual(1, len(result["imported"]))
        self.assertEqual("possible_credential", result["skipped"][0]["reason"])
        self.assertNotIn("abcdefgh12345678", json.dumps(handoff.list_records(self.root)))

    def test_non_handoff_markdown_and_symlinks_are_skipped(self):
        (self.root / ".handoffs" / "notes.md").write_text("# random notes\n", encoding="utf-8")
        link = self.root / ".handoffs" / "2026-07-09-1700-link.md"
        try:
            link.symlink_to(self.legacy)
        except (OSError, NotImplementedError):
            pass
        result = handoff.import_legacy(self.root)
        reasons = {s["file"]: s["reason"] for s in result["skipped"]}
        self.assertEqual("not_a_handoff_doc", reasons["notes.md"])
        if link.is_symlink():
            self.assertEqual("symlink", reasons[link.name])
        self.assertEqual(1, len(handoff.list_records(self.root)))

    def test_existing_upstream4_and_agent_rule_files_are_never_touched(self):
        # Acceptance #5: repeated init/import must not alter or duplicate pre-existing files.
        protected = {
            "AGENT_HANDOFF.md": "# durable state\n<!-- AGENT_HANDOFF_PROTOCOL:START -->\nkeep\n<!-- AGENT_HANDOFF_PROTOCOL:END -->\n",
            ".agent-handoff/snapshot.md": "snapshot 한글\n",
            "AGENTS.md": "# my rules\n",
            "CLAUDE.md": "# claude rules\n",
            ".github/copilot-instructions.md": "# copilot\n",
        }
        for rel, body in protected.items():
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body, encoding="utf-8")
        for _ in range(3):
            handoff.init(self.root)
            handoff.import_legacy(self.root)
        for rel, body in protected.items():
            self.assertEqual(body, (self.root / rel).read_text(encoding="utf-8"), rel)
        self.assertEqual(1, len(handoff.list_records(self.root)))

    def test_cli_import_legacy(self):
        script = str(Path(handoff.__file__).resolve())
        r = subprocess.run([sys.executable, "-I", script, "--repo", str(self.root), "import-legacy", "--dry-run"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(1, len(json.loads(r.stdout)["would_import"]))
        r = subprocess.run([sys.executable, "-I", script, "--repo", str(self.root), "import-legacy"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(1, len(json.loads(r.stdout)["imported"]))


if __name__ == "__main__":
    unittest.main()
