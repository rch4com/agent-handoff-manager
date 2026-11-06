<!-- Use this checklist for any PR that changes upstreams.lock.json adopted_sha or imports upstream-derived content. -->
## Upstream adoption (delete if not applicable)

- Source / old SHA -> new SHA / compare URL:
- Why adopt this change:
- Impact analysis report (from the `[upstream]` issue or `scripts/check_upstreams.py`) attached: [ ]

## Required checks (docs/UPSTREAM_POLICY.md)

- [ ] LICENSE / copyright unchanged, or `THIRD_PARTY_NOTICES.md` updated
- [ ] Every `executable`-category file reviewed as untrusted code (hooks, scripts, workflows)
- [ ] Contract changes (`skill-contract`) mapped to adapter changes or explicitly ignored
- [ ] Migration dry-run on an existing project; rollback verified
- [ ] contract / compat / security / migration tests pass on Windows and Linux
- [ ] CHANGELOG + SemVer bump; supported host versions in `docs/COMPATIBILITY.md` re-checked
- [ ] Only the reviewed SHA is written to `upstreams.lock.json`

## Evidence (command, result, commit)
