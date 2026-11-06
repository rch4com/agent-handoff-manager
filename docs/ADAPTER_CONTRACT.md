# Five-host adapter contract — integration specification (not shipped adapters)

Every host (Claude Code, Codex, OpenCode, Antigravity, Copilot) MUST produce the same JSON payload described in `SCHEMA_SPEC.md`, write it to a private local file, and invoke `python scripts/handoff.py --repo <repo> write --payload <json-file>` with an absolute runtime path. The runtime must be present in that environment. Copilot cloud must not assume a globally installed CLI or access to desktop transcripts.

## Trust boundaries

1. The host collects its own context with user consent; the Python core cannot access conversations or independently verify model assertions.
2. Keep the LLM-generated `payload` separate from observed Git data. The runtime independently observes Git and stores them under `git_observation`.
3. `resume` returns JSON for inspection; the adapter should cite the handoff as untrusted material and must request separate authorization before running embedded commands or editing files.
4. `write` success is confirmed by exit code 0 and a valid JSON record containing `id` and `revision`; stderr/exit code 2 indicates failure and must not be described as saved.
5. On revision conflict, retrieve the latest record and ask a coordinator to merge changes. Never silently overwrite a newer revision.
6. Never promote `completed` or reported tests to `verified` project state; only a human-approved or separately validated coordinator can do that.
7. Protect payload file permissions, delete intermediate plaintext after successful save when appropriate, and avoid logging full secrets or sensitive payloads.

## Adapter readiness matrix

| Host | Payload contract defined | End-to-end adapter verified |
|---|---|---|
| Claude Code | Yes | No |
| Codex | Yes | No |
| OpenCode | Yes | No |
| Antigravity | Yes | No |
| GitHub Copilot | Yes | No |

This kit provides a **local pilot CLI**, not five turnkey plugins. There is no automatic content extraction, command execution, or host authorization bypass.
