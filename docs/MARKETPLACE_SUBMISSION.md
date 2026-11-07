# Official marketplace submission — preparation only (nothing was submitted)

Status 2026-11-07: **not submitted.** Submitting is a public, outward-facing action and needs the owner's explicit approval. This page records what the two directories ask for (read from their public repositories on 2026-11-07) and where this project stands. Re-read the sources before submitting; both change.

## 1. Anthropic: `anthropics/claude-plugins-official`

- Source: its `README.md` ("External Plugins"). Third-party plugins are submitted through the **plugin directory submission form** linked there (https://clau.de/plugin-directory-submission); there is no PR route described for outsiders. "External plugins must meet quality and security standards for approval."
- Not machine-checkable by us: the review criteria are not published in that README. Do not assume acceptance.
- What we already have: valid manifests (`claude plugin validate .` passes), the plugin installs and runs from a real GitHub-hosted marketplace (`docs/MARKETPLACES.md`), MIT license, pinned release `v0.2.0-pilot`.
- Gaps to disclose in the form: experimental pilot, Windows-only host verification, no signatures, the skill executes a local Python script the user installs (stdlib only, no network).

## 2. GitHub: `github/awesome-copilot`

- Source: its `CONTRIBUTING.md`. Public external plugins go through an **issue form**, not a PR editing `plugins/external.json`. GitHub-hosted public repositories only (`source.source: "github"`).
- Fields the form collects (as documented): plugin name; short description; `owner/repo`; plugin path (optional at repo root); **ref = release tag or tag ref, not a branch**; **full 40-char commit SHA**; plugin version; license identifier; author name; optional author URL and homepage.
- Automated gates that must pass: Agent Plugins v1.0.0 manifest compliance (root `plugin.json`, `$schema`; the root manifest is authoritative when legacy manifests coexist); `vally lint` (Agent Skills spec + valid file references for bundled skills); an install smoke test through Copilot CLI; version matching between submission and manifest, and ref/SHA consistency. Failures block; maintainers then review manually (`/approve`, `/reject`).
- "What we don't accept" includes content that only repeats what frontier models already do well without clear uplift and anything that weakens security. Our case for uplift: a deterministic, auditable handoff store with explicit claim/verification separation. A maintainer decides.

### Our values for that form (verify again at submission time)

| Field | Value |
|---|---|
| Plugin name | `agent-handoff-manager` |
| Repository | `rch4com/agent-handoff-manager` |
| Path | repository root (root `plugin.json` present) |
| Ref | `v0.2.0-pilot` (annotated tag, exists) |
| Commit SHA | `041af4963a487c21f739d483c74ae268fadad811` (what the tag points to; confirm with `git rev-parse v0.2.0-pilot^{commit}`) |
| Version | `0.2.0` (all manifests match core `VERSION`; `tests/test_versions.py`) |
| License | `MIT` |
| Author | `rch4com` |

### Local pre-checks we could and could not do

- Done: Copilot CLI `marketplace add` -> `browse` -> `install` from the public repo, installed skill runs; root `plugin.json` has `$schema`; manifest versions match the core; Agent Skills frontmatter (`name` equals the folder, `license`, `description`) passes `gh skill publish --dry-run`.
- **Not done: running `vally lint`.** Fetching and executing an unreviewed npm package was denied by the permission policy and we did not work around that. Note the trap: `npx vally` is an unrelated package (an ES6 form-validation library); the gate uses `@microsoft/vally-cli` (MIT, 0.21.0 on 2026-11-03). Someone should review that package, run it against the tag and fix findings before submitting.
- **Done instead (reading the public gate source `eng/external-plugin-quality-gates.mjs` / `eng/agent-plugin-schema.mjs`, no code from it was run):** `tests/test_agent_plugin_manifest.py` re-implements the documented manifest rules in stdlib code and our root `plugin.json` passes: `$schema` equals the schema URL; `name` 1-64 chars matching the pattern; non-empty `version`/`description`; `author` only `name`/`email`/`url`; only allowed top-level fields (`$schema name version description author homepage repository license keywords extensions`). The same test checks SKILL.md frontmatter (name equals folder and is lowercase-hyphen, description 1-1024 chars, license) and that SKILL.md has no dangling `scripts/...` references. This does not replace the real gate.
- **What the gate does with skills (from its source):** it reads skill directories from a `skills` field of plugin.json, but `skills` is **not** an allowed top-level field in Agent Plugins v1.0.0, so for our plugin it falls back to linting the whole plugin root. What `vally` reports for a whole repository root (our docs, tests, fixtures) is unknown and is the main risk. If it complains, the likely fix is a smaller dedicated plugin directory, which means a new tag and new SHA values in the table above.

### Review of `@microsoft/vally-cli@0.21.0` (metadata and source read on 2026-11-07; run still pending)

- Downloaded with `npm pack --ignore-scripts` into an isolated scratch folder and read, not executed. MIT, `bin: vally`, Node >= 22.15. The CLI package itself has no `preinstall/install/postinstall` script. README: `vally lint` = "fast static checks (no execution)".
- **Telemetry is ON by default** (Azure Application Insights, hard-coded connection string in `dist/usage-telemetry/config.js`). Opt-out env vars that the source honors: `DO_NOT_TRACK=1` or `VALLY_TELEMETRY_OPTOUT=1`. Always set one of them.
- Installed into an empty folder with `npm install --ignore-scripts` (181 packages). In that dependency tree exactly one package has an install-time script: `koffi` (`node ./cnoke.cjs ... --prebuild`, a native FFI library); it was skipped by `--ignore-scripts`. Whether `lint` needs it is unknown.
- Running it was denied by the permission policy ("code from external") and not retried. A human can run it with:

```bash
DO_NOT_TRACK=1 VALLY_TELEMETRY_OPTOUT=1 node "<scratch>/vally-run/node_modules/@microsoft/vally-cli/dist/index.js" lint "<repo>/skills/agent-handoff-manager"
DO_NOT_TRACK=1 VALLY_TELEMETRY_OPTOUT=1 node "<scratch>/vally-run/node_modules/@microsoft/vally-cli/dist/index.js" lint "<repo>"     # what the intake gate falls back to for our plugin
```

  (`<scratch>` is the session scratchpad; recreate with `npm install @microsoft/vally-cli@0.21.0 --ignore-scripts` in an empty folder.) Record the output in `PROJECT_TRACKER.md` and fix findings before any submission.

## 3. Decision needed from the owner

1. Submit to one, both, or neither directory.
2. If submitting: run/review `vally lint` first, then use the table above; any fix means a new tag and updated values.
3. Keep `docs/MARKETPLACES.md` and `docs/RELEASE_GATES.md` in sync with the outcome (they currently say "not submitted").
