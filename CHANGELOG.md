# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/), SemVer. Pre-1.0 versions may break the CLI or schema; schema changes are listed explicitly. The session schema is `schema_version: 1` throughout.

## [0.2.0-pilot] - 2026-11-07

Experimental. Host support is exactly what `docs/COMPATIBILITY.md` marks as verified (Windows 11).

### Added
- Self-contained skill package: the core lives in `skills/agent-handoff-manager/scripts/handoff.py` (ADR-0002); installs via `gh skill` and `npx skills` verified from the public repo.
- `list` filters (`--status`, `--agent`, `--since`, `--until`) and `--all-worktrees`; `archive`/`restore` `--dry-run`; `write --depth`; `doctor` runtime/leftover/schema checks; `upstream status`.
- `resume` verification report: durable state read first, HEAD ancestry, expected-file existence, unverified validation claims, warnings, `do_not_repeat`.
- `write` prints `state_change_candidates` (proposals only); optional `failure_records` payload field; record field `depth`.
- `import-legacy` for claude-handoff-skill `.handoffs/*.md` (lossless, idempotent, originals untouched); optional record field `legacy_import`.
- `inject-rules`: marked, reversible `UNIFIED_HANDOFF` block in AGENTS.md / CLAUDE.md / copilot-instructions.md.
- Broader secret screening (16 token/credential shapes).
- Upstream monitor impact analysis report; PR adoption checklist; pinned upstream SHAs; `THIRD_PARTY_NOTICES.md`.
- Claude Code and GitHub Copilot marketplace manifests (separate formats); `scripts/host_smoke.ps1`.
- ADR-0002..0005.

### Fixed (each has a regression test; see `PROJECT_TRACKER.md` R-001..R-006)
- JSON output crashed on non-ASCII text under cp949 consoles after the record was already saved.
- Windows + Python 3.13+: owner-only ACL on session folders blocked sandboxed hosts and git.
- Git output decoded with the console code page (broke non-ASCII worktree paths).
- `dirty` was always true because the tool's own lock/session files counted.
- `--all-worktrees` listed the same checkout twice for Windows 8.3 short paths.

### Changed
- `write` returns `state_change_candidates` in addition to the record; `resume` output has new keys (additive).
- Removed `LICENSE.template` (real `LICENSE` exists).

### Known limits
See `docs/RELEASE_GATES.md`: agent-composed payload verified only on Claude Code and Codex, no Linux/macOS host runs, no VS Code / Cloud Agent runs, no signatures. Released as pre-release tag `v0.2.0-pilot` with a SHA-256 checksum (commit `041af49`).

## [0.1.0-pilot] - 2026-11-06

## Added
- `scripts/handoff.py`: conservative Python 3.10+ local pilot CLI, explicit JSON payloads, read-only resume, local archive/restore, doctor, atomic JSON writes, exclusive local lock, optimistic revisions, local Git observations, secret pattern checks and safe session IDs.
- `docs/SCHEMA_SPEC.md`, `docs/ADAPTER_CONTRACT.md`, `docs/RECOVERY_PROTOCOL.md`, `docs/RELEASE_GATES.md`, `docs/PILOT_QUICKSTART.md` and a non-sensitive sample payload.
- `tests/test_handoff.py`: local lifecycle, CLI confirmation, revision conflicts, sensitive payload rejection, traversal blocking, symlink rejection, interrupted transition detection.

## Changed
- Upstream monitor: duplicate ID validation, separate `baseline_required` output and genuine update detection; unpinned SHA no longer opens an update issue by itself.
- Upstream workflow: note unpinned baseline in workflow summary; find existing update issues via paginated API rather than a 100-issue list limit.
- CI: invoke package validator as well as unit tests across the existing Windows/Linux/Python matrix.
- Package validator: include pilot files and JSON parsing, optional YAML parsing when PyYAML is installed.
- README, architecture, work order and skill instructions clarify runnable pilot versus unimplemented host adapters.

## Verification
- `python -m unittest discover -s tests -v` — **16 tests passed** in this container.
- `python scripts/validate_distribution.py` — **PASS**.
- End-to-end local CLI smoke test — init -> write -> resume -> archive -> restore -> doctor, **PASS**.

## Remaining release blockers
- Actual five-host adapters and cloud integration tests, upstream adopted SHA verification, remote packaging/installation, distributed concurrency, more comprehensive secret scanning and crash recovery; see `docs/RELEASE_GATES.md`.
