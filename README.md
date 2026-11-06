# Unified Handoff Manager — 개발 착수 문서 패키지

> 상태: **설계·작업지시서 + 업스트림 모니터링 초안** (통합 스킬 런타임은 아직 구현되지 않음)
> 기준일: 2026-11-06 / 대상: Claude Code, Codex CLI, OpenCode, Antigravity, GitHub Copilot (VS Code Agent/CLI/Cloud)

## 목적

두 MIT 공개 프로젝트를 근거로 **프로젝트의 검증된 장기 상태**와 **개별 세션의 인계 기록**을 분리하고,
`write`, `resume`, `list`, `archive`를 일관된 인터페이스로 제공하는 공개 배포용 스킬을 개발합니다.

- ④ [WeirdSky924/agent-handoff-skill](https://github.com/WeirdSky924/agent-handoff-skill): `AGENT_HANDOFF.md`, `.agent-handoff/`, bootstrap / maintain, 장기 프로젝트 상태.
- ③ [aploe/claude-handoff-skill](https://github.com/aploe/claude-handoff-skill): 네 가지 세션 명령, 인계 문서, resume 검증, 보관.
- 원본 변경 감시 = 자동. 원본 변경을 제품으로 채택/배포 = 검증된 PR 승인 뒤. **무검증 자동 병합 금지.**

## 시작할 파일

1. `WORK_ORDER.md`: 개발 CLI에 통째로 전달할 실행 지시서와 완료 기준.
2. `AGENTS.md`: Codex 및 다른 에이전트가 따라야 할 저장소 공통 규칙.
3. `INTENTS.md`: 제품 목표, 범위, 비목표, 설계에서 절대로 깨지면 안 되는 불변조건.
4. `INDENTS.md`: 요청한 이름 그대로 포함한 코드/문서 들여쓰기 및 서식 규칙. (*INTENTS와 다른 파일*)
5. `ARCHITECTURE.md`: 데이터 권한, 동시성, 업데이트 구조.
6. `PROJECT_TRACKER.md`: 마일스톤, 완료 체크박스, 검증 증거 기입란.
7. `docs/USER_GUIDE.md`: 사용자 가이드 초안 — **예시 명령은 구현 후 사용 가능**.
8. `docs/UPSTREAM_POLICY.md`: 버전 pinning, 변경 감지, 분석·테스트·릴리스 정책.

## 현재 들어 있는 실행 가능 부분

- `scripts/check_upstreams.py`: 공개 GitHub 브랜치 HEAD와 `upstreams.lock.json`의 채택 SHA를 비교하는 **검토 알림용** 프로그램.
- `.github/workflows/upstream-monitor.yml`: 매주 업스트림 차이 확인 후 이슈 생성 또는 갱신.
- `.github/workflows/ci.yml`: Windows/Linux에서 모니터링 스크립트 단위 테스트.
- `tests/test_upstreams.py`: 위 모니터링 스크립트의 오프라인 테스트.
- `skills/agent-handoff-manager/SKILL.md`: **스킬 인터페이스 설계서(비작동 명세)**.

현재 `write/resume/list/archive`는 아직 구현되지 않았으므로 설치된 완성품으로 취급하지 마세요.

## 개발 시작 방법

```powershell
# 압축 해제 후 해당 폴더에서
python -m unittest discover -s tests -v
# 이어서 Claude Code / Codex 등에 아래 지시
# 'WORK_ORDER.md와 AGENTS.md, INTENTS.md를 읽고 P0부터 구현하라.'
```

업스트림 모니터링은 인터넷에 연결된 GitHub Actions에서 작동합니다. 초기 `upstreams.lock.json`의 `adopted_sha`는 `null`이므로 **각 원본 소스를 조사하고 검증된 커밋으로 잠가야 배포 가능합니다**.

## 배포 전 필수

- 소유자/조직과 최종 저장소 URL 결정, `LICENSE.template`을 실제 `LICENSE`로 교체.
- 두 업스트림의 해당 시점 원본 저작권·MIT LICENSE를 `THIRD_PARTY_NOTICES.md` 또는 `licenses/`에 보존 (코드를 재사용하는 경우).
- Claude / Codex / OpenCode / Antigravity / GitHub Copilot(VS Code/CLI/Cloud)에서 실제 설치·명령·복구 검증.
- 보안 점검, Windows/Linux 테스트, 문서 예제 실행 확인, 버전 태그 및 릴리스 노트.

## 문서 지도

- [실행 지시서](WORK_ORDER.md) · [설계](ARCHITECTURE.md) · [진척](PROJECT_TRACKER.md)
- [CLI 사용법](docs/USER_GUIDE.md) · [업스트림 정책](docs/UPSTREAM_POLICY.md)
- [설치·호환성](docs/COMPATIBILITY.md) · [기밀정보 보안](docs/SECURITY.md)
- [검증 계획](docs/TEST_PLAN.md) · [배포 계획](docs/RELEASE.md) · [기여](docs/CONTRIBUTING.md)
- [English overview](README.en.md)

## 공개 배포 및 Copilot까지 포함한 설치 지침 (2026-11-06 업데이트)

- **권장 저장소 이름**: `agent-handoff-manager` (GitHub 계정은 `YOUR_GITHUB_ID`로 표시; 실제 공개 저장소는 아직 생성되지 않음).
- **권장 스킬 이름**: `agent-handoff-manager`; 정식 개발 후 `gh skill preview YOUR_GITHUB_ID/agent-handoff-manager agent-handoff-manager`로 검토, `gh skill install ... --agent github-copilot` 등으로 설치.
- **지원 계획**: Claude Code / Codex / OpenCode / Antigravity / GitHub Copilot (VS Code Agent, Copilot CLI, Copilot Cloud Agent).
- **핵심 선결조건**: SKILL.md 복사만으로 공통 Python core 설치가 보장되지는 않음. Core를 스킬 내부에 포함할지, 설치식 wheel로 배포할지 P4에서 확정하고 검증.
- **마켓플레이스**: GitHub Public + Agent Skills 설치는 등록 없이 가능. Claude와 Copilot은 서로 다른 plugin marketplace 규격을 제공하므로 추후 선택적으로 배포.
- [자세한 설치/공유 매뉴얼](docs/INSTALLATION_AND_SHARING.md) · [Copilot 안내](docs/COPILOT_SETUP.md) · [마켓플레이스 정책](docs/MARKETPLACES.md) · [호환성](docs/COMPATIBILITY.md).

`python scripts/validate_distribution.py`로 이 스타터의 문서와 SKILL 메타데이터를 점검할 수 있습니다. 실제 설치 또는 handoff 명령이 동작함을 입증하는 테스트는 아닙니다.

## P0/P1 강화판 — 로컬 파일럿 추가 (2026-11-06)

이 배포물은 **완성된 5개 에이전트 통합 제품이 아닌 개발 키트 + 실행 가능한 로컬 파일럿**입니다. `skills/agent-handoff-manager/scripts/handoff.py`로 명시적 JSON payload 기반의 `init/write/list/resume/archive/restore/doctor`를 실행할 수 있습니다. 그러나 플랫폼별 실제 어댑터, 원격 스킬 설치, cross-machine 동기화는 미구현/미검증입니다. 기존 문서에 등장하는 광범위한 명령은 목표 계약일 수 있습니다.

실행 예시: [docs/PILOT_QUICKSTART.md](docs/PILOT_QUICKSTART.md). 규격: [docs/SCHEMA_SPEC.md](docs/SCHEMA_SPEC.md), [docs/ADAPTER_CONTRACT.md](docs/ADAPTER_CONTRACT.md), [docs/RECOVERY_PROTOCOL.md](docs/RECOVERY_PROTOCOL.md), [docs/RELEASE_GATES.md](docs/RELEASE_GATES.md). 테스트: `python -m unittest discover -s tests -v`.

업스트림 lock 파일에 `adopted_sha: null`인 것은 아직 검증/채택되지 않았음을 뜻합니다. 자동으로 임의 SHA를 채우지 않았습니다. 기준선 검토가 필요하지만 이것만으로 새 업데이트 이슈를 만들지 않습니다.
