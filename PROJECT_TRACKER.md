# PROJECT_TRACKER.md — 개발 진척 및 증거

> 완료 기준: 코드 존재가 아닌 **실행 테스트 통과 + 근거 기록**. 최초 상태를 완료라고 과장하지 마세요.

| ID | 항목 | 상태 | 증거 (커밋/PR/테스트) | 소유자 | 다음 행동 |
|---|---|---|---|---|---|
| P0-01 | ④ 원본 구조 조사 | DONE | `gh api` 2026-11-06: ④ @ef01fa9d… (MIT, 19 files, tree reviewed); ADR-0003 | 미지정 | — |
| P0-02 | ③ 원본 구조 조사 | DONE | `gh api`: ③ @b6ad33e5… (MIT, prompt-only plugin, no scripts); ADR-0003 | 미지정 | — |
| P0-03 | 두 MIT 원본 고지 | DONE | LICENSE blobs bbf0adc0…/a0a2e818… fetched verbatim -> `THIRD_PARTY_NOTICES.md`; nothing vendored; `check_upstreams.py` live: both up_to_date | 미지정 | Re-run notices review if code is ever vendored |
| P1-01 | 세션 스키마/스토리지 | NEEDS_REVIEW | pilot core `skills/agent-handoff-manager/scripts/handoff.py`; 19 tests OK (1 skipped: symlink needs privilege) | 미지정 | Crash-injection + multi-process tests; real `project_id` |
| P1-02 | 레거시 이관 | NEEDS_REVIEW | `import-legacy [--dry-run]`: 7 tests in tests/test_legacy_import.py (lossless + originals byte-identical, idempotent, dry-run, secret skip, symlink/non-handoff skip, ④/AGENTS/CLAUDE/copilot files untouched over 3x init+import, CLI); red-before-green; manual run in non-ASCII path. Fixture is hand-written from upstream template, NOT output of the real ③ plugin | 미지정 | Run against real ③-generated docs; legacy status/INDEX not imported (by design) |
| P2-01 | write | NEEDS_REVIEW | write: payload facts/claims split (`claims_are_unverified`), secret rejection, explicit next_action, `--depth auto/minimal/rich/exhaustive` (7 tests, red-before-green), session meta + git observation; Claude Code E2E write | 미지정 | ④ change candidates (P3); stronger secret scanning; non-Claude host write E2E |
| P2-02 | resume | NEEDS_REVIEW | resume: read-only; branch/HEAD/dirty + HEAD ancestry (ahead N / diverged), expected-file existence (symlink/outside_root not followed), validation claims never executed, warnings (7 tests, red-before-green); cross-agent resume verified on Codex/Copilot CLI/Antigravity/OpenCode | 미지정 | Tests are listed not run (by rule); AGENT_HANDOFF.md/.agent-handoff read order is P3 |
| P2-03 | list | NEEDS_REVIEW | tests/test_list_filters.py: status/agent/date filters (+invalid input rejected, CLI), `--all-worktrees` over a real `git worktree add` with non-ASCII path (read-only, `worktree_root` tagged); Claude Code list E2E earlier | 미지정 | Project filter n/a (project_id is a path hash); Linux run; crash/perf on many sessions |
| P2-04 | archive/restore | NEEDS_REVIEW | archive/restore `--confirm` + `--dry-run` (mutually exclusive, one required): DryRunTests x3 (plan printed, byte-identical tree, invalid cases fail like real run) + clean-copy lifecycle test | 미지정 | Crash-injection between metadata rewrite and rename; Linux |
| P2-05 | doctor | NEEDS_REVIEW | doctor: runtime info (python>=3.10, git), uninitialized + legacy hint, leftover pending files, crash-emptied session dir, newer schema, stray files, symlinked store (7 tests, red-before-green) | 미지정 | Host-CLI compat probes; Windows/Linux CI run |
| P3-01 | 공식 상태와 세션 통합 | NEEDS_REVIEW | tests/test_p3_durable_state.py (6): write/resume/archive/restore/list/doctor leave AGENT_HANDOFF.md + .agent-handoff/* (incl. ④ archive/) byte-identical; resume reads durable state first (declared order, symlink not followed), `session_claims_are_official=false`, completed-claim warning; write proposes `state_change_candidates` (not persisted); `failure_records` + `do_not_repeat`; red-before-green | 미지정 | Not done: snapshot/risks/validation *parsing* (only excerpt+hash), ④ compaction vs ③ archive interplay on a real ④ project, approval workflow for promoting candidates |
| P4-01 | Claude 어댑터 | IN_PROGRESS | Claude Code 2.1.319 / Win11 (haiku): discovery, write+list (gh/npx copy), and resume of a Codex-written session from a `gh skill install --pin <sha>` copy: reported do_not_repeat, refused to retry the failed approach, flagged missing AGENT_HANDOFF.md | 미지정 | Linux/macOS; real long session |
| P4-02 | Codex 어댑터 | IN_PROGRESS | codex-cli 0.165.0 / Win11: discovery, cross-agent resume, and WRITE (`--depth rich`, failure_records) from a `gh skill install --agent codex --pin 74b9026` copy (needs real python path; R-003) | 미지정 | Linux; Codex Cloud n/a |
| P4-03 | OpenCode 어댑터 | IN_PROGRESS | OpenCode 1.19.4 / Win11: with explicit `-m opencode/big-pickle`, skill loaded via Skill tool, `resume latest` ran on gh-installed copy; independently checked git + missing `src/example.py`, flagged empty failed_attempts, ran nothing from payload. Default-model run failed (err_d7bb4327/err_48fd9bc1) = provider config, not skill | 미지정 | write via OpenCode; Linux |
| P4-04 | Antigravity 어댑터 | IN_PROGRESS | Antigravity agy 1.5.0 / Win11: discovered skill in `.agents/skills` (gh skill --agent antigravity install), ran `resume latest`, reported mission/writer/git diff and flagged claimed `src/example.py` as absent | 미지정 | write via agy; Linux |
| P4-05 | Copilot VS Code Agent | TODO | VS Code 1.145.1 present; not run | 미지정 | Needs interactive Agent Mode; manual by owner |
| P4-06 | Copilot CLI | IN_PROGRESS | Copilot CLI 1.0.105 / Win11: skill loaded, `resume latest` on gh-installed copy ran (--allow-tool=shell), mission+writer+git diff correct, validation reported unverified | 미지정 | write via Copilot; Linux |
| P4-07 | Copilot Cloud Agent | TODO | Needs pushed repo + Cloud Agent task; owner approval | 미지정 | After push approval |
| P4-08 | gh skill / npx skills 배포 | NEEDS_REVIEW | gh 2.103.3 (upgraded via winget): `gh skill publish --dry-run` OK; `gh skill preview` + `install --agent github-copilot|claude-code|codex|opencode|antigravity --scope project` from public rch4com/agent-handoff-manager@137799a OK (.agents/skills, .claude/skills); installed copy ran init/write/list/doctor; `npx skills add rch4com/agent-handoff-manager` OK. Not yet: `--pin` tag, update, uninstall, Linux | 미지정 | Tag release + pin/update/uninstall test; Linux run |
| P5-01 | 업스트림 변경 **감지 초안** | NEEDS_REVIEW | `check_upstreams.py` live run both up_to_date; GitHub workflow_dispatch run 42254700976 success; unit tests | 미지정 | Scheduled (cron) run observation; issue creation path only exercised by unit logic |
| P5-02 | 변경 영향분석/PR 흐름 | NEEDS_REVIEW | impact analysis in monitor report (compare metadata only; license/executable/skill-contract/template/docs risk; truncation + API error = high), 4 tests, verified on real aploe range 44f9b29..b6ad33e without touching the lock; `.github/pull_request_template.md` adoption checklist | 미지정 | Issue-creation path on a real change; automatic draft PR is intentionally not implemented (human opens it) |
| P5-03 | 공개 배포 및 외부 시험 | TODO | 없음 | 미지정 | 구현 |
| P5-04 | Claude/Copilot Marketplace | IN_PROGRESS | Claude: manifests validated (`claude plugin validate .`), remote add/install/core run/uninstall/remove PASS. Copilot: separate format (`plugin.json` + `.github/plugin/marketplace.json`), remote `marketplace add`/`browse`/`install` PASS, installed core runs; agent headless run pending user. Not submitted to any official marketplace | 미지정 | Copilot plugin headless write/resume (user-run); VS Code plugin; official listing needs owner approval |
| DOC-02 | README/EN/USER_GUIDE 실행 결과 동기화 | NEEDS_REVIEW | tests/test_docs_sync.py: 문서의 모든 서브커맨드/플래그가 실제 CLI에 존재 | 미지정 | INSTALLATION_AND_SHARING/COPILOT_SETUP 재작성 |
| DOC-01 | 설치/배포/ Copilot 문서 | SCAFFOLD | INSTALLATION_AND_SHARING, COPILOT_SETUP, MARKETPLACES | 미지정 | 실제 설치 후 업데이트 |

상태: `TODO`, `IN_PROGRESS`, `NEEDS_REVIEW`, `BLOCKED`, `DONE`, `SCAFFOLD`.

## 반복 시행착오 차단 기록

| 문제 ID | 실패 접근 | 실패 근거 | 재시도 조건 | 최종 검증 |
|---|---|---|---|---|
| R-001 | `ensure_ascii=False` JSON를 cp949 콘솔로 출력 | write 성공 후 `HANDOFF_ERROR: 'cp949' codec…`, 저장은 됐는데 실패 보고 | stdout/stderr UTF-8 재설정 유지 | `test_skill_package` clean-copy (non-ASCII mission) |
| R-002 | `mkdir(mode=0o700)` | Win + Python>=3.13: 소유자 전용 ACL → 샌드박스 호스트/git이 세션 디렉터리 접근 불가 (icacls로 확인) | mode 인자 없이 생성 | `test_session_dir_created_without_restrictive_mode` (fix 제거 시 FAIL 확인) |
| R-003 | SKILL.md가 `python`/`py -3`/`python3` 가정 | Codex 샌드박스에서 WindowsApps alias 실행 불가 -> resume 중단 | 실제 인터프리터 경로 지정 안내 (SKILL.md) | Codex 재실행 resume 성공 (수동 증거; 자동 테스트 불가) |
| R-004 | `git` stdout을 콘솔 코드페이지(cp949)로 디코딩 | 한글 worktree 경로 깨짐 -> `--all-worktrees`가 해당 checkout 누락 | `git()`가 UTF-8로 디코딩 | `test_all_worktrees_lists_sessions_from_every_checkout_read_only` (fix 제거 시 FAIL 확인) |
| R-005 | `git status`로 dirty 계산 | 코어 자신의 `.write.lock`/`session.json` 때문에 깨끗한 트리도 항상 dirty=True | `.handoffs/` 제외 pathspec (`observe_git`) | `test_own_store_files_do_not_make_clean_tree_dirty` (fix 제거 시 FAIL 확인) |
| R-006 | `--all-worktrees`가 root와 git이 알려준 경로를 문자열 비교 | GitHub Actions windows-latest(8.3 짧은 임시 경로)에서 같은 checkout이 두 번 나열됨 (로컬에서는 Windows 짧은 경로를 직접 만들어 재현) | root를 `resolve()`한 뒤 비교 | `test_all_worktrees_does_not_duplicate_when_root_given_as_windows_short_path` (fix 제거 시 FAIL 확인) |

## 검증 로그

| 시각(UTC) | ID | 환경 | 명령 | 결과 | 커밋/로그 |
|---|---|---|---|---|---|
| 2026-11-06 | P0-03 | Win11, py3.14.6 | `python scripts/check_upstreams.py` | both up_to_date | — |
| 2026-11-06 | P1/P2 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 19 tests OK, 1 skipped | 73c1586 |
| 2026-11-07 | P5-04 | Win11; claude 2.1.319, copilot 1.0.105 | `claude plugin marketplace add rch4com/agent-handoff-manager` + install/uninstall; `copilot plugin marketplace add …` + `browse` + `install` | both installed; Claude core ran from marketplace clone; Copilot installed 1 skill, core ran | commit 2bcb685; Claude entries removed afterwards, Copilot plugin left installed for user E2E |
| 2026-11-07 | acceptance #1 | Win11; gh 2.103.3 `--pin 74b9026`; codex 0.165.0 -> Claude Code 2.1.319 | codex write (`--depth rich`, failure_records) then claude `resume latest` in the same repo | id 20261106T163716Z-14b47991a90a: failed attempt, file, validation claim (not_run) preserved; Claude declined to retry sed and listed warnings. Commits/tests are only as good as the payload (claims) | /tmp temp repo ahm-e2e2 (not committed) |
| 2026-11-07 | CI | GitHub Actions run 42252689698 @0bd9c4b: ubuntu-latest + windows-latest x Python 3.10/3.12 | `python -m unittest discover -s tests -v` + `validate_distribution.py` | success (4/4 jobs). Earlier runs 0851fc8..4dd9951 failed on windows-latest only (R-006) | https://github.com/rch4com/agent-handoff-manager/actions/runs/42252689698 — unit-test evidence on Linux; host E2E on Linux still not run |
| 2026-11-07 | P3-01 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 68 tests OK, 4 skipped (symlink privilege) | see commit |
| 2026-11-07 | P2-05/#3 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 61 tests OK, 3 skipped (symlink privilege); concurrency test (6 processes) stable 6/6 runs | see commit |
| 2026-11-07 | P2-02 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 52 tests OK, 2 skipped (symlink privilege) | see commit |
| 2026-11-07 | P2-01 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 45 tests OK, 1 skipped | see commit |
| 2026-11-07 | P2-04 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 38 tests OK, 1 skipped | see commit |
| 2026-11-07 | P2-03/DOC-02 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 35 tests OK, 1 skipped; docs-sync test fails when a doc flag is misspelled (mutation checked) | see commit |
| 2026-11-07 | P1-02 | Win11, py3.14.6 | `python -m unittest discover -s tests` | 26 tests OK, 1 skipped (symlink privilege) | see commit below |
| 2026-11-06 | P4-08 | Win11, node 26.13, npx skills | `npx skills add D:/…/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex -a opencode -a antigravity -a github-copilot --copy -y` | installed `.agents/skills`+`.claude/skills`, identical copies, script runs | scratchpad proj1 |
| 2026-11-06 | P4-01 | Claude Code 2.1.319 | `claude -p … --model haiku --allowedTools Bash(python:*)…` write+list | session created, id reported | `.handoffs/sessions/20261106T045455Z-61fc48eb5653` |
| 2026-11-06 | P4-02 | codex-cli 0.165.0 | `codex exec -s workspace-write` resume latest | 1st run blocked (R-003), 2nd run OK, no diffs vs saved | — |
| 2026-11-06 | P4-08 | gh 2.103.3 | `gh skill install rch4com/agent-handoff-manager agent-handoff-manager --agent <5 ids> --scope project` | installed; core executes | repo @137799a |
| 2026-11-06 | P4-08 | node 26.13 | `npx skills add rch4com/agent-handoff-manager --skill agent-handoff-manager -a claude-code -a codex --copy -y` | installed | repo @137799a |
| 2026-11-06 | P4-06 | Copilot CLI 1.0.105 | `copilot -p '…resume latest…' --allow-tool=shell` (cwd = gh-installed project) | resume OK, correct mission/writer/diff | user-run |
| 2026-11-06 | P4-04 | agy 1.5.0 | `agy -p '…resume latest…'` | resume OK + flagged missing claimed file | user-run |
| 2026-11-06 | P4-03 | opencode 1.19.4 | `opencode run '…'` (default model) x2 | UnknownError before tool call | provider config, not a product result |
| 2026-11-06 | P4-03 | opencode 1.19.4 | `opencode run -m opencode/big-pickle '…resume latest…'` | resume OK, correct, independent verification | user-run |

## Copilot 및 외부 배포 필수 추가 로그

| 호스트 | Skill 발견 | Core 설치/호출 | E2E | 버전/OS/증거 |
|---|---|---|---|---|
| Copilot VS Code Agent | TODO | TODO | TODO | — |
| Copilot CLI | PASS | PASS (resume) | write 미검증 | v1.0.105, Win11, gh-installed 사본 |
| Copilot Cloud Agent | TODO | TODO | TODO | — |
| `gh skill` Public 원격 설치 | PASS (5 agent ids) | PASS (init/write/list/doctor) | TODO | gh 2.103.3, Win11, repo @137799a |
| `npx skills` Public 원격 설치 | PASS (claude-code, codex) | TODO | TODO | Win11, node 26.13, @137799a |
