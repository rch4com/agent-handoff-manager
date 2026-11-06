# Unified Handoff Manager — Development starter

**Status: specifications and an upstream watcher, not a completed skill.**

The goal is to combine durable repository-level state inspired by
[WeirdSky924/agent-handoff-skill](https://github.com/WeirdSky924/agent-handoff-skill)
with session lifecycle management inspired by
[aploe/claude-handoff-skill](https://github.com/aploe/claude-handoff-skill),
for Claude Code, Codex CLI, OpenCode, Antigravity and GitHub Copilot (VS Code agent, Copilot CLI and cloud agent).

The planned shared commands are `write`, `resume`, `list`, and `archive`.
The implementation will use a portable Python core, a project-owned canonical state,
portable session records, and host-specific wrappers.

**Upstream changes will be detected automatically, not blindly applied.** A change
should be reviewed, tested, and approved before release. This avoids silent regressions.

Read `WORK_ORDER.md`, `AGENTS.md`, `INTENTS.md` and `ARCHITECTURE.md` before coding.
See `docs/USER_GUIDE.md` for the proposed user-facing commands. These commands are not
operational yet. `scripts/check_upstreams.py` and its tests are functional starter tools.

Both sources advertise the MIT license. Preserve source copyright and license notices
for any code redistributed from them. A new public project also needs its own LICENSE,
release pipeline, compatibility testing and publication decision.

## Installation / distribution plan

Suggested public repository: `YOUR_GITHUB_ID/agent-handoff-manager` with the standard Agent Skill source at `skills/agent-handoff-manager/SKILL.md`.

GitHub CLI `gh skill` (2.90.0+, preview) and `npx skills` are planned public-install entry points, but the Python core and real install E2E tests remain TODO. GitHub Copilot's native Agent Skills support covers VS Code Agent Mode, Copilot CLI and Copilot cloud agent; the latter must have the skill/resources in the target repository or environment. **No public repository or marketplace has been created.** See `docs/INSTALLATION_AND_SHARING.md`, `docs/COPILOT_SETUP.md` and `docs/MARKETPLACES.md`.
