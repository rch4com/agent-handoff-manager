# Execution Results Implementation Plan

> Inline execution authorized by the owner. Coordinator owns all edits; any reviewer is read-only. Use TDD and retain existing records and application source.

**Goal:** Commit existing audit fixes, then implement ADR-0006 execution snapshots, immutable results and safe concurrent submissions.

**Architecture:** Shared stdlib Python core inside the existing skill. Reuse store locks, atomic JSON, credential/payload validation and Git observations. Separate run schema v1 from session schema v1. No new dependencies or host settings.

1. Baseline: inspect invariants and pins, run full tests/distribution checker, commit the existing audit changes. Evidence: commit `88992f0`, Windows 113 tests OK (5 skipped).
2. Write failing tests in `tests/test_runs.py`: start/finish/list, snapshot preservation, request replay/conflict, retry lineage, explicit result selection, malformed/secret inputs, old-store reads and diagnostics. Implement shared core and CLI to pass.
3. Add subprocess contention tests: independent writers, same request key, competing final results, source update/start and archive/finish. Add read-only cross-worktree and duplicate-conflict cases, simulated publication faults, and installed-skill-copy lifecycle. Watch failures before completing implementations.
4. Update help, SKILL.md, architecture, schema/user/security/recovery/compatibility docs and CHANGELOG. Add representative run payload example. Keep host support claims unchanged.
5. Run Windows/Linux full suites, distribution and diff checks. Request read-only review, address findings with regressions, record commands/results/review in PROJECT_TRACKER.md, commit implementation. No push or release implied.

**Completion evidence:** committed diff, red/green regressions, cross-platform test output and review findings resolved. Scope excludes automatic work assignment and distributed locks, as agreed in INTENTS.md.
