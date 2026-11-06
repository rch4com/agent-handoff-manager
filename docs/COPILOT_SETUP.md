# GitHub Copilot 지원 계획 및 테스트 매뉴얼

> 상태(2026-11-07): Copilot CLI는 설치·발견·resume을 실제로 확인했고, VS Code Agent와 Cloud Agent는 미검증입니다. 코어는 스킬 폴더에 포함되어 있어 스킬 폴더 전체가 설치되면 실행됩니다 (ADR-0002).

## A. Copilot for VS Code — Agent Mode

- 사용자가 VS Code와 GitHub Copilot에 로그인하고 Agent 모드를 실행할 수 있는지 확인.
- 대상 프로젝트에 `.github/skills/agent-handoff-manager/SKILL.md`를 설치하거나, 공통 `.agents/skills/`에 설치.
- `name`은 부모 폴더와 일치하는 `agent-handoff-manager`여야 함. YAML frontmatter의 `description`은 언제 사용할지 명확히 서술.
- 자연어 예시: `agent-handoff-manager 스킬로 프로젝트 상태를 읽고 최신 세션을 resume --verify-only로 점검해 주세요.`
- 최종판에서는 에이전트가 실제 Python 코어를 호출했는지, 어떤 파일을 읽고 수정했는지 검증.
- VS Code Agent Skills: https://code.visualstudio.com/docs/agent-customization/agent-skills

## B. GitHub Copilot CLI

- 설치: `gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent github-copilot --scope user` (project scope 검증됨)
- Copilot CLI에서 `/skills list`, `/skills info agent-handoff-manager`, `/skills reload`를 사용해 발견 여부 확인.
- `copilot` 명령 자체의 설치/권한은 각 사용자의 GitHub Copilot 요금제와 조직 정책을 따름.
- CLI 명령 참고: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference

## C. Copilot Cloud Agent (GitHub)

- Cloud Agent가 다룰 **대상 Git 저장소 안에** 스킬을 프로젝트 스킬로 포함해야 발견 가능; 다른 저장소에 공개한 것만으로 대상 프로젝트에서 자동 활성화되지 않음.
- `.github/skills/agent-handoff-manager/` 또는 GitHub Docs가 인정한 `.agents/skills/` 경로 사용.
- 별도 커맨드 또는 런타임 필요시 Cloud Agent 실행 환경의 설치 및 파일 접근을 확인. 스킬이 로컬 `$HOME`에 설치돼 있다는 가정 금지.
- Cloud Agent가 생성한 리포트/PR을 `검증된 완료`로 자동 승격하지 말고 CI·리뷰 증거 확인.
- 공식: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills

## D. Copilot Code Review

- GitHub는 Code Review에도 `SKILL.md`를 지원. 다만 본 스킬은 **handoff 관리용**이며 code-review 전문 스킬과 다름.
- 읽기 가능한 리뷰 내용(리스크/검증 기준)은 참고할 수 있어도, PR 리뷰 수행 자체가 `handoff write`를 실행한다고 주장하면 안 됨.

## E. 프로젝트 지침 연계

- 이 개발 저장소에 `.github/copilot-instructions.md` 추가 (root AGENTS.md 참조, 중복된 정책 복제 최소화).
- 설치 대상 저장소의 `AGENTS.md`를 임의로 덮어쓰지 말 것. 기존 `copilot-instructions.md`도 자동 덮어쓰기 금지.
- Copilot instruction 참고: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions

## E2E 필수 3개 표면 (2026-11-07 상태)

| 표면 | Skill 발견 | Core 실행 | 세션 왕복 | 환경 차이 경고 | 결과 |
|---|---|---|---|---|---|
| VS Code Agent Mode (1.145.1 설치됨) | 미검증 | 미검증 | 미검증 | 미검증 | TODO (대화형 조작 필요) |
| Copilot CLI 1.0.105 (Windows 11) | `copilot skill list`로 확인 (gh skill/npx 설치본, 플러그인 설치본) | `copilot -p` 실행으로 확인 (resume) | Codex가 쓴 세션을 resume으로 읽음 / write는 미검증 | `differences`와 경고 보고 확인 | 부분 검증 |
| Copilot Cloud Agent | 미검증 | 미검증 | 미검증 | 미검증 | TODO (대상 저장소에 스킬 커밋 + 이슈 할당 필요) |

Copilot CLI 헤드리스 실행은 `--allow-tool='shell'`이 필요했고(파이썬 경로 패턴 매칭 실패), 중첩 에이전트 권한 정책상 사용자가 직접 실행한 결과입니다. 상세 로그: `PROJECT_TRACKER.md`.
