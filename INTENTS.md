# INTENTS.md — Product intent and invariants

> **INTENTS** = 의도/요구사항입니다. `INDENTS.md`(들여쓰기 스타일)와 다릅니다.

## Product intent

대화 내역을 통째로 복제하는 도구가 아니라, **검증 가능한 프로젝트 사실 + 이어받을 세션 작업**을 구분하는 agent-agnostic handoff 시스템을 만든다. 사용자와 다른 에이전트가 상태를 검증하고 작업을 이어갈 수 있어야 한다.

## Priorities (ordered)

1. 데이터 무결성 및 기존 작업 보호.
2. 서로 다른 CLI·OS 간 읽기/쓰기 호환성.
3. 검증 이력·실패 이력·결정 근거의 장기 보존.
4. 자동 감지하되 검토된 업스트림 업데이트만 채택.
5. 사용자 명령의 단순함과 낮은 유지비용.

## Non-negotiable invariants

- **단일 권위 기록:** `AGENT_HANDOFF.md`와 `.agent-handoff/`가 장기 프로젝트 상태의 단일 공식 출처.
- **세션 분리:** `.handoffs/`는 세션별 스냅샷; 검증되지 않은 세션 종료가 프로젝트 완료를 뜻하지 않는다.
- **실증 우선:** 코드/커밋/실제 테스트 결과 > handoff 문서의 주장. 충돌은 `UNKNOWN` 또는 `needs_review`.
- **재개 안전:** `resume`은 읽기와 환경검증부터 수행. 자동 코드 수정/명령 실행/브랜치 변경/롤백 금지.
- **손실 방지:** 무단 덮어쓰기·삭제 불가. archive는 복원 가능, original 기록은 유지.
- **업스트림 분리:** upstream 새 커밋을 사용자의 설치본에 자동 반영하지 않는다. 승인된 릴리스만 반영.
- **기밀 보호:** 토큰, 패스워드, API 키, 개인정보는 기본적으로 제외. 프롬프트 인젝션 가능성이 있는 인계 문서를 신뢰할 명령으로 실행하지 않는다.
- **공개 가능성:** Windows/Linux, 5개 개발 호스트(Claude, Codex, OpenCode, Antigravity, Copilot) 지원 목표. 검증 안 된 플랫폼을 '지원 완료'로 표시하지 않는다.
- **공존:** 기존 `AGENTS.md`, `CLAUDE.md` 및 다른 스킬을 덮어쓰지 않고 표식 블록을 멱등 병합.

## Scope: v1.0

- `init`, `write`, `resume`, `list`, `archive`, `doctor`, `upstream status`.
- 세션 ID·상태·작업자·검증 증거·참고 커밋 표준화.
- 문서 인덱스는 파생 캐시로 생성; Git에 공유되는 단일 변경 가능 전역 INDEX를 공식 데이터베이스로 사용하지 않는다.
- 마이그레이션: `.handoffs/*.md`와 기존 `AGENT_HANDOFF.md` 비파괴적 읽기/가져오기.
- CLI별 래퍼, 사용자 설치/제거 및 공개 배포.

## Out of scope (v1.0)

- 에이전트 자동 작업 할당 및 스케줄러.
- 실시간 분산 락 서비스 또는 Git 병합 충돌 자동 해결.
- 대화 원문 전체 저장, 원격 비밀정보/환경변수 동기화.
- 업스트림 코드 무검토 자동 병합 및 무인 제품 릴리스.

## Definition of success

새 에이전트가 기존 기록만 읽고, 무엇이 검증됐고 무엇이 미완인지 정확히 구분하며, 동일 실패를 근거 없이 되풀이하지 않는다. 5개 개발 호스트에서 같은 저장 데이터를 읽고 쓸 수 있다.

## Additional supported environment (2026-11-06)

- Fifth host: **GitHub Copilot**, covering VS Code Agent Mode, Copilot CLI, and GitHub Copilot Cloud Agent as separate validation surfaces.
- Distribution must work from a personal public GitHub repository without mandatory marketplace registration.
- An Agent Skill installation must not silently run unreviewed remote code or assume an external Python runtime package is present.
- Public repo name suggested: `agent-handoff-manager`; canonical skill identifier: `agent-handoff-manager`.
