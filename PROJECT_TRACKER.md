# PROJECT_TRACKER.md — 개발 진척 및 증거

> 완료 기준: 코드 존재가 아닌 **실행 테스트 통과 + 근거 기록**. 최초 상태를 완료라고 과장하지 마세요.

| ID | 항목 | 상태 | 증거 (커밋/PR/테스트) | 소유자 | 다음 행동 |
|---|---|---|---|---|---|
| P0-01 | ④ 원본 구조 조사 | DONE | `gh api` 2026-11-06: ④ @ef01fa9d… (MIT, 19 files, tree reviewed); ADR-0003 | 미지정 | — |
| P0-02 | ③ 원본 구조 조사 | DONE | `gh api`: ③ @b6ad33e5… (MIT, prompt-only plugin, no scripts); ADR-0003 | 미지정 | — |
| P0-03 | 두 MIT 원본 고지 | DONE | LICENSE blobs bbf0adc0…/a0a2e818… fetched verbatim -> `THIRD_PARTY_NOTICES.md`; nothing vendored; `check_upstreams.py` live: both up_to_date | 미지정 | Re-run notices review if code is ever vendored |
| P1-01 | 세션 스키마/스토리지 | NEEDS_REVIEW | pilot core `skills/agent-handoff-manager/scripts/handoff.py`; 19 tests OK (1 skipped: symlink needs privilege) | 미지정 | Crash-injection + multi-process tests; real `project_id` |
| P1-02 | 레거시 이관 | TODO | 없음 | 미지정 | 구현 |
| P2-01 | write | NEEDS_REVIEW | write verified via Claude Code 2.1.319 (haiku) on installed copy; unit tests | 미지정 | `--depth`, ④ change candidates (P3) |
| P2-02 | resume | NEEDS_REVIEW | resume verified by Codex 0.165.0 reading a Claude-written session (read-only, git diff reported) | 미지정 | Add checks: expected files / tests |
| P2-03 | list | NEEDS_REVIEW | list verified via Claude Code + unit tests | 미지정 | Filters (project/status/agent/date), worktree test |
| P2-04 | archive/restore | NEEDS_REVIEW | archive/restore: unit + clean-copy lifecycle test (non-ASCII path) | 미지정 | `--dry-run` |
| P2-05 | doctor | NEEDS_REVIEW | doctor: unit + clean-copy test | 미지정 | CLI/path compat checks |
| P3-01 | 공식 상태와 세션 통합 | TODO | 없음 | 미지정 | 구현 |
| P4-01 | Claude 어댑터 | IN_PROGRESS | Claude Code 2.1.319 / Win11: skill discovered in `.claude/skills` (npx skills --copy), write+list E2E pass | 미지정 | resume on Claude; macOS/Linux |
| P4-02 | Codex 어댑터 | IN_PROGRESS | Codex 0.165.0 / Win11: discovery in `.agents/skills`, cross-agent resume pass (needs real python path; R-003) | 미지정 | write via Codex; Linux |
| P4-03 | OpenCode 어댑터 | IN_PROGRESS | OpenCode 1.19.4: `opencode debug skill` lists skill (read from `.claude/skills`); not executed | 미지정 | Headless write/resume run |
| P4-04 | Antigravity 어댑터 | TODO | Antigravity `agy` 1.5.0 installed; not probed | 미지정 | Find skill path; discovery + run |
| P4-05 | Copilot VS Code Agent | TODO | VS Code 1.145.1 present; not run | 미지정 | Needs interactive Agent Mode; manual by owner |
| P4-06 | Copilot CLI | BLOCKED | Copilot CLI 1.0.105: `copilot skill list` discovers project skill (verified). Headless E2E denied by permission classifier (broad shell for nested agent) | 미지정 | Owner decides: allow narrowly-scoped run or run manually |
| P4-07 | Copilot Cloud Agent | TODO | Needs pushed repo + Cloud Agent task; owner approval | 미지정 | After push approval |
| P4-08 | gh skill / npx skills 배포 | BLOCKED | `npx skills add <local>` list+install --copy verified (-a claude-code codex opencode antigravity github-copilot -> `.agents/skills` + `.claude/skills`). `gh skill`: installed gh 2.87.3 has no `skill` cmd (needs >=2.90). Remote install untested (repo not updated) | 미지정 | Owner: upgrade gh + approve push |
| P5-01 | 업스트림 변경 **감지 초안** | NEEDS_REVIEW | `check_upstreams.py` live run 2026-11-06 both up_to_date; unit tests | 미지정 | Verify workflow on GitHub after push |
| P5-02 | 변경 영향분석/PR 흐름 | TODO | 없음 | 미지정 | 구현 |
| P5-03 | 공개 배포 및 외부 시험 | TODO | 없음 | 미지정 | 구현 |
| P5-04 | Claude/Copilot Marketplace | TODO | 플랫폼 문서 확인, manifest 미구현 | 미지정 | 별도 플러그인 검증 |
| DOC-01 | 설치/배포/ Copilot 문서 | SCAFFOLD | INSTALLATION_AND_SHARING, COPILOT_SETUP, MARKETPLACES | 미지정 | 실제 설치 후 업데이트 |

상태: `TODO`, `IN_PROGRESS`, `NEEDS_REVIEW`, `BLOCKED`, `DONE`, `SCAFFOLD`.

## 반복 시행착오 차단 기록

| 문제 ID | 실패 접근 | 실패 근거 | 재시도 조건 | 최종 검증 |
|---|---|---|---|---|
| R-001 | `ensure_ascii=False` JSON를 cp949 콘솔로 출력 | write 성공 후 `HANDOFF_ERROR: 'cp949' codec…`, 저장은 됐는데 실패 보고 | stdout/stderr UTF-8 재설정 유지 | `test_skill_package` clean-copy (non-ASCII mission) |
| R-002 | `mkdir(mode=0o700)` | Win + Python>=3.13: 소유자 전용 ACL → 샌드박스 호스트/git이 세션 디렉터리 접근 불가 (icacls로 확인) | mode 인자 없이 생성 | `test_session_dir_created_without_restrictive_mode` (fix 제거 시 FAIL 확인) |
| R-003 | SKILL.md가 `python`/`py -3`/`python3` 가정 | Codex 샌드박스에서 WindowsApps alias 실행 불가 -> resume 중단 | 실제 인터프리터 경로 지정 안내 (SKILL.md) | Codex 재실행 resume 성공 (수동 증거; 자동 테스트 불가) |

## 검증 로그

| 시각(UTC) | ID | 환경 | 명령 | 결과 | 커밋/로그 |
|---|---|---|---|---|---|
| 2026-11-06 | P0-03 | Win11, py3.14.6 | `python scripts/check_upstreams.py` | both up_to_date | — |
| 2026-11-06 | P1/P2 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 19 tests OK, 1 skipped | working tree (uncommitted at log time) |
| 2026-11-06 | P4-08 | Win11, node 26.13, npx skills | `npx skills add D:/…/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex -a opencode -a antigravity -a github-copilot --copy -y` | installed `.agents/skills`+`.claude/skills`, identical copies, script runs | scratchpad proj1 |
| 2026-11-06 | P4-01 | Claude Code 2.1.319 | `claude -p … --model haiku --allowedTools Bash(python:*)…` write+list | session created, id reported | `.handoffs/sessions/20261106T045455Z-61fc48eb5653` |
| 2026-11-06 | P4-02 | codex-cli 0.165.0 | `codex exec -s workspace-write` resume latest | 1st run blocked (R-003), 2nd run OK, no diffs vs saved | — |
| 2026-11-06 | P4-06 | Copilot CLI 1.0.105 | `copilot skill list` | project skill listed | headless run NOT executed (denied) |

## Copilot 및 외부 배포 필수 추가 로그

| 호스트 | Skill 발견 | Core 설치/호출 | E2E | 버전/OS/증거 |
|---|---|---|---|---|
| Copilot VS Code Agent | TODO | TODO | TODO | — |
| Copilot CLI | PASS (`copilot skill list`, v1.0.105) | TODO | TODO | 헤드리스 실행 미허용 |
| Copilot Cloud Agent | TODO | TODO | TODO | — |
| `gh skill` Public 원격 설치 | TODO | TODO | TODO | — |
| `npx skills` Public 원격 설치 | TODO (local path OK) | TODO | TODO | 로컬 경로 설치만 검증 |
