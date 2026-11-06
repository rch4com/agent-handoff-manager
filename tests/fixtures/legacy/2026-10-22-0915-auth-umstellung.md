<!-- HANDOFF-DOC v1 — agent-agnostic resume protocol -->

> **You are reading a handoff document.** A previous agent has handed off its
> working state so you can continue seamlessly. This doc is not a memo — it is
> your input instruction.
>
> **MANDATORY steps BEFORE you do anything:**
>
> 1. **Read the entire doc** (including Section 4 "Decisions & Constraints"
>    and Section 7 "Pitfalls"). No action without full context.
> 2. **Verify the env snapshot** (Section 6): Are you in the right working
>    directory? Does the git branch match? Are the listed processes still
>    running? If not: STOP, report the discrepancy to the user.
> 3. **Read referenced artifacts** (Section 8) if critical context lives there.
> 4. **Confirm to the user in 3–5 lines**: mission understood, next step per
>    Section 3 is X, risks per Section 7 are Y. Ask explicitly:
>    "Should I begin with the next step?"
> 5. **Only act after user confirmation.** Respect verbatim-quoted constraints
>    in Section 4 — the previous agent did not add them for decoration.
>
> **If you are Claude Code with the `handoff` plugin:** Run
> `/handoff:handoff-resume <path-to-this-doc>` — the skill orchestrates steps 1–4
> automatically and marks the index status.
>
> **If you are a different agent** (Codex, Cursor, Gemini, GPT, …): You have
> no skills/slash-commands, but the 5 steps above are all you need. Treat them
> as your immediate TODO list.

---

# Handoff: Auth-Modul auf JWTVerifier umstellen

> **Status:** open · **Created:** 2026-10-22 09:15 · **Project:** shop-backend
> **Original Agent:** Claude Code (claude-opus-4) · **Depth:** exhaustive

<!-- The status above is the state at creation time and is NOT kept up to date. Current status: INDEX.md (single source of truth). -->

## 1. Mission

Replace the hand-rolled token check in the auth handlers with the new `JWTVerifier` class so expired tokens are rejected consistently.

## 2. Current State

- ✅ Done: `JWTVerifier` implemented in `src/auth/verifier.py`; unit tests for expiry pass locally
- ✅ Done: login handler migrated
- 🔄 In Progress: `validateToken` in `src/handlers/auth.ts` (about half migrated)
- ⏸️ Blocked: waiting for the security team to confirm the clock-skew tolerance

## 3. Next Step

Edit `src/handlers/auth.ts:142` — switch `validateToken` to use the new
`JWTVerifier` class. Then run `npm test -- auth.test.ts` to confirm.

## 4. Decisions & Constraints

**Dependencies:**
> "Do not add new npm packages for this."
Reason: audit freeze
Constraint: use only what is already in package.json

## 5. Changed Files

| File | Lines | Status | Note |
|------|-------|--------|------|
| src/auth/verifier.py | new | created, uncommitted | new class |
| src/handlers/auth.ts | 120-160 | modified, uncommitted | half migrated |
| `docs/한글 설계.md` | new | created | non-ASCII path |

## 6. Env Snapshot

- **Working Directory:** /home/dev/shop-backend
- **Git Branch:** feature/jwt-verifier
- **Dirty Files:** 3

## 7. Pitfalls & Learnings

Tried patching `validateToken` in place: broke refresh flow. Use the verifier instead.

## 8. References

- **Plan/Spec:** docs/plans/jwt.md

## 9. Open Questions (for user, not agent)

Clock-skew tolerance: 30s or 60s? Blocks section 2 item 4.

## Appendix: Conversation Gist

- User asked for consistent expiry handling.
