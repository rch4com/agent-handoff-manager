# 설치·공개 배포 매뉴얼 — agent-handoff-manager

> **상태: 개발용 배포 설계.** `write / resume / list / archive` 실행 코어는 아직 없습니다. 아래의 공개 설치 명령은 리포지토리가 Public으로 게시되고, 코어/패키징/설치 검증이 끝난 **후에만** 일반 사용자에게 안내하세요. `YOUR_GITHUB_ID`는 각자의 계정명으로 교체합니다.

## 0. 이름 및 배포 원칙

- GitHub repository: `YOUR_GITHUB_ID/agent-handoff-manager` (제안, 실제 생성되지는 않음)
- Agent Skill: `agent-handoff-manager`; canonical source path `skills/agent-handoff-manager/SKILL.md`
- User data: target application's `.agent-handoff/`, `.handoffs/`; 설치 패키지와 구분
- Distribution: GitHub Public repo + `gh skill` (우선) + `npx skills` (선택) + Marketplace (별도 플러그인 검증 후)
- Skill 파일만 설치해도 Python 런타임이 자동 설치되는 것은 아님. 다음 둘 중 한 배포 전략을 결정하고 E2E 검증해야 함: A) 동작하는 core script를 skill 폴더에 포함하고 Python 3.10+ 요구, B) version-pinned `pipx`/wheel 설치 및 SKILL.md에서 해당 CLI 실행. 자동 `pip install`/원격 스크립트 실행 금지.

## 1. 개발용 로컬 시작

```powershell
# Windows PowerShell: 압축 해제 폴더에서
python --version
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
```

```bash
# Linux/macOS: 압축 해제 폴더에서
python3 --version
python3 -m unittest discover -s tests -v
python3 scripts/validate_distribution.py
```

실제 handoff 실행 프로그램은 포함되어 있지 않습니다. 위 명령은 문서/구조/업스트림 감시 초안만 테스트합니다.

## 2. 개인 계정에서 Public 저장소 개설

사전 요구: Git과 GitHub CLI(gh) 설치, `gh auth login`으로 본인 계정 인증. 로컬 폴더를 새 빈 저장소로 시작할 때:

```bash
git init
git add .
git commit -m "docs: initialize agent handoff manager development"
git branch -M main
# 로그인/계정 확인 후 직접 실행. 실행하면 Public 리포지토리가 실제로 생성됩니다.
gh repo create agent-handoff-manager --public --source=. --remote=origin --push
```

이미 remote가 있는 저장소라면 `gh repo create`를 반복하지 말고 기존 remote를 확인하세요. **공개 전 민감정보 검사, LICENSE.template 교체, upstream 고지 작성 및 .github workflows 확인이 필요합니다.**

## 3. 권장 설치 A — GitHub CLI `gh skill` (코어 구현 및 공개 이후)

GitHub CLI **v2.90.0 이상**에서 `gh skill` 명령을 사용할 수 있습니다 (공개 프리뷰, 명령 옵션 변화 가능). 사용 전에 `gh --version`, `gh skill --help`로 확인.

```bash
# 설치 전에 원본 내용을 미리 확인
gh skill preview YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager

# 프로젝트별 설치: 기본 에이전트 Copilot
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope project

# Claude / Codex / OpenCode / Antigravity / Copilot 공통 사용자가 각 호스트에 설치할 때
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent claude-code --scope user
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent codex --scope user
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent opencode --scope user
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent antigravity --scope user
gh skill install YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope user

# 설치된 스킬 업데이트 (사용자의 설치 방식에 맞춰 실행)
gh skill update agent-handoff-manager
```

Antigravity **CLI** 제품을 사용하는 경우 `--agent antigravity-cli`도 후보입니다. 실제 제품·버전에 따라 올바른 타깃을 골라 설치 테스트해야 합니다. `gh skill install`의 `--agent` 옵션은 한 호스트씩 지정하는 방식으로 예시를 작성했습니다.

## 4. 대안 설치 B — `npx skills`

Node.js (해당 Skills CLI 문서 기준 22.20+) 필요. 설치 대상 에이전트와 스킬을 선택하는 방식이며 **실제 배포 전 선택지가 그대로 노출되는지 스모크 테스트**합니다.

```bash
# GitHub Public 저장소의 사용 가능한 스킬 목록 확인
npx skills add YOUR_GITHUB_ID/agent-handoff-manager --list

# 에이전트 선택형 설치
npx skills add YOUR_GITHUB_ID/agent-handoff-manager --skill agent-handoff-manager

# 별도 확인된 호스트만 지정해 설치하는 예시
npx skills add YOUR_GITHUB_ID/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex -a opencode

# 릴리스 태그 pin 예시
npx skills add YOUR_GITHUB_ID/agent-handoff-manager@v1.0.0 --skill agent-handoff-manager
```

Copilot 또는 Antigravity에 `-a`로 설치하려면 현재 사용자의 `npx skills` 버전과 `npx skills --help`에 표시된 정확한 agent 식별자를 먼저 확인. 또는 앞 절의 검증된 `gh skill --agent github-copilot` 방식을 우선 사용합니다.

## 5. 로컬 폴더 수동 설치 (구조 확인용, 실행 기능 미완성)

대상 프로젝트의 아래 위치에 `skills/agent-handoff-manager/` **전체 폴더**를 복사하세요. `SKILL.md` 파일만 복사하면 참조 리소스/스크립트를 누락할 수 있습니다.

| 호스트 | 프로젝트 스킬 경로(우선/대표) | 개인 범위 대표 경로 |
|---|---|---|
| GitHub Copilot | `.github/skills/agent-handoff-manager/` 또는 `.agents/skills/` | `~/.copilot/skills/` |
| Claude Code | `.claude/skills/agent-handoff-manager/` | `~/.claude/skills/` |
| Codex CLI | `.agents/skills/agent-handoff-manager/` | `~/.agents/skills/` |
| OpenCode | 설치 도구가 지정한 스킬 경로 사용 | 설치 도구/버전에서 확인 |
| Antigravity | 설치 도구가 지정한 스킬 경로 사용 | 설치 도구/버전에서 확인 |

**중복 설치 주의:** Copilot은 `.github/skills/`, `.claude/skills/`, `.agents/skills/`를 모두 읽을 수 있으므로 같은 이름의 스킬을 복수 경로에 복사하지 않도록 합니다. 공통 사용이라면 `gh skill`로 호스트별 적절한 디렉터리에 설치하는 편이 안전합니다.

## 6. 사용자 검증 절차 (배포 직전 필수)

1. `gh skill preview`로 내용 확인 후 설치. 원격 설치 전에 스크립트와 권한을 점검.
2. 각 에이전트에서 스킬 발견 여부 확인. Copilot CLI는 `/skills list` 또는 `/skills info agent-handoff-manager` 및 `/skills reload`를 활용.
3. 샘플 프로젝트에 `handoff init --dry-run`을 실행; 기존 AGENTS.md 등 설정이 보존되는지 확인.
4. 임시 저장소에서 `write -> list -> resume latest -> archive --dry-run -> archive --confirm -> restore --confirm`를 모두 실행.
5. Copilot VS Code Agent 모드, Copilot CLI, Copilot Cloud Agent는 각각 별도 스모크 테스트. Cloud에는 Python 코어가 포함되거나 사전 설치돼 있어야 함.
6. Win11/PowerShell과 Ubuntu/Bash에서 설치, 재설치, 업데이트, 제거, 롤백, 비ASCII 경로를 확인.
7. 검증 시 실제 버전, 명령, 종료 코드, 결과 파일, 테스트 증거를 `PROJECT_TRACKER.md`에 기록.

## 7. 업스트림 버전과 사용자 설치 버전 분리

- upstream ④/③: weekly watcher로 변경 감지 ⇒ Issue ⇒ PR ⇒ 테스트 ⇒ 승인 ⇒ 내부 제품 릴리스.
- 사용자용 버전: `v0.x` 테스트판, 검증 완료 시 `v1.0.0`, 업데이트 명령은 릴리스 후 안내.
- 원본의 새 commit을 사용자 디바이스에서 자동 pull하거나 실행하지 않음.

## 8. 마켓플레이스는 후속 배포 채널

- GitHub Public + `gh skill`만으로도 다른 사람이 설치 가능. 외부 시장 등록은 필수가 아님.
- Claude Code 플러그인 마켓플레이스와 GitHub Copilot 플러그인 마켓플레이스는 **각각 별도의 규격**을 가짐. Skill 호환과 플러그인 호환은 동일하지 않음.
- 코드 완성 후 `docs/MARKETPLACES.md`의 패키징/시험 계획에 따라 등록. 매니페스트만 넣고 사용 가능하다고 발표하지 않음.

## 공식 참고 문서 (2026-11-06 확인)

- GitHub Copilot skills: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- GitHub CLI skill install: https://cli.github.com/manual/gh_skill_install
- Github CLI skill publish: https://cli.github.com/manual/gh_skill_publish
- Copilot CLI commands: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- `npx skills` options: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
- VS Code Agent Skills: https://code.visualstudio.com/docs/agent-customization/agent-skills
