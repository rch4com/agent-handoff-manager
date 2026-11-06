"""Crash/interruption behaviour: nothing is lost, doctor sees it, re-running heals it."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

PAYLOAD = {"mission": "m", "next_action": "n"}


class CrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rec = handoff.write(self.root, PAYLOAD)
        self.sid = self.rec["id"]

    def session_file(self, bucket="sessions"):
        return self.root / ".handoffs" / bucket / self.sid / "session.json"

    def test_rename_failure_restores_original_metadata(self):
        before = self.session_file().read_bytes()
        with mock.patch.object(Path, "rename", side_effect=PermissionError("locked by another process")):
            with self.assertRaises(PermissionError):
                handoff.transition(self.root, self.sid, True)
        self.assertEqual(json.loads(before), json.loads(self.session_file().read_bytes()))
        self.assertTrue(handoff.doctor(self.root)["ok"])

    def test_crash_between_metadata_rewrite_and_rename_is_detected_and_rerun_heals(self):
        with mock.patch.object(Path, "rename", side_effect=SystemExit("simulated kill")):
            with self.assertRaises(SystemExit):
                handoff.transition(self.root, self.sid, True)
        stuck = json.loads(self.session_file().read_text(encoding="utf-8"))
        self.assertEqual("archived", stuck["status"])  # metadata already rewritten, folder still in sessions/
        report = handoff.doctor(self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("mismatch" in i for i in report["issues"]))
        self.assertEqual(self.sid, handoff.read_record(handoff.locate(self.root, self.sid))["id"])  # still readable
        handoff.transition(self.root, self.sid, True)  # same command again
        self.assertTrue(handoff.doctor(self.root)["ok"])
        self.assertEqual([self.sid], [r["id"] for r in handoff.list_records(self.root, True)])
        self.assertEqual([], handoff.list_records(self.root))

    def test_crash_during_restore_heals_the_same_way(self):
        handoff.transition(self.root, self.sid, True)
        with mock.patch.object(Path, "rename", side_effect=SystemExit("simulated kill")):
            with self.assertRaises(SystemExit):
                handoff.transition(self.root, self.sid, False)
        self.assertFalse(handoff.doctor(self.root)["ok"])
        handoff.transition(self.root, self.sid, False)
        self.assertTrue(handoff.doctor(self.root)["ok"])
        self.assertEqual([self.sid], [r["id"] for r in handoff.list_records(self.root)])

    def test_crash_during_new_write_leaves_no_half_record_visible_as_valid(self):
        with mock.patch.object(handoff, "atomic_json", side_effect=SystemExit("simulated kill")):
            with self.assertRaises(SystemExit):
                handoff.write(self.root, dict(PAYLOAD, mission="second"))
        # lock is released even on SystemExit, existing record untouched, new write works
        self.assertFalse((self.root / ".handoffs" / ".write.lock").exists())
        self.assertEqual("m", handoff.read_record(handoff.locate(self.root, self.sid))["payload"]["mission"])
        issues = handoff.doctor(self.root)["issues"]
        self.assertTrue(any("Unreadable session record" in i for i in issues), issues)  # empty folder is reported
        self.assertEqual(2, handoff.write(self.root, PAYLOAD, self.sid, 1)["revision"])

    def test_stale_lock_is_reported_with_owner_details_and_never_auto_deleted(self):
        lock = self.root / ".handoffs" / ".write.lock"
        lock.write_text("pid=999999 time=2026-01-01T00:00:00Z\n", encoding="utf-8")
        with mock.patch.object(handoff.time, "monotonic", side_effect=[0, 0, 100, 100]), mock.patch.object(handoff.time, "sleep"):
            with self.assertRaises(handoff.HandoffError) as ctx:
                handoff.write(self.root, PAYLOAD)
        self.assertIn("pid=999999", str(ctx.exception))
        self.assertTrue(lock.exists())
        issues = handoff.doctor(self.root)["issues"]
        self.assertTrue(any("pid=999999" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
