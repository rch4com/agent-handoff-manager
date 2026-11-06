import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True, text=True)


class ResumeCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q", "-b", "main")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "one")
        self.payload = {"mission": "m", "next_action": "n", "agent": "codex",
                        "changed_files": [{"path": "src/a.py", "owner": "codex"}, {"path": "src/gone.py", "owner": "codex"}],
                        "validation": [{"command": "python -m unittest", "result": "passed", "evidence": ""},
                                       {"command": "ruff check", "result": "passed", "evidence": "0 errors"}]}
        self.rec = handoff.write(self.root, self.payload)

    def resume(self):
        return handoff.resume(self.root, self.rec["id"])

    def test_clean_state_has_no_git_warnings_but_flags_file_and_evidence_gaps(self):
        out = self.resume()
        self.assertEqual({}, out["differences"])
        self.assertEqual("same", out["head_relation"])
        checks = {c["path"]: c for c in out["file_checks"]}
        self.assertTrue(checks["src/a.py"]["exists"])
        self.assertFalse(checks["src/gone.py"]["exists"])
        text = " | ".join(out["warnings"])
        self.assertIn("src/gone.py", text)
        self.assertIn("python -m unittest", text)  # claimed passed without evidence
        self.assertNotIn("ruff check", text)

    def test_own_store_files_do_not_make_clean_tree_dirty(self):
        # Regression R-005: .write.lock / session.json used to flip `dirty` to True on every write.
        self.assertIs(False, self.rec["git_observation"]["dirty"])
        self.assertIs(False, self.resume()["current_git"]["dirty"])

    def test_new_commit_reports_ahead_and_branch_dirty_mismatch(self):
        (self.root / "src" / "a.py").write_text("y\n", encoding="utf-8")
        git(self.root, "commit", "-q", "-am", "two")
        git(self.root, "checkout", "-q", "-b", "other")
        (self.root / "dirty.txt").write_text("d", encoding="utf-8")
        out = self.resume()
        self.assertEqual("ahead", out["head_relation"])
        self.assertEqual(1, out["commits_since_saved"])
        for key in ("branch", "head", "dirty"):
            self.assertIn(key, out["differences"])
        self.assertTrue(any("branch" in w for w in out["warnings"]))

    def test_diverged_head_is_reported_not_guessed(self):
        git(self.root, "checkout", "-q", "--orphan", "fresh")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "unrelated")
        self.assertEqual("diverged_or_unknown", self.resume()["head_relation"])

    def test_validation_claims_are_listed_unverified_and_nothing_is_executed(self):
        marker = self.root / "executed.txt"
        self.payload["validation"] = [{"command": f"python -c \"open(r'{marker}','w')\"", "result": "passed", "evidence": "e"}]
        rec = handoff.write(self.root, self.payload)
        out = handoff.resume(self.root, rec["id"])
        self.assertFalse(marker.exists())
        self.assertFalse(out["validation_claims"][0]["verified"])
        self.assertEqual("passed", out["validation_claims"][0]["claimed_result"])

    def test_symlinked_expected_path_is_reported_not_followed(self):
        target = self.root / "real.txt"
        target.write_text("x", encoding="utf-8")
        link = self.root / "src" / "link.py"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        self.payload["changed_files"] = [{"path": "src/link.py", "owner": "codex"}]
        rec = handoff.write(self.root, self.payload)
        check = handoff.resume(self.root, rec["id"])["file_checks"][0]
        self.assertEqual("symlink", check["kind"])

    def test_outside_git_repo_degrades_cleanly(self):
        with tempfile.TemporaryDirectory() as plain:
            root = Path(plain)
            rec = handoff.write(root, self.payload)
            out = handoff.resume(root, rec["id"])
            self.assertEqual("unavailable", out["head_relation"])


if __name__ == "__main__":
    unittest.main()
