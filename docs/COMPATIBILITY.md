# Compatibility Matrix — 5 hosts / 7 surfaces (PLANNED; NOT VALIDATED)

| 호스트/표면 | 프로젝트 스킬 발견 | 공통 Python CLI | 실제 4개 명령 | 현재 상태 |
|---|---|---|---|---|
| Claude Code CLI | `.claude/skills` 등 | 계획 | 미구현 | 미검증 |
| Codex CLI | `.agents/skills` | 계획 | 미구현 | 미검증 |
| OpenCode | 설치도구 경로에 따름 | 계획 | 미구현 | 미검증 |
| Antigravity IDE/CLI | 각 제품·버전 검증 | 계획 | 미구현 | 미검증 |
| GitHub Copilot VS Code Agent | `.github/skills`, `.agents/skills` | 계획 | 미구현 | 미검증 |
| GitHub Copilot CLI | `.github/skills`, `.agents/skills` 등 | 계획 | 미구현 | 미검증 |
| GitHub Copilot Cloud Agent | 대상 저장소 프로젝트 skill | 환경 별도 준비 필요 | 미구현 | 미검증 |

## 배포 도구 (2026-11-06 문서 확인; 실제 설치는 미실행)

| 배포 수단 | 역할 | 원칙 |
|---|---|---|
| `gh skill` (GitHub CLI ≥2.90.0) | 5개 호스트에 스킬 설치 / 업데이트 / 배포 | 원본 preview, tag pin, release smoke |
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
