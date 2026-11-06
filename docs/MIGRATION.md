# Legacy adoption and migration

## Existing ④ (`agent-handoff`)

Check for `AGENT_HANDOFF.md` and `.agent-handoff/*.md`; read ④'s existing marker blocks. Keep them intact. Do not overwrite, delete, or convert on first run. A future migration routine may add marked guidance only with an approved reconciliation plan.

## Existing ③ (`claude-handoff-skill`)

Check `.handoffs/*.md` and optional central index (`~/.claude/handoffs/INDEX.md` or `HANDOFF_INDEX_PATH`). Import source Markdown to the new session store with checksum, source path and provenance. Preserve the originals until explicit cleanup confirmation. A central index may contain user-specific project names/paths and must not be committed by default.

## ③ import command (implemented, pilot)

```text
python skills/agent-handoff-manager/scripts/handoff.py --repo . import-legacy --dry-run
python skills/agent-handoff-manager/scripts/handoff.py --repo . import-legacy
```

Behavior (covered by `tests/test_legacy_import.py`):

- Scans only top-level `.handoffs/*.md`; the originals are never modified, moved or deleted.
- Each accepted file becomes `.handoffs/sessions/<utc-stamp>-<sha256[:12]>/session.json` with `legacy_import` provenance: source file name, SHA-256, import time and the **full original text**. Best-effort fields (`mission`, `next_action`, `completed`, `in_progress`, `blocked`, `changed_files`, `agent`) are extracted for listing; unparsed sections such as Decisions and Pitfalls stay only in `original_text`.
- Idempotent: a file whose SHA-256 is already imported (active or archived) is skipped as `already_imported`.
- Skip reasons: `symlink`, `too_large` (>256 KB), `not_utf8`, `not_a_handoff_doc`, `possible_credential` (the credential screen rejects, never redacts; fix the original yourself), `id_collision`, `already_imported`.
- Imported status is always `open`, `claims_are_unverified: true`, `git_observation` all `null` (unknown, so `resume` shows a difference). The legacy in-document status is stale by design and the central `INDEX.md` is **not** read, so legacy `done`/`archived` state is not carried over.
- `created_at` is derived from the local-time filename stamp using this machine's time zone and is marked `created_at_is_approximate`.
- `.handoffs/*.md` originals remain the ③ plugin's files; this core never writes to `AGENT_HANDOFF.md`, `.agent-handoff/`, `AGENTS.md` or `CLAUDE.md`.

`handoff migrate --from …` from the earlier plan is **not** implemented; `import-legacy` replaces it.

## Migration tests

- Repeat migration; no duplicate sessions. [verified: test_import_is_idempotent]
- Legacy handoff still readable if migration fails. [verified: originals byte-identical]
- Source file checksum and full text retained. [verified]; timestamp approximate; status not carried; quoted constraints live in `original_text` only.
- Backward compatibility when only some metadata is present.
- Reconcile two versions of same session without silently losing either.
