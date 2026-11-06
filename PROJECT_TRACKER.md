# PROJECT_TRACKER.md — 개발 진척 및 증거

> 완료 기준: 코드 존재가 아닌 **실행 테스트 통과 + 근거 기록**. 최초 상태를 완료라고 과장하지 마세요.

| ID | 항목 | 상태 | 증거 (커밋/PR/테스트) | 소유자 | 다음 행동 |
|---|---|---|---|---|---|
| P0-01 | ④ 원본 구조 조사 | TODO | README 링크만 확인 | 미지정 | 소스/버전 고정 |
| P0-02 | ③ 원본 구조 조사 | TODO | README 링크만 확인 | 미지정 | 실제 skill 명세 조사 |
| P0-03 | 두 MIT 원본 고지 | TODO | 웹 라이선스 존재 확인 | 미지정 | 실제 파일 및 고지 포함 |
| P1-01 | 세션 스키마/스토리지 | TODO | 없음 | 미지정 | 구현 |
| P1-02 | 레거시 이관 | TODO | 없음 | 미지정 | 구현 |
| P2-01 | write | TODO | 없음 | 미지정 | 구현 |
| P2-02 | resume | TODO | 없음 | 미지정 | 구현 |
| P2-03 | list | TODO | 없음 | 미지정 | 구현 |
| P2-04 | archive/restore | TODO | 없음 | 미지정 | 구현 |
| P2-05 | doctor | TODO | 없음 | 미지정 | 구현 |
| P3-01 | 공식 상태와 세션 통합 | TODO | 없음 | 미지정 | 구현 |
| P4-01 | Claude 어댑터 | TODO | 없음 | 미지정 | 구현 및 시험 |
| P4-02 | Codex 어댑터 | TODO | 없음 | 미지정 | 구현 및 시험 |
| P4-03 | OpenCode 어댑터 | TODO | 없음 | 미지정 | 구현 및 시험 |
| P4-04 | Antigravity 어댑터 | TODO | 없음 | 미지정 | 구현 및 시험 |
| P4-05 | Copilot VS Code Agent | TODO | 공식 문서 확인, 실행 미검증 | 미지정 | 스킬 발견/코어/인계 시험 |
| P4-06 | Copilot CLI | TODO | 공식 문서 확인, 실행 미검증 | 미지정 | gh skill 설치/명령 시험 |
| P4-07 | Copilot Cloud Agent | TODO | 공식 문서 확인, 실행 미검증 | 미지정 | 대상 저장소/환경/인계 시험 |
| P4-08 | gh skill / npx skills 배포 | TODO | 설치 구문 문서화, 실제 미실행 | 미지정 | 공개 원격 스모크 |
| P5-01 | 업스트림 변경 **감지 초안** | SCAFFOLD | `scripts/check_upstreams.py`, workflow, 단위 테스트 | 미지정 | GitHub 실제 작동 확인 |
| P5-02 | 변경 영향분석/PR 흐름 | TODO | 없음 | 미지정 | 구현 |
| P5-03 | 공개 배포 및 외부 시험 | TODO | 없음 | 미지정 | 구현 |
| P5-04 | Claude/Copilot Marketplace | TODO | 플랫폼 문서 확인, manifest 미구현 | 미지정 | 별도 플러그인 검증 |
| DOC-01 | 설치/배포/ Copilot 문서 | SCAFFOLD | INSTALLATION_AND_SHARING, COPILOT_SETUP, MARKETPLACES | 미지정 | 실제 설치 후 업데이트 |

상태: `TODO`, `IN_PROGRESS`, `NEEDS_REVIEW`, `BLOCKED`, `DONE`, `SCAFFOLD`.

## 반복 시행착오 차단 기록

| 문제 ID | 실패 접근 | 실패 근거 | 재시도 조건 | 최종 검증 |
|---|---|---|---|---|
| — | 아직 없음 | — | — | — |

## 검증 로그

| 시각(UTC) | ID | 환경 | 명령 | 결과 | 커밋/로그 |
|---|---|---|---|---|---|
| — | — | — | — | 미실행 | — |

## Copilot 및 외부 배포 필수 추가 로그

| 호스트 | Skill 발견 | Core 설치/호출 | E2E | 버전/OS/증거 |
|---|---|---|---|---|
| Copilot VS Code Agent | TODO | TODO | TODO | — |
| Copilot CLI | TODO | TODO | TODO | — |
| Copilot Cloud Agent | TODO | TODO | TODO | — |
| `gh skill` Public 원격 설치 | TODO | TODO | TODO | — |
| `npx skills` Public 원격 설치 | TODO | TODO | TODO | — |
