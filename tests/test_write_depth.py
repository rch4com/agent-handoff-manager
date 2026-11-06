import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

MINIMAL = {"mission": "m", "next_action": "n"}
RICH = dict(MINIMAL, in_progress=["x"], failed_attempts=[], validation=[{"command": "pytest", "result": "not_run"}])
EXHAUSTIVE = dict(RICH, acceptance_criteria=["a"], completed=[], blocked=[], decisions=[], changed_files=[])


class DepthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, payload, depth="auto"):
        return handoff.write(self.root, payload, depth=depth)

    def test_auto_picks_highest_satisfied_depth(self):
        self.assertEqual("minimal", self.write(MINIMAL)["depth"])
        self.assertEqual("rich", self.write(RICH)["depth"])
        self.assertEqual("exhaustive", self.write(EXHAUSTIVE)["depth"])

    def test_explicit_depth_rejects_underfilled_payload_and_saves_nothing(self):
        with self.assertRaisesRegex(handoff.HandoffError, "rich.*validation"):
            self.write(MINIMAL, "rich")
        with self.assertRaisesRegex(handoff.HandoffError, "exhaustive.*acceptance_criteria"):
            self.write(RICH, "exhaustive")
        self.assertEqual([], handoff.list_records(self.root))

    def test_explicit_depth_accepts_sufficient_payload_and_records_it(self):
        self.assertEqual("rich", self.write(EXHAUSTIVE, "rich")["depth"])
        self.assertEqual("minimal", self.write(RICH, "minimal")["depth"])

    def test_rich_requires_explicit_failed_attempts_key_even_if_empty(self):
        bad = {k: v for k, v in RICH.items() if k != "failed_attempts"}
        with self.assertRaisesRegex(handoff.HandoffError, "failed_attempts"):
            self.write(bad, "rich")

    def test_unknown_depth_rejected(self):
        with self.assertRaises(handoff.HandoffError):
            self.write(MINIMAL, "huge")

    def test_cli_depth_flag_and_default_auto(self):
        path = self.root / "p.json"
        path.write_text(json.dumps(RICH), encoding="utf-8")
        base = [sys.executable, "-I", str(Path(handoff.__file__).resolve()), "--repo", str(self.root), "write", "--payload", str(path)]
        r = subprocess.run(base, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual("rich", json.loads(r.stdout)["depth"])
        r = subprocess.run(base + ["--depth", "exhaustive"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(2, r.returncode)
        self.assertIn("exhaustive", r.stderr)

    def test_update_keeps_depth_rule(self):
        first = self.write(RICH)
        with self.assertRaises(handoff.HandoffError):
            handoff.write(self.root, MINIMAL, first["id"], 1, depth="rich")
        self.assertEqual(1, handoff.read_record(handoff.locate(self.root, first["id"]))["revision"])


if __name__ == "__main__":
    unittest.main()
