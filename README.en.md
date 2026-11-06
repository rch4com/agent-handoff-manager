# agent-handoff-manager

**Status: experimental local pilot (0.2.0-pilot).** The shared Python core works and was exercised on Windows 11 with several hosts. This is not v1.0; Linux/macOS and the Copilot VS Code Agent and Cloud Agent surfaces are unverified. As of 2026-11-07.

An Agent Skill for handing work over between AI coding agents (Claude Code, Codex CLI, OpenCode, Antigravity, GitHub Copilot). It keeps **verified long-term project state** separate from **per-session handoff records (claims)**. `resume` is read-only: it compares the record with the real git state and runs nothing from the record.

Design references: ④ [WeirdSky924/agent-handoff-skill](https://github.com/WeirdSky924/agent-handoff-skill) and ③ [aploe/claude-handoff-skill](https://github.com/aploe/claude-handoff-skill), both MIT; reviewed SHAs are pinned in `upstreams.lock.json`. **No upstream code is vendored** (see `docs/ADR-0003.md`, `THIRD_PARTY_NOTICES.md`). Upstream changes are detected automatically but never adopted without a reviewed PR.

## Install (paths verified on Windows 11)

```bash
gh skill preview rch4com/agent-handoff-manager agent-handoff-manager
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope project   # needs gh 2.90+ (tested: 2.103.3)
npx skills add rch4com/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex --copy
```

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
| Antigravity agy 1.5.0 | yes | yes | resume, write (core invocation only; payload prepared externally) |
| Copilot CLI 1.0.105 | yes | yes | resume, write (core invocation only; payload prepared externally) |
| Copilot VS Code Agent / Cloud Agent | no | no | not tested |

Evidence: `PROJECT_TRACKER.md` and `docs/COMPATIBILITY.md`. Compatibility will not be declared for v1.0 before end-to-end runs on all five hosts and the three Copilot surfaces.

## Not implemented yet

Durable-state (④) change proposals, upstream impact-analysis PR automation, Claude/Copilot marketplace manifests, release tags/checksums, Linux verification. See `docs/RELEASE_GATES.md`.

## Develop

```bash
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/check_upstreams.py
```

Licensed under MIT (`LICENSE`).
