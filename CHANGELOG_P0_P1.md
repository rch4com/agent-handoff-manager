# P0/P1 enhancement changelog — 2026-11-06

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
