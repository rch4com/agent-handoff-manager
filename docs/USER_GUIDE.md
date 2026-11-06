# 사용자 사용 설명서 (설계 초안 — CLI 아직 미구현)

> **주의:** 이 문서의 `handoff` 명령은 예정된 사용자 인터페이스입니다. 현재 개발 ZIP에는 동작하는 handoff runtime이 포함되어 있지 않습니다. 설치 문서: [INSTALLATION_AND_SHARING.md](INSTALLATION_AND_SHARING.md).

## 지원 목표

Claude Code, Codex CLI, OpenCode, Antigravity, GitHub Copilot (VS Code Agent / CLI / Cloud Agent). 모든 환경에서 핵심은 공통 Python CLI이며 네이티브 slash command 지원 여부는 별도로 검증합니다.

## 권장 사용 흐름 (완성 후)

```bash
handoff init --repo . --layout multi --dry-run
handoff init --repo . --layout multi
handoff doctor
handoff write --mission "Auth API 기능 테스트"
handoff list --status open
handoff resume latest --verify-only
handoff archive SESSION_ID --dry-run
handoff archive SESSION_ID --confirm
handoff restore SESSION_ID --confirm
```

`resume`은 Git/worktree/테스트 근거 검증 후 현재 상태를 보여주며 사용자 승인 없는 checkout/reset/소스 변경을 실행하지 않습니다. `archive`는 영구 기록이 아닌 세션 단위로만 이동합니다.

## AI에게 요청하는 문장

- `agent-handoff-manager로 현재 작업을 write 해 주세요. 변경 파일, 커밋, 테스트, 실패한 접근법, 차기 작업 1개를 기록해 주세요.`
- `resume latest --verify-only로 검증한 후 실제 코드와 충돌하는 주장만 보고해 주세요.`
- `list로 open 세션을 보여주고, archive 후보를 dry-run으로 제안해 주세요.`

## GitHub Copilot 사용

- VS Code Copilot Agent: 저장소/사용자 스킬 디렉터리에 설치한 뒤 자연어 호출.
- Copilot CLI: 설치 확인은 `/skills list` 또는 `/skills info agent-handoff-manager`, 변경 반영은 `/skills reload`.
- Copilot Cloud Agent: **대상 프로젝트 저장소**에 skill을 추가하고 Python 실행 환경을 확인. 이미 설치되어 있다고 가정하지 않음.
- 자세한 내용은 [COPILOT_SETUP.md](COPILOT_SETUP.md).

## 서로 다른 CLI간 인계

1. Claude가 `write`를 수행. Git 브랜치와 실제 검증된 테스트를 기록.
2. 세션 폴더와 공식 기록을 비밀정보 검사 후 Git으로 공유.
3. Copilot/Codex가 `resume latest --verify-only` 수행.
4. 불일치를 보고한 뒤, 다른 에이전트 또는 사용자 검토 후 작업 재개.
5. 완료된 세션은 archive하되 공식 검증/결정 기록 삭제 금지.

## 안전 규칙

`AGENT_HANDOFF.md`는 검증된 프로젝트 장기 상태, `.handoffs/`는 세션 이력. 인계 문서를 신뢰할 수 있는 실행 스크립트로 취급하면 안 됩니다. 프로젝트 비밀정보·개인 경로·환경변수 원문은 인계에서 제외해야 합니다.
