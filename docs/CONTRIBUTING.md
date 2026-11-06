# Contributing

We welcome bug reports, documentation corrections, platform compatibility reports, upstream update proposals and tests.

## Before changes

Read `INTENTS.md`, `AGENTS.md`, `WORK_ORDER.md`, `docs/UPSTREAM_POLICY.md` and `docs/SECURITY.md`.

## PR structure

- Summary and scope; linked issue, source version and SHA if adapting upstream.
- Changed files and migration impact.
- Tests actually run, with OS/Python/tool versions and outputs.
- Risks, rollback plan and legal attribution.
- Documentation and example changes.

## Upstream updates

Do not paste new upstream code directly into `main`. Create an isolated PR, record old/new SHA, keep license notices, review behavior differences, run the test matrix, and obtain maintainer approval.

## Changes to handoff format

Backward compatibility is required by default. Add `schema_version`, migration tests and release notes for format changes.

## Multi-agent contributions

Use distinct branches/worktrees. Assign ownership for overlapping files. Integration maintainer validates the final combined tree and records exact evidence; agent-authored claims are not a substitute for tests.

## Five-agent contribution support

Contributions from GitHub Copilot (VS Code Agent, Copilot CLI, Cloud Agent), Claude Code, Codex CLI, OpenCode, and Antigravity follow the same AGENTS.md and PROJECT_TRACKER.md evidence rules. Do not merge marketplace metadata until a real install smoke test proves the packaged Python core executes. Changes to a host adapter require corresponding entries in docs/COMPATIBILITY.md and docs/COPILOT_SETUP.md as applicable.
