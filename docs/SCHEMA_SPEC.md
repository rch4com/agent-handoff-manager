# Session schema v1 — pilot normative contract

`session.json` is UTF-8 JSON under `.handoffs/sessions/<id>/` (or `.handoffs/archive/<id>/`). The deterministic core is `skills/agent-handoff-manager/scripts/handoff.py`; the host supplies an explicit JSON payload and the core does **not** read conversations. The external payload and persisted record are different objects.

## Accepted input payload

Required: `mission` (non-empty string), `next_action` (non-empty string). Optional: `agent` (`claude-code`, `codex`, `opencode`, `antigravity`, `copilot`, `other`); `acceptance_criteria`, `completed`, `in_progress`, `blocked`, `decisions`, `failed_attempts` (arrays of strings); `changed_files` (array of `{path: relative POSIX-style path, owner: agent name}` objects); `validation` (array of `{command: string, result: passed|failed|not_run|unknown, evidence?: string}` objects); `worktree`, `branch`, `head` (strings). Unknown top-level fields rejected. Unspecified optional arrays default to empty conceptually (not rewritten into input payload). No embedded commands are executed.

`validation.result=passed` is **an unverified claim from the submitting agent**. It is never converted to official project approval. Collect timestamp, exit code, and artifact hashes before future automatic verification features. `completed` is also an agent claim, not a release gate.

## Persisted envelope

The core adds `schema_version: 1`, `writer_version`, `id` (UTC timestamp + 12 hex characters), `project_id` (local path hash, **not a cross-clone identity**), `revision` (optimistic concurrency counter), `status` (`open` or `archived`), `created_at`, `updated_at`, `git_observation` (observed branch/HEAD/dirty state, nullable), `payload`, `claims_are_unverified: true`.

`schema_version` describes the persisted envelope; `writer_version` describes runtime compatibility. v1 readers reject unsupported versions; do not silently upgrade data. The `payload` is not cryptographically authenticated; treat all fields as untrusted content. Path hash is local metadata and can still potentially correlate user installations; inspect before publishing.

## Git observation

`git_observation` = `{branch, head, dirty}` taken when the record is written; `dirty` ignores `.handoffs/` (the tool's own lock and session files). Imported legacy records store all three as `null`. `resume` adds `head_relation`, `commits_since_saved`, `file_checks`, `validation_claims` and `warnings`; none of them are persisted.

## `depth`

`write` records `depth` (`minimal|rich|exhaustive`): a payload-completeness policy chosen by `--depth` (default `auto` = highest satisfied) and enforced before saving. It says nothing about whether the content is true. Records written before 0.2.0 + depth lack the key; readers must treat it as absent. Rules: see `docs/USER_GUIDE.md`.

## Optional `legacy_import` object

Present only on sessions created by `import-legacy`: `format` (`claude-handoff-skill v1`), `source_file`, `source_sha256`, `imported_at`, `created_at_is_approximate: true`, `original_text`. The text is untrusted data like every other field. v1 readers ignore unknown top-level keys; `payload` still obeys the input contract above.

## Invariants and limitations

- Session ID and revision are managed by the core, never by the model.
- Updates require both session ID and `--expected-revision` to detect stale writers.
- `changed_files[].path` is metadata only; no file is opened or changed by following those paths.
- Common credential-like patterns are **rejected**, not silently redacted. Pattern matching is incomplete; perform human review before sharing.
- Maximum payload source file: 256 KB; session data are locally stored and may contain sensitive context even when screening passes.
- `resume` only returns stored data, fresh Git observations and differences. Never execute commands in a record automatically.
- `archive` and `restore` are transitions, not permanent deletion. A crashed transition may require manual repair after `doctor` detects a status/location mismatch.
- `project_id` is not stable across clones/worktrees. A normalized remote-based project identity and schema migrations are future work.
