# Recovery and concurrent work protocol

## Local write algorithm

`write` creates `.handoffs` only under a caller-selected, existing repository directory and rejects a symlinked store or session bucket. It takes an exclusive `.handoffs/.write.lock` using `O_CREAT|O_EXCL` (4-second wait). A lock left by a crashed process is deliberately **not removed automatically**. For new sessions, the directory is created exclusively; metadata is written into a same-directory temporary file, fsynced, then atomically replaced. For updates, pass the current `revision`; stale writers fail rather than overwriting newer content.

## Archive/restore interruption recovery

A confirmed transition first writes the destination status in the existing session metadata, then renames the session directory within the same filesystem. If the rename errors normally, previous metadata are restored; a sudden crash between the two operations can leave status/location mismatch. `doctor` reports the mismatch. An operator must inspect the record, compare destination and source, back up the data and then repair the status/location manually. Never delete an unexpected copy solely on the basis of this document. Archive and restore do not delete session contents.

## Worktrees, machines, conflicts

The exclusive lock coordinates local processes sharing the *same* `.handoffs` path. It is NOT a distributed lock and does not coordinate independent Git worktrees, cloned repositories, cloud agents, or filesystems that do not honor exclusive creation. Give each agent a separate worktree; designate one coordinator for merging session claims and changing authoritative `.agent-handoff/` project state. Before merging, compare base commit, changed-file ownership, revision, and validation evidence. A mismatch is a review/merge task, not permission to overwrite. Do not use this pilot as the source of truth for cross-machine concurrent edits.

## Failure drills

1. Create session and update using a correct revision, then verify a stale update is rejected.
2. Archive and restore with explicit `--confirm`; inspect `doctor` before and after.
3. Fabricate a status/location mismatch and ensure `doctor` returns nonzero.
4. Place a temporary `.write.lock`; ensure a second writer fails safely instead of deleting it.
5. Run the same tests on Windows and Linux in CI.

The runtime does not implement automatic rollback journals, cross-machine leases, atomic multi-file transactions, or fully automated crash recovery. These are explicit release blockers for any stronger durability guarantee.

## Verified interruption behavior (tests/test_crash_recovery.py, simulated kills)

| Interruption | Result | Recovery |
|---|---|---|
| `rename` fails during archive/restore (e.g. folder locked) | original metadata restored, `doctor` ok | retry |
| Process killed after metadata rewrite, before the folder move | `doctor` reports `Status/location mismatch`; record still readable | **re-run the same `archive`/`restore --confirm`**: completes and `doctor` is ok |
| Process killed while creating a new session | existing records untouched; the empty folder is reported by `doctor` as `Unreadable session record` | remove that empty folder after backing it up, or ignore; new writes are unaffected |
| Process killed while holding `.write.lock` | next writers fail after about 4 s naming the lock owner (`pid=... time=...`); `doctor` reports it | verify the process is gone, remove the lock file **manually**; never automatic |

Real `kill -9`/power-loss durability (fsync ordering, network filesystems) is **not** tested; `os.replace` + `fsync` are used but not proven under such faults.
