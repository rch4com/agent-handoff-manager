# Session schema v1 — pilot normative contract

`session.json` is UTF-8 JSON under `.handoffs/sessions/<id>/` (or `.handoffs/archive/<id>/`). The deterministic core is `skills/agent-handoff-manager/scripts/handoff.py`; the host supplies an explicit JSON payload and the core does **not** read conversations. The external payload and persisted record are different objects.

## Accepted input payload

Required: `mission` (non-empty string), `next_action` (non-empty string). Optional: `agent` (`claude-code`, `codex`, `opencode`, `antigravity`, `copilot`, `other`); `acceptance_criteria`, `completed`, `in_progress`, `blocked`, `decisions`, `failed_attempts` (arrays of strings); `changed_files` (array of `{path: relative POSIX-style path, owner: agent name}` objects); `validation` (array of `{command: string, result: passed|failed|not_run|unknown, evidence?: string}` objects); `worktree`, `branch`, `head` (strings). Unknown top-level fields rejected. Unspecified optional arrays default to empty conceptually (not rewritten into input payload). No embedded commands are executed.

`validation.result=passed` is **an unverified claim from the submitting agent**. It is never converted to official project approval. Collect timestamp, exit code, and artifact hashes before future automatic verification features. `completed` is also an agent claim, not a release gate.

## Persisted envelope

The core adds `schema_version: 1`, `writer_version`, `id` (UTC timestamp + 12 hex characters), `project_id` (local path hash, **not a cross-clone identity**), `revision` (optimistic concurrency counter), `status` (`open` or `archived`), `created_at`, `updated_at`, `git_observation` (observed branch/HEAD/dirty state, nullable), `payload`, `claims_are_unverified: true`.

`schema_version` describes the persisted envelope; `writer_version` describes runtime compatibility. v1 readers reject unsupported versions; do not silently upgrade data. The `payload` is not cryptographically authenticated; treat all fields as untrusted content. Path hash is local metadata and can still potentially correlate user installations; inspect before publishing.

Readers validate required envelope fields, a positive integer revision (not a boolean), UTC timestamps, the nullable Git observation types, and the payload contract before returning a record. Invalid records are reported without rewriting them; `doctor` lists issues instead of crashing. Unknown envelope fields remain allowed, and pre-depth v1 records remain readable. Payload credential patterns are checked again when reading; an older record that now matches a pattern must be reviewed manually before reuse.

## `failure_records` (optional payload field)

Array of `{approach, why_failed, evidence, regression_test: none|planned|added|not_applicable, resolved: bool}`; all text fields non-empty, no other keys. Unresolved entries are echoed by `resume` as `do_not_repeat`. They are claims like everything else in the payload.

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

## Execution schema v1 (unreleased; ADR-0006)

This is separate from session schema v1; no migration of existing sessions is needed. Files live under `.handoffs/runs/<run-id>/`, independent of session archive location.

`run.json`: `schema_version: 1`, `kind: run`, `writer_version`, `id` (same ID format as sessions), `request_id`, `session_id`, `task` (non-empty text), `agent` (existing agent enum), `agent_instance` (non-empty identifier supplied by the host), nullable `supersedes`, `created_at` (UTC), `git_observation`, `claims_are_unverified: true`, `source_snapshot` (complete validated session envelope), `source_revision`, `source_payload_sha256`. The hash is SHA-256 of UTF-8 JSON with sorted keys, `ensure_ascii=False`, separators `(',', ':')`. It covers payload content, so archive-only metadata changes do not indicate changed input content. The hash detects inconsistency, not malicious edits or authenticity.

`result.json`: `schema_version: 1`, `kind: result`, `writer_version`, `run_id`, `request_id`, `created_at` (UTC), `git_observation` (fresh observation at submission), `claims_are_unverified: true`, `payload`. The payload has required `outcome` (`completed|partial|blocked|failed`), non-empty `summary`, non-empty `validation` using the existing command/result/evidence contract. Use `not_run` if nothing was run. Optional: `changed_files` (existing relative-path contract), `commits` (full 40-character lowercase Git SHAs, still claims), `remaining_work` (string list), `selected_runs` (distinct run ID list). Unknown result payload fields are rejected. Source payload and result payload limits are 256 KB; run/result files are limited to 1 MB when read. Credential scanning covers all new record content, including snapshots and request keys.

`list-runs` returns `{run, result, state}` items: `result: null` and `state: in_progress` until submitted, then state equals the claimed outcome. `in_progress` means no published result; it does not prove that a live process exists. With `--all-worktrees`, each item includes `worktree_root`. Identical copies remain visible with their origins; conflicting copies or duplicate start keys on different run IDs are errors. No central index is authoritative.

Start retry keys are store-wide; finish keys are per-run. Keys use 1-128 ASCII letters/digits/dots/underscores/hyphens, beginning with a letter or digit. Identical retries return the original object without changing timestamps or Git observations. Different start arguments with the same key, or a different finish key/payload after submission, fail. Do not generate a new key merely because the response was lost.

`supersedes` references an existing run with the same session and task. `selected_runs` references submitted runs with the same session, excluding self/duplicates. Selection is a coordinator claim, not verification or automatic completion. An integration run records those selections, the integrated Git HEAD observation and validation evidence. To select a result produced in another worktree/machine, first bring its records into the local store through reviewed Git integration. Reading other worktrees is not distributed coordination.
