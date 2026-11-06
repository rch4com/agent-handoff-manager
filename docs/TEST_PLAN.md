# Test plan and release gates

## Automated unit tests

- ID uniqueness (same second multi-process), UTF-8 paths, invalid path/symlink, atomic failure recovery.
- Project state authority conflicts; no unverified 'done' promotion.
- `write` payload validation, secret redaction positive/negative fixtures, depth levels.
- `list` across multiple worktrees and broken cache, filter precision.
- `resume`: branch mismatch, dirty worktree, missing tests, stale or untrusted handoff, no execution side effects.
- `archive`/`restore`: dry-run, idempotency, absent or duplicate ID, state rollback on failure.
- `init` idempotent marker merge, existing upstream ④ and ③ documents untouched.
- Legacy import: source backup, metadata conversion, data preserved.
- Upstream tracking: missing SHA, malformed SHA, API error, no changes, version changes.

## Integration and E2E tests

1. Empty project -> init -> write -> list -> resume -> archive -> restore -> list.
2. ④ initialized project -> integrate without changing its unrelated files.
3. ③ existing `.handoffs/*.md` -> import with dry-run, compare content hashes.
4. Claude write -> Codex resume, Codex write -> OpenCode list, OpenCode write -> Antigravity resume (where supported).
5. Two agents write concurrently, unique IDs with no overwrites.
6. Different OS/paths and Git worktrees, shared Git commit & merge simulation.
7. ④ compaction while ③ archiving, validation records retained.
8. Upstream SHA changes; watcher updates issue only; product code remains unchanged.

## Pre-release checklist

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] Windows and Linux CI matrix green.
- [ ] all user guide examples actually run.
- [ ] exact CLI version and host behavior reported in compatibility matrix.
- [ ] no known unresolved data-loss/secret/permission issues.
- [ ] third-party attribution and license files verified.
- [ ] upgrade from previous version + rollback tested.
- [ ] public pilot user installs and exercises core workflow.

## Evidence format

For each test include test name, OS, Python version, CLI version, command, exit code, expected vs actual, artifact hash/commit, timestamp, responsible reviewer.

## Five-host compatibility and distribution E2E (additional)

- Copilot VS Code: project and user skill discovery; correct loading only once; Python core invocation; session transfer from Claude/Codex.
- Copilot CLI: `gh skill install --agent github-copilot` + `/skills list`, `/skills info`, `/skills reload`; `write/list/resume/archive` core execution.
- Copilot Cloud Agent: target repository receives skill and runtime; untrusted handoff data can't execute arbitrary commands; check artifact commit/review status.
- Shared source -> installed layout: `gh skill` may copy the `skills/<name>` directory **without repo root**; all runtime references must be resolvable after installation.
- Public repo: new account/clean profile, `gh skill preview/install/update`; `npx skills add`; pinned tag; uninstall and rollback.
- Windows PowerShell / Linux Bash, non-ASCII paths, two concurrent agents, symlink/copy path differences.
- Release gate: every claimed supported surface has OS, exact version, command, exit code, artifacts, reviewer evidence.
