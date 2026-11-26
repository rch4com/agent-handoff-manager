# agent-handoff-manager

**Status: experimental source version (0.3.0-pilot).** The shared Python core has tests on Windows/Linux and several host runs on Windows 11. Linux/macOS host E2E and Copilot VS Code Agent remain unverified; Cloud Agent testing was skipped by the owner. Documentation reconciled on 2026-11-13; historical execution evidence is in `PROJECT_TRACKER.md`.

An Agent Skill for handing work over between AI coding agents (Claude Code, Codex CLI, OpenCode, Antigravity, GitHub Copilot). It keeps **verified long-term project state** separate from **per-session handoff records (claims)**. `resume` is read-only: it compares the record with the real git state and runs nothing from the record.

Design references: ④ [WeirdSky924/agent-handoff-skill](https://github.com/WeirdSky924/agent-handoff-skill) and ③ [aploe/claude-handoff-skill](https://github.com/aploe/claude-handoff-skill), both MIT; reviewed SHAs are pinned in `upstreams.lock.json`. **No upstream code is vendored** (see `docs/ADR-0003.md`, `THIRD_PARTY_NOTICES.md`). Upstream changes are detected automatically but never adopted without a reviewed PR.

## Install (paths verified on Windows 11)

```bash
gh skill preview rch4com/agent-handoff-manager agent-handoff-manager
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope project   # needs gh 2.90+ (tested: 2.103.3)
npx skills add rch4com/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex --copy
```

Use `--pin v0.3.0-pilot` to install from the current source tag. [v0.3.0-pilot source](https://github.com/rch4com/agent-handoff-manager/tree/v0.3.0-pilot)

`--agent` values `claude-code`, `codex`, `opencode`, `antigravity` and `github-copilot` were each installed and checked. The core (`scripts/handoff.py`) is shipped inside the skill folder (`docs/ADR-0002.md`); only Python 3.10+ is required. Nothing is executed at install time. Do not install the same skill into both `.agents/skills` and `.claude/skills` for Copilot.

### Optional: plugin route (do not combine with a skill install)

```bash
# Claude Code (tested: 2.1.319)
claude plugin marketplace add rch4com/agent-handoff-manager
claude plugin install agent-handoff-manager@agent-handoff-manager-marketplace
# GitHub Copilot CLI (tested: 1.0.105, install only)
copilot plugin marketplace add rch4com/agent-handoff-manager
copilot plugin install agent-handoff-manager@agent-handoff-manager-copilot
```

The two marketplace manifests use different formats (`.claude-plugin/` vs `plugin.json` + `.github/plugin/`) and point at the same skill folder. Nothing was submitted to an official marketplace. See `docs/MARKETPLACES.md`.

## Use

The commands in `docs/USER_GUIDE.md` match the real CLI:

```bash
python <skill-dir>/scripts/handoff.py --repo . write --payload payload.json
python <skill-dir>/scripts/handoff.py --repo . list [--status all] [--agent codex] [--since D] [--until D] [--all-worktrees]
python <skill-dir>/scripts/handoff.py --repo . resume latest
python <skill-dir>/scripts/handoff.py --repo . archive ID --confirm   # restore ID --confirm
python <skill-dir>/scripts/handoff.py --repo . doctor
python <skill-dir>/scripts/handoff.py --repo . import-legacy --dry-run
```

## Verified so far (Windows 11)

| Host | Discovered | Core ran | Verified behavior |
|---|---|---|---|
| Claude Code 2.1.319 | yes | yes | write, list, resume |
| Codex CLI 0.165.0 | yes | yes | write, resume (needs a real python path) |
| OpenCode 1.19.4 | yes | yes | resume, write (core invocation only; payload prepared externally; with explicit `-m`) |
| Antigravity agy 1.5.0 / 1.5.6 | yes | yes | resume, write (core invocation only; payload prepared externally) |
| Copilot CLI 1.0.105 | yes | yes | resume, write (core invocation only; payload prepared externally) |
| Copilot VS Code Agent / Cloud Agent | no | no | not tested |

Evidence: `PROJECT_TRACKER.md` and `docs/COMPATIBILITY.md`. Compatibility will not be declared for v1.0 before end-to-end runs on all five hosts and the three Copilot surfaces.

## Remaining work and verification

### Execution tracking in local source (unreleased)

Use `run-start` to capture the received input, `run-finish` to submit an immutable per-worker result, and `list-runs`/`resume` to inspect results, retries and explicit integration selections. Identical request-key retries do not create duplicate submissions. No agent scheduling or official approval is automated. These commands are absent from the existing `v0.2.0-pilot` release tag. See `docs/USER_GUIDE.md` and `docs/ADR-0006.md`.

Change proposals, upstream impact reports, Claude/Copilot marketplace manifests, and a pilot release tag/checksum already exist. Remaining work: durable-state parsing/approval, issue updates for a real upstream change, Linux/macOS host E2E, Copilot VS Code Agent, external-user clean-machine onboarding and new-version updates, signatures and tag protection. Cloud Agent testing was skipped by the owner and is not verified support. See `docs/RELEASE_GATES.md`.

## Develop

```bash
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/check_upstreams.py
```

Licensed under MIT (`LICENSE`).
