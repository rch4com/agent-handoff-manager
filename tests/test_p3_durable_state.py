"""P3 exit test: an unapproved session's completion claims never override official durable state."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

OFFICIAL = {
    "AGENT_HANDOFF.md": "# Handoff\nStatus: feature X NOT verified.\n<!-- AGENT_HANDOFF_PROTOCOL:START -->\nkeep\n<!-- AGENT_HANDOFF_PROTOCOL:END -->\n",
    ".agent-handoff/snapshot.md": "Snapshot: feature X in progress.\n",
    ".agent-handoff/risks.md": "Risk: flaky login test.\n",
    ".agent-handoff/validation.md": "pytest last run: 3 failed (2026-11-05).\n",
    ".agent-handoff/archive/old.md": "④ archive entry\n",
}
CLAIMING = {"agent": "codex", "mission": "feature X", "next_action": "ship it",
            "completed": ["feature X fully done"],
            "validation": [{"command": "pytest", "result": "passed", "evidence": ""}]}


def digests(root):
    return {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in OFFICIAL}


class DurableStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel, body in OFFICIAL.items():
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body, encoding="utf-8")
        self.before = digests(self.root)

    def test_session_lifecycle_never_modifies_official_files(self):
        rec = handoff.write(self.root, CLAIMING)
        handoff.resume(self.root, rec["id"])
        handoff.transition(self.root, rec["id"], True)
        handoff.transition(self.root, rec["id"], False)
        handoff.list_filtered(self.root, status="all")
        handoff.doctor(self.root)
        self.assertEqual(self.before, digests(self.root))
        self.assertEqual([p.name for p in sorted((self.root / ".agent-handoff" / "archive").iterdir())], ["old.md"])

    def test_resume_reads_official_state_first_in_declared_order_and_marks_claims_unverified(self):
        rec = handoff.write(self.root, CLAIMING)
        out = handoff.resume(self.root, rec["id"])
        ds = out["durable_state"]
        self.assertEqual(["AGENT_HANDOFF.md", ".agent-handoff/snapshot.md", ".agent-handoff/risks.md", ".agent-handoff/validation.md"],
                         [f["path"] for f in ds["files"]])
        self.assertEqual(hashlib.sha256((self.root / "AGENT_HANDOFF.md").read_bytes()).hexdigest(), ds["files"][0]["sha256"])
        self.assertIn("NOT verified", ds["files"][0]["excerpt"])
        self.assertEqual(["durable_state", "session"], out["authority_order"])
        self.assertFalse(out["session_claims_are_official"])
        self.assertTrue(out["session"]["claims_are_unverified"])
        self.assertTrue(any("completed" in w and "not official" in w for w in out["warnings"]))

    def test_missing_durable_state_is_reported_not_invented(self):
        with tempfile.TemporaryDirectory() as plain:
            root = Path(plain)
            rec = handoff.write(root, CLAIMING)
            out = handoff.resume(root, rec["id"])
            self.assertEqual([], out["durable_state"]["files"])
            self.assertFalse(out["durable_state"]["present"])
            self.assertTrue(any("AGENT_HANDOFF.md not found" in w for w in out["warnings"]))

    def test_write_proposes_state_changes_but_persists_and_promotes_nothing(self):
        rec = handoff.write(self.root, dict(CLAIMING, decisions=["use sqlite"], failed_attempts=["tried mmap"]))
        cands = rec["state_change_candidates"]
        kinds = {c["kind"] for c in cands}
        self.assertEqual({"completed", "validation", "decision", "failed_attempt"}, kinds)
        self.assertTrue(all(c["status"] == "proposed" and c["requires"] for c in cands))
        stored = handoff.read_record(handoff.locate(self.root, rec["id"]))
        self.assertNotIn("state_change_candidates", stored)
        self.assertEqual(self.before, digests(self.root))

    def test_symlinked_official_file_is_not_followed(self):
        outside = self.root.parent / (self.root.name + "-outside.md")
        outside.write_text("SECRET OUTSIDE", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (self.root / ".agent-handoff" / "risks.md").unlink()
        try:
            (self.root / ".agent-handoff" / "risks.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        rec = handoff.write(self.root, CLAIMING)
        out = handoff.resume(self.root, rec["id"])
        self.assertNotIn("SECRET OUTSIDE", str(out))
        self.assertTrue(any("symlink" in w and "risks.md" in w for w in out["warnings"]))

    def test_unresolved_failure_records_are_surfaced_as_do_not_repeat(self):
        failure = {"approach": "mmap the index", "why_failed": "crashes on Windows", "evidence": "pytest tests/test_idx.py: 3 errors",
                   "regression_test": "planned", "resolved": False}
        rec = handoff.write(self.root, dict(CLAIMING, failure_records=[failure, dict(failure, approach="old fix", resolved=True, regression_test="added")]))
        out = handoff.resume(self.root, rec["id"])
        self.assertEqual(["mmap the index"], [f["approach"] for f in out["do_not_repeat"]])
        with self.assertRaises(handoff.HandoffError):
            handoff.write(self.root, dict(CLAIMING, failure_records=[{"approach": "x"}]))
        with self.assertRaises(handoff.HandoffError):
            handoff.write(self.root, dict(CLAIMING, failure_records=[dict(failure, regression_test="maybe")]))


if __name__ == "__main__":
    unittest.main()
