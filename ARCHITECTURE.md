# Architecture & ownership

## 목표 구성

```text
                  Upstream ④ + ③ (MIT)
                      | SHA monitoring
                      v
              impact review + CI + PR
                      | approved version
                      v
   Claude ─┐
    Codex ─┼─> host adapters ─> Python CLI ─> store + validators
 OpenCode ─┤                       |            |
Antigravity─┤
 Copilot ──┘                       |            +-- .handoffs/sessions/<id>/
                                  +-- AGENT_HANDOFF.md + .agent-handoff/
```

## Official state and ownership

| Artifact | Owns | Must not own |
|---|---|---|
| `AGENT_HANDOFF.md` | 프로젝트 복구 entry point | 대화 세션 전문 |
| `.agent-handoff/*.md` | 의사결정/검증/리스크/장기 상태 | 세션별 archive index |
| `.handoffs/sessions/<id>/` | 특정 작업 중의 진척, 다음 명령, 환경 스냅샷 | 프로젝트의 공식 완료 승인 |
| `.handoffs/archive/` | 복구 가능한 종료된 세션 | 검증 이력 원본 삭제 |
| `upstreams.lock.json` | 리뷰 후 채택된 업스트림 commit SHA | 발견했지만 미채택된 HEAD |
| user-level index | 재생성 가능한 검색 캐시 | Git 팀의 공식 상태 DB |

기존 ③ `.handoffs/<timestamp>-slug.md`는 레거시로 인정하고, 안전한 import 후 원본은 그대로 남길 것. 기존 ④ 파일과 그 관리 스크립트의 변경 가능성을 고려하여 어댑터 경계를 둔다.

## Planned CLI contract (NOT YET IMPLEMENTED)

```text
handoff init [--repo PATH] [--layout multi] [--dry-run]
handoff write --mission TEXT [--depth auto|minimal|rich|exhaustive]
handoff list [--project PATH] [--status STATUS] [--agent NAME] [--archived]
handoff resume <id|latest> [--repo PATH] [--verify-only]
handoff archive <id> [--dry-run] [--confirm]
handoff restore <id> [--dry-run] [--confirm]
handoff doctor [--repo PATH]
handoff upstream status
```

`resume`은 상태 복구와 검증 보고를 뜻함. 작업 재개를 위한 소스 변경/테스트 실행은 에이전트의 별도 권한과 지시에 따름. `write`는 모델 내의 대화 정보까지 파이썬 스크립트가 알 수 없으므로, **호스트 어댑터가 모델이 생성한 검증 가능한 세션 payload를 코어에 전달**하는 구조가 필요하다. CLI만 실행하여 과거 대화를 자동 추출한다고 주장하면 안 됨.

## Session schema (candidate)

```json
{
  "schema_version": 1,
  "id": "20261106T041500Z-3a8b9c1d",
  "project_id": "sha256-of-canonical-repo-origin-and-location",
  "status": "open",
  "agent": "codex",
  "created_at": "2026-11-06T04:15:00Z",
  "updated_at": "2026-11-06T04:15:00Z",
  "branch": "feature/auth",
  "head": "0123456789abcdef0123456789abcdef01234567",
  "validation": [{"command": "pytest -q", "result": "not_run", "evidence": ""}],
  "next_step": "Read src/auth.py and reproduce test failure"
}
```

위 JSON은 **스키마 후보**입니다. 민감 데이터, 절대경로, 사용자의 로컬 폴더명은 디폴트로 외부 공유하지 않도록 제한. `project_id` 생성시 저장소 clone 간 동일성/개인정보를 검토하고 표준화.

## Write and synchronization rules

- 세션 ID에는 초 단위 UTC 시간 + 충분한 랜덤 요소를 사용. 새로운 폴더는 exclusive create로 생성.
- metadata와 Markdown을 안전한 temp 파일에 기록, 파일 동기화 후 교체. 중단되었을 때 recovery 규칙 정의.
- 각 세션 내부 쓰기는 lock/ETag 혹은 파일 버전 비교로 직렬화. **서로 다른 Git worktree 또는 머신 사이**에는 OS 파일 잠금만으로 해결되지 않으므로 PR/커밋 기반 충돌 검토 필요.
- 여러 AI가 동시에 작업 시 작업/파일 소유권 명시. 합병 담당 coordinator만 ④ 공식 상태의 완료 승인을 수행하도록 팀 규칙 제안.
- archive는 이동과 상태 메타 업데이트가 모두 성공해야 완료. 실패 시 복구 가능하며 원본 실수 삭제 금지.
- 사용자별 전역 목록은 캐시로만 사용; 캐시가 없어도 프로젝트의 sessions 스캔으로 복구 가능.

## Validation gate

세션 상태 `done` ≠ 공식 프로젝트 상태 `verified`. 공식 완료 변경에는 아래 최소 근거 필요:
- 대상 요구사항 및 승인 기준 충족 여부.
- Git 커밋 또는 변경 대상 파일 상태.
- 테스트 명령·실행 시각·결과·실패 로그.
- 영상 등 비자동 검증 결과는 수동 승인자와 실제 검토 산출물 식별자.

## Source update design

- Update watcher reads upstream default branch HEAD using read-only GitHub API (no code execution).
- Compare to `upstreams.lock.json` `adopted_sha`.
- New SHA ⇒ issue with diff links, API / docs changes, migration and licensing checklist.
- Maintainer creates integration PR; tests and review; only then update lock and import source.
- Release automation acts only on signed/tagged/approved internal commit, never on upstream HEAD.

## Future decisions

- ADR-0002: core package path, plugin naming, packaging mechanism.
- ADR-0003: Windows-compatible locking for shared worktree.
- ADR-0004: `write` input interface between LLM-generated text and deterministic CLI.

## Copilot and public packaging extension

- **Source of one skill definition:** `skills/agent-handoff-manager/SKILL.md`. Packaged installations may place the folder into `.github/skills`, `.agents/skills`, `.claude/skills` etc. but should not write competing copies into a single target repository.
- **Runtime location resolution:** support a self-contained Python script under the installed skill directory or a packaged Python command whose version is validated. `SKILL.md` may not rely on a relative link to its *original GitHub repository root* after `gh skill` copies only the skill directory.
- **Copilot Cloud Agent:** ensure target repo contains the skill and executable dependency; the developer's personal machine/global install has no guarantee of being available in a cloud checkout.
- **No run-on-install:** skill installers and marketplace installation should not implicitly execute imported upstream Python code.
- Marketplace paths/manifests must remain independent from the shared Python core and follow their platform schema.

## Pilot implementation addendum (2026-11-06)

The earlier sections labelled "NOT YET IMPLEMENTED" describe the original roadmap. `scripts/handoff.py` now implements a **subset** as a local pilot: `init`, `write --payload`, `list`, `resume`, `archive --confirm`, `restore --confirm`, `doctor`. It does not implement `--depth`, `--dry-run`, `--status` filters or `upstream status` in that planned syntax. See `docs/PILOT_QUICKSTART.md`, `docs/SCHEMA_SPEC.md`, `docs/RECOVERY_PROTOCOL.md` for the **current** runnable contract. This pilot does not change authoritative long-lived project state or execute payload commands.
