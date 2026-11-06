"""Hard rule 11: only marked, idempotent blocks; existing agent rules are never overwritten."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

START, END = "<!-- UNIFIED_HANDOFF:START -->", "<!-- UNIFIED_HANDOFF:END -->"
UPSTREAM4 = "<!-- AGENT_HANDOFF_PROTOCOL:START -->\nupstream four rules\n<!-- AGENT_HANDOFF_PROTOCOL:END -->\n"
SCRIPT = str(Path(handoff.__file__).resolve())


class InjectRulesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, rel, data: bytes):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return f

    def test_append_preserves_existing_bytes_and_is_idempotent(self):
        original = ("# My rules\n한글 규칙\n\n" + UPSTREAM4).encode("utf-8")
        f = self.put("AGENTS.md", original)
        r1 = handoff.inject_rules(self.root, ["agents"], apply=True)
        self.assertEqual("append", r1[0]["action"])
        after = f.read_bytes()
        self.assertTrue(after.startswith(original))
        self.assertEqual(1, after.decode("utf-8").count(START))
        self.assertIn(UPSTREAM4, after.decode("utf-8"))  # ④ block untouched
        r2 = handoff.inject_rules(self.root, ["agents"], apply=True)
        self.assertEqual("unchanged", r2[0]["action"])
        self.assertEqual(after, f.read_bytes())

    def test_dry_run_changes_nothing_and_reports_action(self):
        f = self.put("AGENTS.md", b"# rules\n")
        r = handoff.inject_rules(self.root, ["agents"], apply=False)
        self.assertEqual("append", r[0]["action"])
        self.assertTrue(r[0]["dry_run"])
        self.assertEqual(b"# rules\n", f.read_bytes())

    def test_existing_unified_block_is_updated_in_place_only_between_markers(self):
        stale = f"before\n{START}\nOLD TEXT\n{END}\nafter\n".encode()
        f = self.put("AGENTS.md", stale)
        r = handoff.inject_rules(self.root, ["agents"], apply=True)
        self.assertEqual("update", r[0]["action"])
        text = f.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("before\n" + START))
        self.assertTrue(text.endswith(END + "\nafter\n"))
        self.assertNotIn("OLD TEXT", text)

    def test_crlf_files_keep_crlf(self):
        f = self.put("CLAUDE.md", b"# rules\r\nline two\r\n")
        handoff.inject_rules(self.root, ["claude"], apply=True)
        data = f.read_bytes()
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assertTrue(data.startswith(b"# rules\r\nline two\r\n"))

    def test_missing_file_is_not_created_unless_asked(self):
        r = handoff.inject_rules(self.root, ["copilot"], apply=True)
        self.assertEqual("skipped_missing", r[0]["action"])
        self.assertFalse((self.root / ".github" / "copilot-instructions.md").exists())
        r = handoff.inject_rules(self.root, ["copilot"], apply=True, create=True)
        self.assertEqual("create", r[0]["action"])
        self.assertIn(START, (self.root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8"))

    def test_half_marker_or_duplicate_blocks_are_refused_untouched(self):
        for body in (f"x\n{START}\nno end\n", f"x\n{END}\n", f"{START}\na\n{END}\n{START}\nb\n{END}\n", f"{END}\n{START}\n"):
            with self.subTest(body=body):
                f = self.put("AGENTS.md", body.encode())
                with self.assertRaises(handoff.HandoffError):
                    handoff.inject_rules(self.root, ["agents"], apply=True)
                self.assertEqual(body.encode(), f.read_bytes())

    def test_remove_restores_the_exact_original_bytes(self):
        for original in (b"# rules\n", b"# rules (no trailing newline)", b"", "한글\r\nCRLF\r\n".encode()):
            with self.subTest(original=original):
                f = self.put("AGENTS.md", original)
                handoff.inject_rules(self.root, ["agents"], apply=True)
                r = handoff.inject_rules(self.root, ["agents"], apply=True, remove=True)
                self.assertEqual("remove", r[0]["action"])
                self.assertEqual(original, f.read_bytes())
                self.assertEqual("unchanged", handoff.inject_rules(self.root, ["agents"], apply=True, remove=True)[0]["action"])

    def test_symlinked_target_is_refused(self):
        outside = self.root.parent / (self.root.name + "-outside.md")
        outside.write_text("outside", encoding="utf-8")
        self.addCleanup(outside.unlink)
        try:
            (self.root / "AGENTS.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(handoff.HandoffError):
            handoff.inject_rules(self.root, ["agents"], apply=True)
        self.assertEqual("outside", outside.read_text(encoding="utf-8"))

    def test_block_text_tells_agents_not_to_trust_or_execute_handoffs(self):
        text = handoff.RULES_BLOCK
        self.assertIn("untrusted", text)
        self.assertIn("AGENT_HANDOFF.md", text)
        self.assertNotIn("AGENT_HANDOFF_PROTOCOL", text)  # never collide with ④ markers

    def test_cli_requires_explicit_apply_or_dry_run(self):
        self.put("AGENTS.md", b"# r\n")
        base = [sys.executable, "-I", SCRIPT, "--repo", str(self.root), "inject-rules", "--target", "agents"]
        r = subprocess.run(base, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(2, r.returncode)
        self.assertEqual(b"# r\n", (self.root / "AGENTS.md").read_bytes())
        r = subprocess.run(base + ["--dry-run"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual("append", json.loads(r.stdout)[0]["action"])
        r = subprocess.run(base + ["--apply"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn(START, (self.root / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
