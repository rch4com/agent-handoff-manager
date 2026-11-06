# Compatibility Matrix — 5 hosts / 7 surfaces (PLANNED; NOT VALIDATED)

| 호스트/표면 (버전, Win11) | 프로젝트 스킬 발견 | 코어 실행 | write/list/resume | 상태 |
|---|---|---|---|---|
| Claude Code 2.1.319 | 검증 (`.claude/skills`) | 검증 | write+list 검증, resume 미검증 | 부분 검증 |
| Codex CLI 0.165.0 | 검증 (`.agents/skills`) | 검증 (실제 python 경로 필요, R-003) | resume 검증 (Claude 작성 세션 읽기) | 부분 검증 |
| OpenCode 1.19.4 | 검증 (`opencode debug skill`) | 미실행 | 미검증 | 발견만 검증 |
| Antigravity agy 1.5.0 | 미검증 | 미검증 | 미검증 | 미검증 |
| Copilot VS Code Agent 1.145.1 | 미검증 | 미검증 | 미검증 | 미검증 |
| Copilot CLI 1.0.105 | 검증 (`copilot skill list`) | 미실행 | 미검증 | 발견만 검증 |
| Copilot Cloud Agent | 미검증 | 미검증 | 미검증 | 미검증 (push 승인 필요) |

증거: `PROJECT_TRACKER.md` 검증 로그. Linux/macOS는 전 표면 미검증. 위 표의 "검증"은 로컬 경로에서 `npx skills --copy`로 설치한 사본 기준이며 `gh skill`·공개 원격 설치는 미검증.

## 배포 도구 (2026-11-06 문서 확인; 실제 설치는 미실행)

| 배포 수단 | 역할 | 원칙 |
|---|---|---|
| `gh skill` (GitHub CLI ≥2.90.0; 이 환경 gh 2.87.3에는 `skill` 명령 없음 → 미검증) | 5개 호스트에 스킬 설치 / 업데이트 / 배포 | 원본 preview, tag pin, release smoke |
| `npx skills` (Node 22.20+) | Agent Skills 설치/갱신 | `-a` agent id 실제 도움말 확인 |
| GitHub Releases | Core binary/script, 문서, checksum | SKILL과 core가 같은 버전이어야 함 |
| Claude Code Marketplace | 선택적 플러그인 배포 | 별도 manifest / 테스트 |
| Copilot Marketplace | 선택적 플러그인 배포 | Claude와 다른 manifest / 테스트 |

## 최소 운영체제 환경

- Windows 11 / PowerShell 7 및 필요 시 Windows PowerShell 5.1
- Ubuntu 24.04/26.04 / Bash
- Python 3.10+; 실제 core 검증은 3.10, 3.12 그리고 최신 지원 버전
- 한국어·일본어 문자와 공백 포함 경로, 비영어 프로젝트
- Dirty Git, worktree, 서로 다른 clone, Cloud Agent, 권한 없는 경로

## 수용 기준

각 표면에서 Skill 발견, `handoff init`, `write`, `list`, `resume`, `archive`, `restore`, update/uninstall 시험 결과를 버전·OS·로그·커밋 SHA와 함께 기록해야 `SUPPORTED`로 변경할 수 있음.
