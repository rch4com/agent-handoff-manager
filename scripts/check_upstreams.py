#!/usr/bin/env python3
"""Read-only upstream HEAD monitor. Does not download, execute, or adopt source."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from urllib import error, parse, request

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9_./-]+$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def validate_source(source: dict) -> None:
    if not REPO_RE.fullmatch(source.get("repo", "")):
        raise ValueError("Invalid repository identifier")
    if not REF_RE.fullmatch(source.get("ref", "")) or ".." in source["ref"]:
        raise ValueError("Invalid branch/tag reference")
    sha = source.get("adopted_sha")
    if sha is not None and not SHA_RE.fullmatch(sha):
        raise ValueError(f"Invalid pinned 40-character SHA for {source['repo']}")


def fetch_head(repo: str, ref: str, token: str | None = None) -> str:
    url = f"https://api.github.com/repos/{repo}/commits/{parse.quote(ref, safe='')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "unified-handoff-upstream-monitor/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=20) as response:
        data = json.load(response)
    sha = data.get("sha", "")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError(f"GitHub API returned no valid commit SHA for {repo}@{ref}")
    return sha.lower()


MAX_COMPARE_FILES = 300  # GitHub compare returns at most 300 files
EXECUTABLE_SUFFIXES = {".py", ".sh", ".ps1", ".psm1", ".cmd", ".bat", ".js", ".mjs", ".cjs", ".ts", ".yml", ".yaml"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def fetch_compare(repo: str, old: str, new: str, token: str | None = None) -> list[dict]:
    """File-level metadata only (names/status/line counts). Never downloads or runs upstream contents."""
    files: list[dict] = []
    for page in (1, 2, 3):
        url = f"https://api.github.com/repos/{repo}/compare/{old}...{new}?per_page=100&page={page}"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "unified-handoff-upstream-monitor/0.1",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with request.urlopen(request.Request(url, headers=headers, method="GET"), timeout=20) as response:
            batch = json.load(response).get("files", [])
        files += batch
        if len(batch) < 100:
            break
    return files


def classify_files(files: list[dict]) -> list[dict]:
    out = []
    for item in files:
        name = str(item.get("filename", ""))
        low = name.lower()
        base = low.rsplit("/", 1)[-1]
        suffix = "." + base.rsplit(".", 1)[-1] if "." in base else ""
        if base.startswith(("license", "copying", "notice")):
            category, risk = "license", "high"
        elif suffix in EXECUTABLE_SUFFIXES or "/hooks/" in "/" + low or low.startswith(("hooks/", ".github/workflows/")):
            category, risk = "executable", "high"
        elif base == "skill.md" or low.endswith(("plugin.json", "openai.yaml")) or "/references/" in "/" + low or low.startswith("references/"):
            category, risk = "skill-contract", "medium"
        elif low.startswith("templates/") or "/templates/" in low or suffix == ".json":
            category, risk = "template-or-data", "medium"
        else:
            category, risk = "docs-or-assets", "low"
        out.append({"file": name, "status": item.get("status", "?"), "changes": item.get("additions", 0) + item.get("deletions", 0),
                    "category": category, "risk": risk})
    return out


def overall_risk(classified: list[dict]) -> str:
    return max((c["risk"] for c in classified), key=RISK_ORDER.get, default="low")


def analyze(repo: str, old: str, new: str, compare) -> dict:
    try:
        files = compare(repo, old, new)
    except (OSError, ValueError, error.URLError) as exc:
        return {"error": f"impact analysis unavailable: {exc}", "overall_risk": "high", "files": []}
    classified = classify_files(files)
    truncated = len(files) >= MAX_COMPARE_FILES
    return {"files": classified, "truncated": truncated,
            "overall_risk": "high" if truncated else overall_risk(classified)}


def inspect(lock: dict, fetch=fetch_head, compare=None) -> list[dict]:
    if lock.get("schema_version") != 1:
        raise ValueError("Unsupported upstream lock format")
    sources = lock.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("No upstream sources configured")
    findings = []
    seen = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,62}', source['id']):
            raise ValueError('Source id must be lowercase kebab-case')
        if source['id'] in seen:
            raise ValueError(f"Duplicate source id: {source['id']}")
        seen.add(source['id'])
        validate_source(source)
        latest = fetch(source["repo"], source["ref"])
        adopted = source["adopted_sha"]
        status = "baseline_required" if adopted is None else (
            "update_available" if adopted.lower() != latest else "up_to_date"
        )
        finding = {
            "id": source["id"], "repo": source["repo"],
            "ref": source["ref"], "adopted_sha": adopted,
            "latest_sha": latest, "status": status,
        }
        if status == "update_available" and compare is not None:
            finding["impact"] = analyze(source["repo"], adopted, latest, compare)
        findings.append(finding)
    return findings


def markdown_report(findings: list[dict]) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Upstream comparison report", "", f"Checked: {stamp}", "",
        "**This monitor only reports upstream changes; it never installs or merges upstream code.**", "",
        "| Source | Adopted SHA | Latest SHA | Status | Review |",
        "|---|---|---|---|---|",
    ]
    for item in findings:
        repo, ref = item["repo"], item["ref"]
        old, new = item["adopted_sha"], item["latest_sha"]
        link = (f"https://github.com/{repo}/compare/{old}...{new}" if old else
                f"https://github.com/{repo}/commits/{parse.quote(ref, safe='')}")
        lines.append(f"| {repo} | `{old or 'NOT_PINNED'}` | `{new}` | {item['status']} | [Review]({link}) |")
    for item in findings:
        impact = item.get("impact")
        if not impact:
            continue
        lines += ["", f"## Impact analysis: {item['repo']}", "", f"Overall risk: **{impact['overall_risk']}**"]
        if impact.get("error"):
            lines += ["", f"> {impact['error']} (treated as high risk; review the compare link manually)"]
            continue
        if impact.get("truncated"):
            lines += ["", f"> Compare output reached {MAX_COMPARE_FILES} files and may be incomplete; treated as high risk."]
        lines += ["", "| File | Status | Lines | Category | Risk |", "|---|---|---|---|---|"]
        for f in sorted(impact["files"], key=lambda f: (-RISK_ORDER[f["risk"]], f["file"])):
            lines.append(f"| `{f['file']}` | {f['status']} | {f['changes']} | {f['category']} | {f['risk']} |")
        lines += ["", "Reviewer must: re-check LICENSE/copyright; read every `executable` change as untrusted code; diff `skill-contract` files against the adapter; run migration dry-run; then pin only through a reviewed PR."]
    lines += ["", "## Adoption gate", "", "Pin only after manual source review, license attribution, cross-platform tests, migration check, and reviewed PR.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", default="upstreams.lock.json")
    parser.add_argument("--report", default="upstream-report.md")
    parser.add_argument("--json-report", default=None)
    parser.add_argument("--github-output", default=None)
    args = parser.parse_args(argv)
    try:
        lock = json.loads(Path(args.lock).read_text(encoding="utf-8"))
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        findings = inspect(lock, fetch=lambda repo, ref: fetch_head(repo, ref, token),
                           compare=lambda repo, old, new: fetch_compare(repo, old, new, token))
        Path(args.report).write_text(markdown_report(findings), encoding="utf-8")
        if args.json_report:
            Path(args.json_report).write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
        updates = any(item["status"] == "update_available" for item in findings)
        baseline = any(item["status"] == "baseline_required" for item in findings)
        if args.github_output:
            with Path(args.github_output).open("a", encoding="utf-8") as output:
                output.write(f"changes={'true' if updates else 'false'}\n")
                output.write(f"baseline_required={'true' if baseline else 'false'}\n")
        for item in findings:
            print(f"{item['id']}: {item['status']} ({item['latest_sha'][:12]})")
        return 0
    except (ValueError, OSError, error.URLError, json.JSONDecodeError) as exc:
        print(f"UPSTREAM_MONITOR_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
