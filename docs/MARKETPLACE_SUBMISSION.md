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
- **Not done: `vally lint`.** It was not run because fetching and executing an unreviewed npm package was denied by the permission policy and we did not work around that. Someone should review the `vally` source, run it against the tag, and fix findings before submitting. Unknown result: it may flag things (for example the plugin manifest's skill path or file references) that we have not seen.
- One thing to watch: the tag points at a commit whose `plugin.json` does not declare the skill path explicitly; the Copilot CLI discovered it by convention. If the lint requires an explicit entry, a new tag (v0.2.1-pilot) is needed, since the submission must reference a tag and a SHA that contain the fix.

## 3. Decision needed from the owner

1. Submit to one, both, or neither directory.
2. If submitting: run/review `vally lint` first, then use the table above; any fix means a new tag and updated values.
3. Keep `docs/MARKETPLACES.md` and `docs/RELEASE_GATES.md` in sync with the outcome (they currently say "not submitted").
