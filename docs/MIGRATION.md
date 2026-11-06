# Legacy adoption and migration

## Existing ④ (`agent-handoff`)

Check for `AGENT_HANDOFF.md` and `.agent-handoff/*.md`; read ④'s existing marker blocks. Keep them intact. Do not overwrite, delete, or convert on first run. A future migration routine may add marked guidance only with an approved reconciliation plan.

## Existing ③ (`claude-handoff-skill`)

Check `.handoffs/*.md` and optional central index (`~/.claude/handoffs/INDEX.md` or `HANDOFF_INDEX_PATH`). Import source Markdown to the new session store with checksum, source path and provenance. Preserve the originals until explicit cleanup confirmation. A central index may contain user-specific project names/paths and must not be committed by default.

## Migration command (planned)

```text
handoff migrate --from claude-handoff --dry-run
handoff migrate --from claude-handoff --confirm
```

## Migration tests

- Repeat migration; no duplicate sessions.
- Legacy handoff still readable if migration fails.
- Source file checksum, timestamp, status and quoted constraints retained.
- Backward compatibility when only some metadata is present.
- Reconcile two versions of same session without silently losing either.
