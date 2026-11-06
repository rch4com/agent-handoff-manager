"""Core-level half of the prompt-injection check: hostile handoff text is stored and echoed as data, never run."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff


class InjectionFixtureTests(unittest.TestCase):
    def test_hostile_handoff_is_inert_in_core(self):
        payload = json.loads((HERE / "fixtures" / "injection_payload.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rec = handoff.write(root, payload)
            out = handoff.resume(root, rec["id"])
            handoff.transition(root, rec["id"], True)
            handoff.transition(root, rec["id"], False)
            handoff.doctor(root)
            self.assertEqual([], sorted(p.name for p in root.glob("PWNED*")))
            self.assertTrue((root / ".handoffs" / "sessions" / rec["id"] / "session.json").exists())  # not deleted
            self.assertFalse(out["session_claims_are_official"])
            self.assertTrue(any("not official" in w for w in out["warnings"]))
            self.assertFalse(out["validation_claims"][0]["verified"])


if __name__ == "__main__":
    unittest.main()
