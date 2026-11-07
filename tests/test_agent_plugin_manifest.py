"""Self-check of the root plugin.json and SKILL.md against the rules published for the awesome-copilot intake gate
(Agent Plugins v1.0.0 manifest) and the Agent Skills spec. This re-implements the documented checks in stdlib code;
it is NOT `vally lint` and does not prove the real gate will pass (see docs/MARKETPLACE_SUBMISSION.md)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ALLOWED = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def manifest_issues(m):
    issues = []
    if m.get("$schema") != SCHEMA_URL:
        issues.append("$schema")
    name = m.get("name")
    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not NAME_RE.match(name):
        issues.append("name")
    for f in ("version", "description"):
        if not isinstance(m.get(f), str) or not m[f].strip():
            issues.append(f)
    for f in ("homepage", "repository", "license"):
        if f in m and not isinstance(m[f], str):
            issues.append(f)
    if "author" in m:
        a = m["author"]
        if not isinstance(a, dict) or set(a) - {"name", "email", "url"} or any(not isinstance(v, str) for v in a.values()):
            issues.append("author")
    if "keywords" in m and (not isinstance(m["keywords"], list) or any(not isinstance(k, str) for k in m["keywords"])):
        issues.append("keywords")
    if "extensions" in m and (not isinstance(m["extensions"], dict) or any(not isinstance(v, dict) for v in m["extensions"].values())):
        issues.append("extensions")
    issues += [f"top-level {k}" for k in m if k not in ALLOWED]
    return issues


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_-]+:", line):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class ManifestRuleTests(unittest.TestCase):
    def test_root_plugin_json_has_no_issues(self):
        m = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual([], manifest_issues(m))

    def test_checker_actually_catches_violations(self):
        good = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        for broken in (dict(good, skills=["skills/x"]), dict(good, name="Bad--Name"), dict(good, author={"nick": "x"}),
                       {k: v for k, v in good.items() if k != "$schema"}, dict(good, version=" ")):
            self.assertNotEqual([], manifest_issues(broken))

    def test_skill_frontmatter_follows_agent_skills_rules(self):
        skill_dir = ROOT / "skills" / "agent-handoff-manager"
        fm = frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n"))
        self.assertEqual(skill_dir.name, fm["name"])
        self.assertTrue(SKILL_NAME_RE.match(fm["name"]) and len(fm["name"]) <= 64)
        self.assertTrue(1 <= len(fm["description"]) <= 1024, len(fm["description"]))
        self.assertEqual("MIT", fm["license"])

    def test_skill_md_has_no_dangling_relative_references(self):
        skill_dir = ROOT / "skills" / "agent-handoff-manager"
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"`(scripts/[A-Za-z0-9_./-]+)`", text):
            self.assertTrue((skill_dir / ref).exists(), ref)

    def test_both_marketplace_files_reference_the_same_plugin_name(self):
        names = {json.loads((ROOT / p).read_text(encoding="utf-8"))["plugins"][0]["name"]
                 for p in (".claude-plugin/marketplace.json", ".github/plugin/marketplace.json")}
        self.assertEqual({"agent-handoff-manager"}, names)


if __name__ == "__main__":
    unittest.main()
