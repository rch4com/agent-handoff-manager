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


def inspect(lock: dict, fetch=fetch_head) -> list[dict]:
    if lock.get("schema_version") != 1:
        raise ValueError("Unsupported upstream lock format")
    sources = lock.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("No upstream sources configured")
    findings = []
    for source in sources:
        validate_source(source)
        latest = fetch(source["repo"], source["ref"])
        adopted = source["adopted_sha"]
        status = "baseline_required" if adopted is None else (
            "update_available" if adopted.lower() != latest else "up_to_date"
        )
        findings.append({
            "id": source["id"], "repo": source["repo"],
            "ref": source["ref"], "adopted_sha": adopted,
            "latest_sha": latest, "status": status,
        })
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
        findings = inspect(lock, fetch=lambda repo, ref: fetch_head(repo, ref, token))
        Path(args.report).write_text(markdown_report(findings), encoding="utf-8")
        if args.json_report:
            Path(args.json_report).write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
        updates = any(item["status"] != "up_to_date" for item in findings)
        if args.github_output:
            with Path(args.github_output).open("a", encoding="utf-8") as output:
                output.write(f"changes={'true' if updates else 'false'}\n")
        for item in findings:
            print(f"{item['id']}: {item['status']} ({item['latest_sha'][:12]})")
        return 0
    except (ValueError, OSError, error.URLError, json.JSONDecodeError) as exc:
        print(f"UPSTREAM_MONITOR_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
