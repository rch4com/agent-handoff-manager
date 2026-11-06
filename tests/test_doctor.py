import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

PAYLOAD = {"mission": "m", "next_action": "n"}
LEGACY = Path(__file__).resolve().parent / "fixtures" / "legacy" / "2026-07-09-1530-pdf-export-fix.md"


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def sessions(self):
        return self.root / ".handoffs" / "sessions"

    def test_uninitialized_store_reports_runtime_info_and_legacy_hint(self):
        (self.root / ".handoffs").mkdir()
        shutil.copyfile(LEGACY, self.root / ".handoffs" / LEGACY.name)
        shutil.rmtree(self.root / ".handoffs" / "sessions", ignore_errors=True)
        out = handoff.doctor(self.root)
        self.assertFalse(out["ok"])
        self.assertTrue(any("not initialized" in i for i in out["issues"]))
        self.assertTrue(out["info"]["python_ok"])
        self.assertEqual(1, out["info"]["legacy_unimported"])

    def test_healthy_store_info_counts(self):
        handoff.write(self.root, PAYLOAD)
        out = handoff.doctor(self.root)
        self.assertTrue(out["ok"], out)
        self.assertEqual(1, out["info"]["active_sessions"])
        self.assertEqual(0, out["info"]["archived_sessions"])
        self.assertIn("git_available", out["info"])

    def test_leftover_pending_file_inside_session_is_reported(self):
        rec = handoff.write(self.root, PAYLOAD)
        (self.sessions() / rec["id"] / ".pending-abc").write_text("x", encoding="utf-8")
        out = handoff.doctor(self.root)
        self.assertFalse(out["ok"])
        self.assertTrue(any(".pending-abc" in i for i in out["issues"]))

    def test_empty_session_dir_after_crash_is_reported(self):
        handoff.init(self.root)
        (self.sessions() / "20261107T000000Z-aaaaaaaaaaaa").mkdir()
        out = handoff.doctor(self.root)
        self.assertFalse(out["ok"])
        self.assertTrue(any("20261107T000000Z-aaaaaaaaaaaa" in i for i in out["issues"]))

    def test_newer_schema_version_is_flagged_not_misread(self):
        rec = handoff.write(self.root, PAYLOAD)
        f = self.sessions() / rec["id"] / "session.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        data["schema_version"] = 2
        f.write_text(json.dumps(data), encoding="utf-8")
        out = handoff.doctor(self.root)
        self.assertFalse(out["ok"])
        self.assertTrue(any("Invalid session record" in i for i in out["issues"]))

    def test_stray_file_in_bucket_is_reported(self):
        handoff.init(self.root)
        (self.sessions() / "notes.txt").write_text("x", encoding="utf-8")
        out = handoff.doctor(self.root)
        self.assertTrue(any("notes.txt" in i for i in out["issues"]))

    def test_symlinked_store_is_an_issue_not_a_crash(self):
        with tempfile.TemporaryDirectory() as other:
            try:
                os.symlink(other, self.root / ".handoffs", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            out = handoff.doctor(self.root)
            self.assertFalse(out["ok"])
            self.assertTrue(any("Symlink" in i for i in out["issues"]))


if __name__ == "__main__":
    unittest.main()
