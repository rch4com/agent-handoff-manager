# Release gates (pilot vs stable)

State as of 2026-11-07. `[x]` = evidence exists in `PROJECT_TRACKER.md`; `[ ]` = not done or not verified.

## Pilot readiness

- [x] Deterministic local CLI: init/write/list/resume/archive/restore/doctor/import-legacy (`--depth`, list filters, `--dry-run`)
- [x] Schema v1 + explicit host payload boundary (`docs/SCHEMA_SPEC.md`)
- [x] Local exclusive write lock, atomic metadata replacement, revision conflict rejection, 6-process concurrency tests
- [x] Secret pattern rejection (16 fake shapes), path traversal checks, read-only resume, symlink rejection
- [x] Durable state (`AGENT_HANDOFF.md`, `.agent-handoff/`) read first and never modified; session claims never official
- [x] Upstream SHAs pinned after license/source review; impact analysis report; PR adoption checklist
- [x] Self-contained skill package (core inside the skill folder); gh skill + npx skills remote install verified (Windows 11)
- [x] Unit tests on Windows + Linux in CI (Python 3.10, 3.12)
- [x] Host smoke on Windows 11: Claude Code, Codex, OpenCode, Antigravity, Copilot CLI (see `docs/COMPATIBILITY.md` for exact scope)

## Stable v1.0 blockers

- [ ] write + resume verified on **every** host (missing: write on OpenCode/Antigravity/Copilot CLI) and on Linux/macOS hosts
- [ ] Copilot VS Code Agent Mode and Copilot Cloud Agent end-to-end (not tested)
- [ ] Real process-kill and power-loss durability, network filesystems (simulated interruptions are tested: `docs/RECOVERY_PROTOCOL.md`)
- [ ] Distributed coordination across worktrees/machines beyond OS locks and revision checks (explicitly out of scope for v1.0 per INTENTS.md; must be documented, not implied)
- [ ] Secret screening beyond patterns (entropy/PII) or an explicit accepted-risk decision; manual privacy review
- [ ] Release tag, checksums/signature policy, GitHub Release artifact, tag protection, `gh skill update` receiving a new tagged version
- [ ] Clean-machine onboarding run by someone other than the author (new user -> install -> write/resume -> upgrade -> uninstall)
- [ ] ④ durable-state parsing/approval workflow (P3 only reads and proposes), ④ compaction vs ③ archive on a real ④ project
- [ ] Real ③-generated legacy documents imported (fixture is hand-written)
- [ ] Threat model reviewed against prompt injection through handoff records (resume never executes them; needs adversarial test with real hosts)
- [ ] Owner approval for any official marketplace submission

**Status: experimental pilot. Do not declare v1.0 or host support beyond what `docs/COMPATIBILITY.md` marks as verified.**
