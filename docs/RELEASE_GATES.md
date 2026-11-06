# Release gates (pilot vs stable)

## Pilot readiness (included in this package)

- [x] Deterministic local CLI for init/write/list/resume/archive/restore/doctor
- [x] Schema v1 and explicit host payload boundary
- [x] Local exclusive write lock, atomic metadata replacement, revision conflict rejection
- [x] Common secret pattern rejection, path traversal checks, read-only resume
- [x] Unit tests for lifecycle, conflicts, security and interrupted transition detection
- [x] Upstream monitor flags an unpinned baseline separately from genuine updates
- [ ] Real five-host adapters and end-to-end permission checks
- [ ] Verified upstream pins after license/source review
- [ ] Remote skill installation, packaged self-contained runtime and upgrade tests

## Stable v1.0 blockers

- [ ] Complete supported host adapters with real session handoffs on each platform (including Copilot cloud)
- [ ] Stronger schema validation and a tested backward-compatible migration procedure
- [ ] Multi-process and crash-injection tests, durability review on Windows and network filesystems
- [ ] Verified secret scanning and manual privacy/security assessment
- [ ] Versioned distribution, checksums, install/update/rollback and clean-machine smoke tests
- [ ] Source attribution and licensing cleared; all adopted upstream SHAs pinned by reviewed PR
- [ ] Security threat model reviewed against prompt injection and untrusted handoff records

**Status: experimental local pilot. Not a production-ready multi-agent manager.** Test evidence must never be described as host integration or public distribution verification.
