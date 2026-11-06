import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_upstreams.py"
spec = importlib.util.spec_from_file_location("check_upstreams", SCRIPT)
upstreams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstreams)

FIRST = "a" * 40
SECOND = "b" * 40


def source(sha):
    return {"id": "unit", "repo": "owner/project", "ref": "main", "adopted_sha": sha}


class UpstreamMonitorTests(unittest.TestCase):
    def test_baseline_required_when_sha_missing(self):
        got = upstreams.inspect({"schema_version": 1, "sources": [source(None)]},
                                fetch=lambda repo, ref: FIRST)
        self.assertEqual(got[0]["status"], "baseline_required")

    def test_detects_update_without_changing_lock(self):
        lock = {"schema_version": 1, "sources": [source(FIRST)]}
        before = json.dumps(lock, sort_keys=True)
        got = upstreams.inspect(lock, fetch=lambda repo, ref: SECOND)
        self.assertEqual(got[0]["status"], "update_available")
        self.assertEqual(before, json.dumps(lock, sort_keys=True))
        self.assertIn("/compare/", upstreams.markdown_report(got))

    def test_no_change(self):
        got = upstreams.inspect({"schema_version": 1, "sources": [source(FIRST)]},
                                fetch=lambda repo, ref: FIRST)
        self.assertEqual(got[0]["status"], "up_to_date")

    def test_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate source id'):
            upstreams.inspect({'schema_version': 1, 'sources': [source(FIRST), source(SECOND)]},
                              fetch=lambda repo, ref: FIRST)

    def test_unpinned_is_not_a_change_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'upstreams.json'
            lock.write_text(json.dumps({'schema_version': 1, 'sources': [source(None)]}), encoding='utf-8')
            output = Path(tmp) / 'report.md'
            ghout = Path(tmp) / 'github.txt'
            with patch.object(upstreams, 'fetch_head', return_value=FIRST):
                self.assertEqual(0, upstreams.main(['--lock', str(lock), '--report', str(output), '--github-output', str(ghout)]))
            self.assertIn('changes=false', ghout.read_text())
            self.assertIn('baseline_required=true', ghout.read_text())

    def test_bad_sha_rejected(self):
        with self.assertRaises(ValueError):
            upstreams.inspect({"schema_version": 1, "sources": [source("not-a-sha")]},
                              fetch=lambda repo, ref: FIRST)

    def test_bad_repo_rejected(self):
        bad = source(FIRST)
        bad["repo"] = "../../example"
        with self.assertRaises(ValueError):
            upstreams.inspect({"schema_version": 1, "sources": [bad]},
                              fetch=lambda repo, ref: FIRST)

    def test_api_failure_does_not_fake_up_to_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "upstreams.json"
            lock.write_text(json.dumps({"schema_version": 1, "sources": [source(FIRST)]}), encoding="utf-8")
            output = Path(tmp) / "out.md"
            with patch.object(upstreams, "fetch_head", side_effect=OSError("Offline")):
                self.assertEqual(upstreams.main(["--lock", str(lock), "--report", str(output)]), 2)
            self.assertFalse(output.exists())


class ImpactAnalysisTests(unittest.TestCase):
    FILES = [
        {"filename": "LICENSE", "status": "modified", "additions": 1, "deletions": 1},
        {"filename": "scripts/maintain_handoff.py", "status": "modified", "additions": 10, "deletions": 2},
        {"filename": "templates/handoff-watch.mjs", "status": "added", "additions": 50, "deletions": 0},
        {"filename": "skills/handoff-write/SKILL.md", "status": "modified", "additions": 3, "deletions": 3},
        {"filename": "README.md", "status": "modified", "additions": 1, "deletions": 0},
        {"filename": "assets/readme/hero.png", "status": "modified", "additions": 0, "deletions": 0},
    ]

    def test_classification_and_risk(self):
        got = {f["file"]: f for f in upstreams.classify_files(self.FILES)}
        self.assertEqual(("license", "high"), (got["LICENSE"]["category"], got["LICENSE"]["risk"]))
        self.assertEqual(("executable", "high"), (got["scripts/maintain_handoff.py"]["category"], got["scripts/maintain_handoff.py"]["risk"]))
        self.assertEqual(("executable", "high"), (got["templates/handoff-watch.mjs"]["category"], got["templates/handoff-watch.mjs"]["risk"]))
        self.assertEqual(("skill-contract", "medium"), (got["skills/handoff-write/SKILL.md"]["category"], got["skills/handoff-write/SKILL.md"]["risk"]))
        self.assertEqual("low", got["README.md"]["risk"])
        self.assertEqual("low", got["assets/readme/hero.png"]["risk"])
        self.assertEqual("high", upstreams.overall_risk(list(got.values())))
        self.assertEqual("low", upstreams.overall_risk([got["README.md"]]))

    def test_inspect_attaches_impact_only_for_updates_and_never_fetches_contents(self):
        calls = []

        def compare(repo, old, new):
            calls.append((repo, old, new))
            return self.FILES

        lock = {"schema_version": 1, "sources": [source(FIRST)]}
        got = upstreams.inspect(lock, fetch=lambda r, ref: SECOND, compare=compare)
        self.assertEqual([("owner/project", FIRST, SECOND)], calls)
        self.assertEqual("high", got[0]["impact"]["overall_risk"])
        report = upstreams.markdown_report(got)
        self.assertIn("Impact analysis", report)
        self.assertIn("scripts/maintain_handoff.py", report)
        self.assertIn("LICENSE", report)
        self.assertIn("never installs or merges", report)
        same = upstreams.inspect(lock, fetch=lambda r, ref: FIRST, compare=compare)
        self.assertNotIn("impact", same[0])
        self.assertEqual(1, len(calls))

    def test_compare_failure_is_reported_not_hidden(self):
        def boom(repo, old, new):
            raise OSError("rate limited")

        got = upstreams.inspect({"schema_version": 1, "sources": [source(FIRST)]}, fetch=lambda r, ref: SECOND, compare=boom)
        self.assertEqual("update_available", got[0]["status"])
        self.assertIn("rate limited", got[0]["impact"]["error"])
        self.assertIn("rate limited", upstreams.markdown_report(got))

    def test_truncated_compare_marks_risk_unknown_high(self):
        files = [{"filename": f"docs/{i}.md", "status": "modified", "additions": 1, "deletions": 0} for i in range(300)]
        got = upstreams.inspect({"schema_version": 1, "sources": [source(FIRST)]}, fetch=lambda r, ref: SECOND, compare=lambda *a: files)
        self.assertTrue(got[0]["impact"]["truncated"])
        self.assertEqual("high", got[0]["impact"]["overall_risk"])


if __name__ == "__main__":
    unittest.main()
