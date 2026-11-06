"""Acceptance #3: simultaneous writers never overwrite each other (separate OS processes)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts" / "handoff.py")


def spawn(root, payload_path, *extra):
    return subprocess.Popen([sys.executable, "-I", SCRIPT, "--repo", str(root), "write", "--payload", str(payload_path), *extra],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")


class ConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.payloads = []
        for i in range(6):
            f = self.root.parent / f"{self.root.name}-p{i}.json"
            f.write_text(json.dumps({"agent": "other", "mission": f"writer {i}", "next_action": "n"}), encoding="utf-8")
            self.addCleanup(f.unlink)
            self.payloads.append(f)

    def test_parallel_new_sessions_all_saved_with_unique_ids(self):
        procs = [spawn(self.root, f) for f in self.payloads]
        results = [(p.wait(timeout=60), *p.communicate()) for p in procs]
        for code, out, err in results:
            self.assertEqual(0, code, err)
        ids = [json.loads(out)["id"] for _, out, _ in results]
        self.assertEqual(6, len(set(ids)))
        sessions = sorted(d.name for d in (self.root / ".handoffs" / "sessions").iterdir())
        self.assertEqual(sorted(ids), sessions)
        missions = sorted(json.loads((self.root / ".handoffs" / "sessions" / i / "session.json").read_text(encoding="utf-8"))["payload"]["mission"] for i in ids)
        self.assertEqual([f"writer {i}" for i in range(6)], missions)
        self.assertFalse((self.root / ".handoffs" / ".write.lock").exists())

    def test_parallel_updates_of_same_revision_exactly_one_wins(self):
        first = subprocess.run([sys.executable, "-I", SCRIPT, "--repo", str(self.root), "write", "--payload", str(self.payloads[0])],
                               capture_output=True, text=True, encoding="utf-8", check=True)
        ident = json.loads(first.stdout)["id"]
        procs = [spawn(self.root, f, "--id", ident, "--expected-revision", "1") for f in self.payloads[1:]]
        codes = []
        for p in procs:
            codes.append(p.wait(timeout=60))
            p.communicate()
        self.assertEqual(1, codes.count(0), codes)
        self.assertEqual(4, codes.count(2), codes)
        record = json.loads((self.root / ".handoffs" / "sessions" / ident / "session.json").read_text(encoding="utf-8"))
        self.assertEqual(2, record["revision"])


if __name__ == "__main__":
    unittest.main()
