import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = str(ROOT / "skills" / "agent-handoff-manager" / "scripts" / "handoff.py")


def run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True, encoding="utf-8")


class UpstreamStatusTests(unittest.TestCase):
    def test_status_reports_baseline_matching_lock_file_without_network(self):
        r = run("upstream", "status")
        self.assertEqual(0, r.returncode, r.stderr)
        out = json.loads(r.stdout)
        lock = json.loads((ROOT / "upstreams.lock.json").read_text(encoding="utf-8"))
        expected = {s["repo"]: s["adopted_sha"] for s in lock["sources"]}
        got = {s["repo"]: s["adopted_sha"] for s in out["baseline"]}
        self.assertEqual(expected, got)  # embedded copy must never drift from the reviewed lock
        self.assertFalse(out["network_checked"])
        self.assertEqual("design-reference-only", out["adoption"])
        self.assertIn("scripts/check_upstreams.py", out["how_to_check_for_updates"])
        self.assertTrue(out["core_version"])

    def test_status_does_not_need_a_repo_or_write_anything(self):
        r = run("--repo", str(ROOT / "does-not-exist"), "upstream", "status")
        self.assertEqual(0, r.returncode, r.stderr)


if __name__ == "__main__":
    unittest.main()
