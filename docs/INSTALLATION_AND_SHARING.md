# 설치·공개 배포 매뉴얼 — agent-handoff-manager

> 상태: **실험적 파일럿 (0.2.0-pilot)**. 아래 명령은 2026-11-07 Windows 11에서 실제로 실행해 결과를 확인한 것입니다(근거: `PROJECT_TRACKER.md` 검증 로그). 표시가 없는 항목은 미검증입니다. 릴리스 태그는 아직 없습니다(`--pin`에는 커밋 SHA 사용).

## 0. 이름과 배포 원칙

- 저장소: `rch4com/agent-handoff-manager` (공개, MIT). 스킬 이름과 폴더명: `agent-handoff-manager` (`skills/agent-handoff-manager/SKILL.md`가 유일한 원본).
- Python 코어는 스킬 폴더 안에 포함됩니다(`scripts/handoff.py`, [ADR-0002](ADR-0002.md)). 설치 후 **Python 3.10+**만 필요하며 설치 중 코드 실행·`pip install`·네트워크 접근은 없습니다.
- 사용자 데이터(`.handoffs/`)는 설치 폴더와 분리되어 대상 프로젝트 안에 만들어집니다.
- 이 저장소의 `skills/`는 어떤 호스트의 자동 발견 경로도 아닙니다. 개발 저장소에서 스킬을 쓰려면 설치(아래)해야 합니다.

## 1. 개발용 로컬 확인

```powershell
python --version
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/check_upstreams.py      # 읽기 전용 upstream 비교
```

CI(GitHub Actions)는 ubuntu/windows × Python 3.10/3.12에서 같은 단위 테스트를 실행합니다. 이것은 단위 테스트 증거이며 Linux 호스트 E2E가 아닙니다.

## 2. 권장 설치 A — `gh skill` (GitHub CLI 2.90+, 검증: 2.103.3)

```bash
gh skill preview rch4com/agent-handoff-manager agent-handoff-manager
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope project
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent claude-code --scope project
gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent codex --scope project --pin <커밋 SHA 또는 태그>
```

`--agent` 값 `github-copilot`, `claude-code`, `codex`, `opencode`, `antigravity`를 각각 설치해 확인했습니다. 결과 위치: `claude-code` -> `.claude/skills/agent-handoff-manager/`, 나머지 -> `.agents/skills/agent-handoff-manager/`. `--pin`은 SHA로 확인했고 `SKILL.md` frontmatter에 `github-pinned`가 기록됩니다. gh가 `SKILL.md`에 `metadata`(출처, 트리 SHA)를 추가합니다.

업데이트·제거(실측): `--pin`으로 설치한 스킬은 `gh skill update agent-handoff-manager`가 `pinned to <sha> (skipped)`로 건너뜁니다. `gh skill`에는 uninstall 명령이 없어 스킬 폴더(`.agents/skills/agent-handoff-manager/`)를 직접 지우는 것이 제거입니다. 제거·재설치(이전 커밋 -> 최신 커밋) 후에도 `.handoffs/` 데이터는 그대로이며 새 버전이 이전 버전이 쓴 세션을 읽고 `doctor`가 `ok: true`였습니다. 핀 없는 설치가 새 커밋을 받는 `update` 경로는 새 릴리스가 생길 때 시험합니다. `gh skill publish --dry-run`은 통과했습니다(태그 보호 규칙 없음 경고만).

## 3. 대안 설치 B — `npx skills` (검증: node 26.13)

```bash
npx skills add rch4com/agent-handoff-manager --list
npx skills add rch4com/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex --copy -y
```

로컬 경로(`npx skills add <dir>`)와 GitHub 원격 모두 설치를 확인했고 `.agents/skills/`와 `.claude/skills/`에 동일한 사본이 만들어졌습니다. 그 결과 Copilot이 두 경로를 모두 읽을 수 있으니 **`-a claude-code`와 다른 호스트를 같이 지정하면 사본이 둘 생깁니다**. 한 경로만 쓰세요.

## 4. 선택 C — 플러그인 marketplace 경로

Claude Code와 GitHub Copilot CLI 모두 설치까지 확인했습니다(`docs/MARKETPLACES.md`, README 참조). 스킬 설치와 **동시에 쓰지 마세요**. 공식 marketplace 등록은 하지 않았습니다.

## 5. 수동 설치 (폴더 전체 복사)

`skills/agent-handoff-manager/` **폴더 전체**(`SKILL.md`와 `scripts/`)를 복사하세요. `SKILL.md`만 복사하면 코어가 없어 쓸 수 없습니다.

| 호스트 | 프로젝트 스킬 경로 | 개인 범위 |
|---|---|---|
| GitHub Copilot | `.github/skills/` 또는 `.agents/skills/` 또는 `.claude/skills/` | `~/.copilot/skills/`, `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex CLI | `.agents/skills/` | `~/.agents/skills/` |
| OpenCode | `.agents/skills/`, `.claude/skills/` (실측: `.claude/skills`에서 발견) | — |
| Antigravity | `.agents/skills/` (실측) | — |

여러 경로에 같은 스킬을 복사하지 않습니다.

## 6. 설치 후 확인 절차

1. 발견: Copilot CLI `copilot skill list`, OpenCode `opencode debug skill`, 나머지는 각 호스트에서 스킬 호출.
2. 코어: `python <skill-dir>/scripts/handoff.py --version` -> `agent-handoff-manager core 0.2.0-pilot`.
3. 임시 저장소에서 `write -> list -> resume latest -> archive --dry-run -> archive --confirm -> restore --confirm`(`docs/USER_GUIDE.md`).
4. Windows 샌드박스 에이전트(Codex)는 Microsoft Store용 `python` alias를 실행하지 못할 수 있으니 실제 인터프리터 경로를 지정하세요.
5. 호스트별 실제 결과는 `docs/COMPATIBILITY.md`에서만 확인하세요. 거기 "검증"으로 표시되지 않은 호스트·OS는 지원을 주장하지 않습니다.

## 7. 새 사용자 온보딩 시험 상태

- 검증됨: 원격 preview -> install -> core 실행 -> (호스트에서) write/resume.
- 검증됨: pin 건너뜀, 제거(폴더 삭제) 후 재설치에서 데이터 보존. 미검증: 핀 없는 update로 새 버전 수신, Linux·macOS, Copilot VS Code Agent, Copilot Cloud Agent(대상 저장소에 스킬을 커밋해야 함).

## 8. 업스트림과 사용자 설치본 분리

업스트림 HEAD 변화는 주간 워크플로가 감지해 영향분석 보고서를 이슈로 올릴 뿐이며, 설치본에는 반영되지 않습니다. 반영은 검토된 PR(`.github/pull_request_template.md`)과 승인된 릴리스로만 합니다.

## 9. 공개 저장소 관리

저장소는 이미 공개되어 있습니다(`gh repo create`를 다시 실행하지 마세요). 푸시·태그·Release·marketplace 등록은 소유자가 승인한 뒤에만 합니다. 릴리스 체크섬/서명 정책은 아직 없습니다.

## 참고 문서 (2026-11-06 확인)

- GitHub Copilot skills: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- GitHub CLI skill: https://cli.github.com/manual/gh_skill_install , https://cli.github.com/manual/gh_skill_publish
- Copilot CLI: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- `npx skills`: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
- VS Code Agent Skills: https://code.visualstudio.com/docs/agent-customization/agent-skills
