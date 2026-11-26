# agent-handoff-manager

> 상태: **실험적 소스 버전 (0.3.0-pilot)**. 공통 Python 코어는 Windows/Linux에서 테스트됐고 Windows 11에서 일부 호스트로 검증했습니다. Linux/macOS 호스트 E2E와 Copilot VS Code Agent는 미검증이며, Cloud Agent는 소유자 결정으로 시험을 건너뛰었습니다. 문서 정리 기준일 2026-11-13; 기존 실행 증거는 `PROJECT_TRACKER.md` 참조.

서로 다른 AI 코딩 에이전트(Claude Code, Codex CLI, OpenCode, Antigravity, GitHub Copilot) 사이에서 작업을 이어받기 위한 Agent Skill 입니다. 프로젝트의 **검증된 장기 상태**와 **세션별 인계 기록(주장)** 을 분리하고, `resume`은 읽기 전용으로 실제 git 상태와 비교만 합니다.

설계 근거: ④ [WeirdSky924/agent-handoff-skill](https://github.com/WeirdSky924/agent-handoff-skill), ③ [aploe/claude-handoff-skill](https://github.com/aploe/claude-handoff-skill) (둘 다 MIT, 검토한 SHA는 `upstreams.lock.json`). 두 원본의 **코드는 가져오지 않았습니다** ([ADR-0003](docs/ADR-0003.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)). 원본 변경은 자동 감지만 하고 검토 PR 없이는 채택하지 않습니다.

## 설치 (실제 검증된 경로, Windows 11)

```bash
gh skill preview rch4com/agent-handoff-manager agent-handoff-manager
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope project   # gh 2.90+ 필요 (검증: 2.103.3)
npx skills add rch4com/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex --copy
```

현재 소스 태그로 고정하려면 `--pin v0.3.0-pilot`을 사용하세요. [v0.3.0-pilot 소스](https://github.com/rch4com/agent-handoff-manager/tree/v0.3.0-pilot)

`--agent`는 `claude-code`, `codex`, `opencode`, `antigravity`, `github-copilot`로 설치를 확인했습니다. 설치 결과는 `.agents/skills/` 또는 `.claude/skills/`이며 코어(`scripts/handoff.py`)가 스킬 폴더 안에 함께 복사됩니다 ([ADR-0002](docs/ADR-0002.md)). 설치 후 Python 3.10+만 있으면 됩니다. 설치 중 코드는 실행되지 않습니다.

> 같은 스킬을 `.agents/skills`와 `.claude/skills`에 모두 설치하면 Copilot이 둘 다 읽을 수 있으니 한 곳만 쓰세요.

### 선택: 플러그인 경로 (스킬 설치와 동시에 쓰지 마세요)

```bash
# Claude Code (검증: 2.1.319)
claude plugin marketplace add rch4com/agent-handoff-manager
claude plugin install agent-handoff-manager@agent-handoff-manager-marketplace
# GitHub Copilot CLI (검증: 1.0.105, 설치까지)
copilot plugin marketplace add rch4com/agent-handoff-manager
copilot plugin install agent-handoff-manager@agent-handoff-manager-copilot
```

두 marketplace 매니페스트는 형식이 다르며(`.claude-plugin/` vs `plugin.json` + `.github/plugin/`) 같은 스킬 폴더를 가리킵니다. 공식 marketplace에는 등록하지 않았습니다. 자세한 내용은 [docs/MARKETPLACES.md](docs/MARKETPLACES.md).

## 사용

[docs/USER_GUIDE.md](docs/USER_GUIDE.md)의 명령은 실제 CLI와 일치합니다. 요약:

```bash
python <skill-dir>/scripts/handoff.py --repo . write --payload payload.json
python <skill-dir>/scripts/handoff.py --repo . list [--status all] [--agent codex] [--since D] [--until D] [--all-worktrees]
python <skill-dir>/scripts/handoff.py --repo . resume latest
python <skill-dir>/scripts/handoff.py --repo . archive ID --confirm   # restore ID --confirm
python <skill-dir>/scripts/handoff.py --repo . doctor
python <skill-dir>/scripts/handoff.py --repo . import-legacy --dry-run
```

## 호스트별 검증 현황 (Windows 11)

| 호스트 | 발견 | 실행 | 검증된 동작 |
|---|---|---|---|
| Claude Code 2.1.319 | O | O | write, list, resume |
| Codex CLI 0.165.0 | O | O | write, resume (실제 python 경로 필요) |
| OpenCode 1.19.4 | O | O | resume, write(core 호출만; payload는 외부 준비) (`-m` 모델 지정 시) |
| Antigravity agy 1.5.0 / 1.5.6 | O | O | resume, write(core 호출만; payload는 외부 준비) |
| Copilot CLI 1.0.105 | O | O | resume, write(core 호출만; payload는 외부 준비) |
| Copilot VS Code Agent / Cloud Agent | 미검증 | 미검증 | — |

증거: [PROJECT_TRACKER.md](PROJECT_TRACKER.md) 검증 로그, [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md). 지원 선언(v1.0)은 5개 호스트 + Copilot 3개 표면 E2E 이후입니다.

## 남은 검증과 구현

### 로컬 소스의 실행·결과 기록 확장 (미릴리스)

`run-start`로 인계받은 입력을 고정하고, 각 에이전트가 별도 실행 ID로 작업한 뒤 `run-finish`로 결과를 남길 수 있습니다. 결과는 변경 불가이며 같은 request ID의 동일 재시도는 중복 저장하지 않습니다. `list-runs`와 `resume`에서 결과·재시도·통합 담당자의 선택을 확인합니다. 자동 작업 배정이나 공식 완료 승격은 하지 않습니다. 기존 `v0.2.0-pilot` 태그에는 없으며 [사용 설명서](docs/USER_GUIDE.md)와 [ADR-0006](docs/ADR-0006.md)을 참조하세요.

변경 후보 제안, upstream 영향분석 보고서, Claude/Copilot marketplace manifest, 파일럿 릴리스 태그·체크섬은 있습니다. 남은 항목은 장기 상태 파싱·승인 흐름, 실제 upstream 변경 시 이슈 갱신, Linux/macOS 호스트 E2E, Copilot VS Code Agent, 외부 사용자의 새 환경 온보딩·새 버전 업데이트, 서명·태그 보호입니다. Cloud Agent 시험은 소유자 결정으로 건너뛰었으며 검증된 지원이 아닙니다. 상세: [docs/RELEASE_GATES.md](docs/RELEASE_GATES.md).

## 개발

```bash
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/check_upstreams.py          # 읽기 전용 upstream HEAD 비교
```

먼저 읽을 파일: [AGENTS.md](AGENTS.md), [INTENTS.md](INTENTS.md), [WORK_ORDER.md](WORK_ORDER.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PROJECT_TRACKER.md](PROJECT_TRACKER.md), [docs/UPSTREAM_POLICY.md](docs/UPSTREAM_POLICY.md).

## 문서 지도

[설치·공유](docs/INSTALLATION_AND_SHARING.md) · [Copilot](docs/COPILOT_SETUP.md) · [마켓플레이스](docs/MARKETPLACES.md) · [스키마](docs/SCHEMA_SPEC.md) · [어댑터 계약](docs/ADAPTER_CONTRACT.md) · [복구](docs/RECOVERY_PROTOCOL.md) · [마이그레이션](docs/MIGRATION.md) · [보안](docs/SECURITY.md) · [English](README.en.md)

라이선스: MIT ([LICENSE](LICENSE)).
