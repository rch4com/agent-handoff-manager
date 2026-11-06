# 작업 지시서 — Unified Handoff Manager (④+③ 통합)

## 역할과 목적

당신은 공개 배포 가능한 크로스 CLI Handoff 스킬을 개발한다. 시작 전 `AGENTS.md`, `INTENTS.md`, `ARCHITECTURE.md`, `PROJECT_TRACKER.md`, `docs/UPSTREAM_POLICY.md`를 읽고, 현재 Git/파일 상태를 점검하라. 문서에 없는 구현은 임의 완료 처리하지 말고 증거를 남겨라.

### 원본 소스

- ④ `https://github.com/WeirdSky924/agent-handoff-skill` — 공식 프로젝트 상태/장기 검증 기록/유지보수와 용량 관리.
- ③ `https://github.com/aploe/claude-handoff-skill` — write/resume/list/archive, 인계 템플릿, 환경 검증, 세션 아카이브.
- 소스 파일, 라이선스, 실제 commit SHA는 개발 시작 시 `git`으로 확인. 양쪽 모두 MIT로 표기되어 있으나 재배포한 파일의 고지를 실제 원문과 재확인할 것.

## 아키텍처 결정 (수정하려면 ADR 작성)

1. `AGENT_HANDOFF.md` + `.agent-handoff/` = 검증된 프로젝트 장기 상태의 single source of truth.
2. `.handoffs/sessions/<id>/{metadata.json,handoff.md}` = 각 세션 인계 저장. `.handoffs/archive/`는 되돌릴 수 있는 보관소.
3. 인덱스는 디렉터리 스캔 또는 재생성 가능한 캐시. 중앙 사용자 인덱스는 읽기 전용/파생 정보로 관리하고 Git 충돌의 공식 출처로 사용하지 않는다.
4. Python 3.10+ 공통 CLI 코어. CLI별 SKILL.md/슬래시 명령/설정은 얇은 adapter. 구현하지 않은 호스트 네이티브 명령을 된다고 표기하지 말 것.
5. 업스트림 채택은 SHA pin + 변경 영향분석 + 테스트 + 수동 승인을 거친 릴리스에서만 실시.

## 마일스톤과 순서

### P0 — 조사·기준선·권리 정리
- [ ] 두 원본 최신 기본 브랜치, 최근 변경, SKILL.md, 스크립트·템플릿, 호환 API를 조사.
- [ ] `upstreams.lock.json`의 `adopted_sha`를 확인된 전체 40자리 SHA로 pin.
- [ ] 코드 재사용 범위와 SPDX, MIT 저작권 고지를 명시하고 `THIRD_PARTY_NOTICES.md` 작성.
- [ ] 실제 지원되는 CLI별 진입점/설치 경로를 **문서 및 테스트**로 확인.
- [ ] ADR: 직접 vendor vs stable adapter 결정 (권장: 포크 통합보다 adapter + 필요한 부분의 최소 vendor).
**Exit:** lock SHA 2개, 증거 링크, 변경 영향표, 재사용 고지 확인.

### P1 — 상태 스키마·스토리지·마이그레이션
- [ ] 버전이 있는 `metadata.json` 스키마 (`schema_version`, `id`, `project_id`, `status`, `agent`, `branch`, `head`, `created_at`, `updated_at`, `validation`, `next_step`).
- [ ] ID 충돌 방지, 원자적 쓰기, 장애 복구, 경로 순회 차단, 중복 archive 처리.
- [ ] ④ 기존 문서 보존; ③ 기존 `.handoffs/*.md`를 손실 없이 가져오기. 원본은 보관.
- [ ] 캐시 파손 시 목록이 문서 스캔으로 복구되어야 함.
**Exit:** 스키마·마이그레이션·충돌·복구 테스트 통과.

### P2 — 공통 명령 4종 + 검증
- [ ] `write`: depth(auto/minimal/rich/exhaustive), 사실/주장 분리, 비밀정보 필터, 명시적 next step, 세션 메타 기록.
- [ ] `list`: project/status/agent/date 필터, active/archive 구분, Git worktree에서도 읽기.
- [ ] `resume`: 검증 보고만 수행, 환경 불일치 표시, 허용되지 않은 코드 실행 없음, 실제 완료 증거 확인.
- [ ] `archive`: dry-run, 명시적 확인, 이동 후 목록 반영, `restore` 별도 구현으로 복구 가능.
- [ ] `doctor`: 초기 상태와 형식 오류, 누락, 경로·CLI 호환 검진.
**Exit:** 각 명령 success/failure 케이스 + end-to-end write→list→resume→archive→restore 완료.

### P3 — ④ 영구 상태와 ③ 세션 통합
- [ ] `write` 완료 시 프로젝트 상태의 변경 후보를 제시하되 무검증 사실을 완료로 자동 승격하지 않음.
- [ ] `resume`은 `AGENT_HANDOFF.md` → snapshot/risks/validation → 선택 세션 순서로 검증.
- [ ] 동일 기술 결함 반복을 방지할 수 있도록 failed approach / evidence / regression status 기록.
- [ ] ④ snapshot compaction / rotation과 ③ archive가 서로 자료를 삭제하지 않도록 각각의 책임 격리.
**Exit:** 비승인 세션의 완료 주장이 공식 상태를 덮지 않는 회귀 테스트.

### P4 — 5개 호스트 어댑터와 7개 실행 표면 설치
- [ ] Codex CLI, Claude Code, OpenCode, Antigravity, GitHub Copilot(VS Code Agent/Copilot CLI/Cloud Agent)의 해당 **버전**에서 실제 Skill 경로/호출/보안 정책 확인.
- [ ] 일관된 `python -m unified_handoff ...` 또는 설치된 `handoff ...` 명령 구현.
- [ ] 진입점은 네이티브 슬래시 명령이 없더라도 공통 CLI로 사용 가능하게 설계.
- [ ] PowerShell/Bash 설치·업그레이드·제거 및 기존 설정 병합 테스트.
**Exit:** OS × 5호스트(7표면) smoke tests에서 skill 발견·core 실행·write/list/resume/archive 통과, 미검증은 명시.

### P5 — 지속 업데이트·배포·커뮤니티
- [x] 업스트림 SHA 변화를 확인하는 모니터링 **초안** 제공 (`scripts/check_upstreams.py`, GitHub workflow).
- [ ] upstream 변화 발생 시 기존 issue 업데이트, 담당자가 영향분석 및 `adopted_sha` 업데이트 PR 작성.
- [ ] PR에서 contract/compat/security/migration 테스트, 리뷰 후 merge, SemVer/CHANGELOG 작성.
- [ ] `README.md` / 영어 README / 설치·사용법 / FAQ / 예제 프로젝트 / 기여·보안·라이선스 고지.
- [ ] 설치 가능한 릴리스 artifact, 릴리스 체크섬/서명 정책 및 공용 GitHub Releases.
- [ ] 실제 다른 사용자 환경에서 새 프로젝트 설치 → 인계 → 재개 → 제거 시험.
**Exit:** v1.0 배포 후보의 모든 수용 조건 통과. 공개 저장소와 릴리스는 소유자가 개설/승인.

## 필수 수용 테스트 (최소)

1. 다른 에이전트로 전환했을 때 수정 파일·커밋·테스트·이전 실패가 보존될 것.
2. `resume`이 잘못된 branch/HEAD/dirty 상태를 경고하고 직접 실행하지 않을 것.
3. 두 에이전트가 동시에 `write`해도 서로 덮어쓰지 않을 것.
4. `archive`가 장기 공식 기록을 손대지 않고 원복 가능할 것.
5. 기존 ④/③ 파일이 있는 프로젝트에 `init`을 여러 번 적용해도 손실/중복 없을 것.
6. 업스트림 change alert만으로 제품 설치 코드가 변경되지 않을 것.
7. secret/token fixture가 인계에 노출되지 않을 것.
8. 공개 설치 예시가 Windows + Linux에서 실제 재현될 것.
9. 외부 원본 라이선스 및 자체 재배포 고지가 포함될 것.
10. 사용자 가이드의 명령/출력이 실제 CLI와 동일할 것.

## 보고 형식

작업 시작: Git HEAD/branch, 조사한 원본 SHA, 작업 ID, 소유자, 변경 대상 파일.
작업 종료: [구현한 기능] [수정 파일] [커밋] [실제 테스트/결과] [미검증] [실패한 시도 및 반복 금지] [차기 단일 작업].
`PROJECT_TRACKER.md`에서 체크박스를 완료 처리하기 전에 위 증거를 남겨라.

### P4 보강 — 실제 공개 설치 패키징
- [ ] `skills/agent-handoff-manager/SKILL.md`를 canonical source로 유지. SKILL frontmatter name과 폴더명을 반드시 일치시킬 것.
- [ ] 설치된 SKILL.md에서 Python core를 실제로 호출할 수 있도록 배포 방식(A: skill 내 포함 / B: pinned wheel) 결정하고 ADR 기록.
- [ ] `gh skill preview/install/update` 및 `npx skills add`로 **외부 Public GitHub repository**에서 원격 설치·작동 검증.
- [ ] Copilot 3개 표면: VS Code Agent, Copilot CLI, Copilot Cloud Agent에서 discovery + core execution + 데이터 공유/복구 시험.
- [ ] 기존 `AGENTS.md`, `.github/copilot-instructions.md`, `.claude/CLAUDE.md`가 있는 저장소에서도 설치가 비파괴적인지 검증.
- [ ] `docs/INSTALLATION_AND_SHARING.md`, `docs/COPILOT_SETUP.md`, `docs/COMPATIBILITY.md`를 설치 명령과 시험 증거에 따라 갱신.
- [ ] 온보딩 흐름: 새 GitHub 사용자 -> preview -> install -> Python 준비 -> write/resume -> upgrade -> uninstall까지 테스트.

### P5 보강 — GitHub Skills 및 양쪽 Marketplace
- [ ] `gh skill publish --dry-run` 검증 후 공개 skill 노출 절차 조사/시험.
- [ ] Claude Code marketplace와 GitHub Copilot marketplace는 **서로 다른 포맷**이므로 각각 매니페스트 작성·검증.
- [ ] skill 설치 경로와 plugin 설치 경로에서 중복 인식/명령 충돌이 없는지 점검.
- [ ] 사용자에게 Release 태그 pin 방법, 후속 update 방법, changelog와 breaking change 안내.
- [ ] E2E 5개 호스트 + Copilot 3개 표면을 검증하지 않았다면 v1.0.0 호환성 지원을 선언하지 않음.
