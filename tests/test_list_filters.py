import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

SCRIPT = str(Path(handoff.__file__).resolve())


def payload(agent, mission="m"):
    return {"agent": agent, "mission": mission, "next_action": "n"}


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True, text=True)


class ListFilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a = handoff.write(self.root, payload("codex", "alpha"))
        self.b = handoff.write(self.root, payload("claude-code", "beta"))
        handoff.transition(self.root, self.b["id"], True)

    def ids(self, **kw):
        return sorted(r["id"] for r in handoff.list_filtered(self.root, **kw))

    def test_status_filter(self):
        self.assertEqual([self.a["id"]], self.ids())
        self.assertEqual([self.a["id"]], self.ids(status="open"))
        self.assertEqual([self.b["id"]], self.ids(status="archived"))
        self.assertEqual(sorted([self.a["id"], self.b["id"]]), self.ids(status="all"))

    def test_agent_filter(self):
        self.assertEqual([self.b["id"]], self.ids(status="all", agent="claude-code"))
        self.assertEqual([], self.ids(status="all", agent="opencode"))

    def test_date_filter_uses_created_at_inclusive(self):
        day = self.a["created_at"][:10]
        self.assertEqual(2, len(self.ids(status="all", since=day, until=day)))
        self.assertEqual([], self.ids(status="all", since="2999-01-01"))
        self.assertEqual([], self.ids(status="all", until="2000-01-01"))

    def test_invalid_filters_rejected(self):
        for kw in ({"status": "bogus"}, {"agent": "nobody"}, {"since": "2026-13-40"}, {"since": "yesterday"}):
            with self.assertRaises(handoff.HandoffError):
                handoff.list_filtered(self.root, **kw)

    def test_cli_filters_and_archived_alias(self):
        base = [sys.executable, "-I", SCRIPT, "--repo", str(self.root), "list"]
        def run(*extra):
            r = subprocess.run(base + list(extra), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, r.returncode, r.stderr)
            return json.loads(r.stdout)
        self.assertEqual([self.b["id"]], [x["id"] for x in run("--archived")])
        self.assertEqual([self.a["id"]], [x["id"] for x in run("--agent", "codex")])
        self.assertEqual(2, len(run("--status", "all")))
        r = subprocess.run(base + ["--status", "bogus"], capture_output=True, text=True)
        self.assertEqual(2, r.returncode)


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.main = base / "메인 repo"
        self.main.mkdir()
        git(self.main, "init", "-q")
        git(self.main, "commit", "-q", "--allow-empty", "-m", "init")
        self.linked = base / "linked wt"
        git(self.main, "worktree", "add", "-q", str(self.linked), "-b", "feature")

    def test_all_worktrees_lists_sessions_from_every_checkout_read_only(self):
        a = handoff.write(self.main, payload("codex", "main side"))
        b = handoff.write(self.linked, payload("copilot", "linked side"))
        self.assertEqual([b["id"]], [r["id"] for r in handoff.list_filtered(self.linked)])
        found = handoff.list_filtered(self.linked, all_worktrees=True)
        self.assertEqual(sorted([a["id"], b["id"]]), sorted(r["id"] for r in found))
        by_id = {r["id"]: r for r in found}
        self.assertEqual(str(self.main.resolve()), by_id[a["id"]]["worktree_root"])
        self.assertEqual(str(self.linked.resolve()), by_id[b["id"]]["worktree_root"])
        # no mutation: main store still has exactly one session
        self.assertEqual(1, len(handoff.list_records(self.main)))

    def test_all_worktrees_outside_git_falls_back_to_current_store(self):
        with tempfile.TemporaryDirectory() as plain:
            root = Path(plain)
            r = handoff.write(root, payload("codex"))
            found = handoff.list_filtered(root, all_worktrees=True)
            self.assertEqual([r["id"]], [x["id"] for x in found])


if __name__ == "__main__":
    unittest.main()
