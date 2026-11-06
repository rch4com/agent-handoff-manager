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


if __name__ == "__main__":
    unittest.main()
