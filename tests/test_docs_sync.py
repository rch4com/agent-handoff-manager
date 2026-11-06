"""Acceptance #10: commands shown in user docs must exist in the real CLI."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "agent-handoff-manager" / "scripts" / "handoff.py"
DOCS = ["docs/USER_GUIDE.md", "README.md", "README.en.md", "docs/PILOT_QUICKSTART.md",
        "skills/agent-handoff-manager/SKILL.md"]


def help_text(*cmd):
    r = subprocess.run([sys.executable, "-I", str(SCRIPT), *cmd, "--help"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


class DocsMatchCliTests(unittest.TestCase):
    def test_every_documented_subcommand_and_flag_exists(self):
        top = help_text()
        subs = re.search(r"\{([a-z,-]+)\}", top).group(1).split(",")
        helps = {s: help_text(s) for s in subs}
        known_flags = set(re.findall(r"--[a-z][a-z-]*", top + "".join(helps.values())))
        pattern = re.compile(r"(?:handoff\.py|\$H)\s+(?:--repo\s+\S+\s+)?([a-z-]+)([^\n`]*)")
        seen = 0
        for rel in DOCS:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for sub, rest in pattern.findall(text):
                if sub.startswith("-"):
                    continue
                seen += 1
                self.assertIn(sub, subs, f"{rel}: unknown subcommand '{sub}'")
                for flag in re.findall(r"--[a-z][a-z-]*", rest):
                    self.assertIn(flag, known_flags, f"{rel}: unknown flag {flag} in '{sub}{rest}'")
        self.assertGreater(seen, 15)

    def test_docs_do_not_advertise_unimplemented_flags_as_working(self):
        guide = (ROOT / "docs/USER_GUIDE.md").read_text(encoding="utf-8")
        for fake in ("--verify-only", "--layout"):
            for line in guide.splitlines():
                if fake in line and "python $H" in line:
                    self.fail(f"USER_GUIDE shows unimplemented {fake}: {line}")


if __name__ == "__main__":
    unittest.main()
