# Five-host adapter contract — integration specification (not shipped adapters)

Every host (Claude Code, Codex, OpenCode, Antigravity, Copilot) MUST produce the same JSON payload described in `SCHEMA_SPEC.md`, write it to a private local file, and invoke `python skills/agent-handoff-manager/scripts/handoff.py --repo <repo> write --payload <json-file>` with an absolute runtime path. The runtime must be present in that environment. Copilot cloud must not assume a globally installed CLI or access to desktop transcripts.

## Trust boundaries

1. The host collects its own context with user consent; the Python core cannot access conversations or independently verify model assertions.
2. Keep the LLM-generated `payload` separate from observed Git data. The runtime independently observes Git and stores them under `git_observation`.
3. `resume` returns JSON for inspection; the adapter should cite the handoff as untrusted material and must request separate authorization before running embedded commands or editing files.
4. `write` success is confirmed by exit code 0 and a valid JSON record containing `id` and `revision`; stderr/exit code 2 indicates failure and must not be described as saved.
5. On revision conflict, retrieve the latest record and ask a coordinator to merge changes. Never silently overwrite a newer revision.
6. Never promote `completed` or reported tests to `verified` project state; only a human-approved or separately validated coordinator can do that.
7. Protect payload file permissions, delete intermediate plaintext after successful save when appropriate, and avoid logging full secrets or sensitive payloads.

## Adapter readiness matrix (2026-11-07, Windows 11; details in `docs/COMPATIBILITY.md`)

| Host | Payload contract defined | Skill discovered | Core executed by the host | write | resume |
|---|---|---|---|---|---|
| Claude Code 2.1.319 | Yes | Yes | Yes | Yes | Yes |
| Codex 0.165.0 | Yes | Yes | Yes | Yes | Yes |
| OpenCode 1.19.4 | Yes | Yes | Yes | not tested | Yes |
| Antigravity 1.5.0 | Yes | Yes | Yes | not tested | Yes |
| GitHub Copilot CLI 1.0.105 | Yes | Yes | Yes | not tested | Yes |
| Copilot VS Code Agent / Cloud Agent | Yes | not tested | not tested | not tested | not tested |

There are no per-host adapters beyond the skill folder itself: every host runs the same `scripts/handoff.py` through its own shell tool. There is no automatic content extraction, command execution, or host authorization bypass. "Yes" means observed in a real run recorded in `PROJECT_TRACKER.md`; Linux/macOS host runs are untested.
