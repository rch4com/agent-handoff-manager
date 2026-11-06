# Compatibility Matrix — 5 hosts / 7 surfaces (PLANNED; NOT VALIDATED)

| 호스트/표면 (버전, Win11) | 프로젝트 스킬 발견 | 코어 실행 | write/list/resume | 상태 |
|---|---|---|---|---|
| Claude Code 2.1.319 | 검증 (`.claude/skills`) | 검증 | write, list, resume 검증 (Codex 작성 세션 resume 포함) | 부분 검증 |
| Codex CLI 0.165.0 | 검증 (`.agents/skills`) | 검증 (실제 python 경로 필요, R-003) | write(`--depth rich`, failure_records), resume 검증 | 부분 검증 |
| OpenCode 1.19.4 | 검증 (`opencode debug skill`) | 검증 (`-m opencode/big-pickle` 지정 시) | resume 검증, write는 core 호출만 검증(payload 외부 준비) | 부분 검증 |
| Antigravity agy 1.5.0 | 검증 (`.agents/skills`) | 검증 | resume 검증(미존재 주장 파일 지적), write는 core 호출만 검증(payload 외부 준비) | 부분 검증 |
| Copilot VS Code Agent 1.145.1 | 미검증 | 미검증 | 미검증 | 미검증 |
| Copilot CLI 1.0.105 | 검증 | 검증 | resume 검증, write는 core 호출만 검증(payload는 외부 준비, 에이전트가 직접 작성한 것은 아님) | 부분 검증 |
| Copilot Cloud Agent | 미검증 | 미검증 | 미검증 | 미검증 (push 승인 필요) |

증거: `PROJECT_TRACKER.md` 검증 로그. **Linux**: 코어 단위 테스트 83개를 Ubuntu 24.04(WSL2, Python 3.12.3)와 GitHub Actions ubuntu-latest(3.10/3.12)에서 통과(symlink 포함). **Linux에서 호스트 에이전트(Claude/Codex/OpenCode/Antigravity/Copilot) 실행은 전부 미검증**, macOS는 전 항목 미검증. 위 표의 "검증"은 로컬 경로에서 `npx skills --copy`로 설치한 사본 기준이며 `gh skill`·공개 원격 설치는 미검증.

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

## 재현 스크립트

`scripts/host_smoke.ps1`는 공개 저장소의 스킬을 고정 SHA로 임시 저장소에 설치하고, 호스트 에이전트에게 `write`를 시킨 뒤 **코어(`list`, `doctor`)와 git으로 결과를 직접 판정**합니다(에이전트의 자기 보고는 증거로 쓰지 않음). 실제 호스트 CLI를 실행하므로 모델 크레딧이 소모되며 직접 실행해야 합니다.

```powershell
pwsh -File scripts/host_smoke.ps1 -Target copilot,opencode,agy -Python C:/Users/me/AppData/Local/Python/pythoncore-3.14-64/python.exe
pwsh -File scripts/host_smoke.ps1 -Target copilot -ComposePayload   # agent writes the payload itself (broader permission)
pwsh -File scripts/host_smoke.ps1 -DryRun    # 설치 + 코어 확인만 (에이전트 미실행)
```

`-DryRun`은 2026-11-07 Windows 11에서 실행해 설치와 코어 실행을 확인했습니다. 에이전트를 실제로 띄우는 부분은 이 문서의 "검증" 표에 반영된 결과만 사실로 취급하세요.

Copilot CLI 헤드리스 팁: `--allow-tool='shell(python)'`처럼 **실행 파일 이름만** 지정하고 프롬프트에서 `python ...`을 쓰도록 하세요. 전체 경로 패턴(`shell(C:\...\python.exe)`)은 Windows에서 `& 'C:\...'` 형태로 실행되어 매칭되지 않았습니다.
OpenCode 헤드리스 팁: 환경변수 `OPENCODE_PERMISSION='{"bash":{"python *":"allow","*":"deny"},"edit":"deny"}'`로 python 실행만 허용하고 `opencode run -m <모델> ...`을 실행하세요. Antigravity(agy 1.5.0)는 `--settings '<JSON>'`(세션 전용, 사용자 전역 allow 목록을 **대체**)로 `permissions.allow`/`deny`를 지정할 수 있고, `command(regex:^python(?:\s.*)?$)`와 읽기 전용 명령만 허용하는 설정으로 write 호출이 통과했습니다(`command(python*)`만 주면 agy가 자체적으로 자동 거부).

`host_smoke.ps1` 기본 동작: copilot/opencode는 **좁은 권한 모드**(에이전트는 `python ...`만 실행 가능, payload는 스크립트가 준비), claude/codex/agy는 에이전트가 payload를 직접 작성. `-ComposePayload`를 주면 copilot/opencode도 직접 작성(넓은 권한 필요). 2026-11-07 Windows 11에서 `-Target claude,codex`와 `-Target opencode,copilot` 모두 `PASS`(코어 판정)였습니다.
