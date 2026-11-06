# Upstream update policy — Source ④ + ③

## Sources and current observations

| ID | Source | Monitored branch | Purpose |
|---|---|---|---|
| `agent-handoff` | `WeirdSky924/agent-handoff-skill` | `main` | durable state and compaction |
| `claude-handoff` | `aploe/claude-handoff-skill` | `main` | write/resume/list/archive semantics |

두 프로젝트 모두 2026-11-06 기준 GitHub에 MIT 라이선스로 표시되었음. 실제 소스 재사용 전 SHA와 원본 LICENSE를 다시 확인해야 합니다.

## Levels of upstream update

| Level | Auto action | Human gate |
|---|---|---|
| Discover | GitHub API에서 새 HEAD 조회, issue 생성/수정 | 필요 없음 |
| Analyze | 변경 파일, API, 템플릿, 저장 포맷, 호환성 영향표 작성 | 영향도 검토 |
| Adapt | adapter/vendor 소스 변경을 **별도 PR**에 구현 | 코드 리뷰 필수 |
| Verify | Windows/Linux + CLI별 smoke, migration, security | 미통과 시 차단 |
| Release | 버전, changelog, notices, 설치 파일 게시 | maintainer 승인 |

> **중요:** 모니터링만으로 ④나 ③의 코드를 자동으로 설치/실행/병합하면 안 됩니다. 새로운 원본 코드 자체가 실행 권한·파일 삭제·프롬프트 동작을 바꿀 수 있으므로 신뢰 경계를 반드시 둡니다.

## Version pinning

`upstreams.lock.json`의 `adopted_sha`는 검토 후 제품에 실제 채택한 40자 commit SHA입니다. `null`이면 아직 기준선을 채택하지 않은 상태이며 출시 차단 조건입니다. (2026-11-06 두 원본 모두 검토 후 pin 완료, 코드는 가져오지 않음: ADR-0003.) 모니터링이 발견한 `latest_sha`는 보고서/이슈에만 기록하고 lock을 저절로 갱신하지 않습니다.

변경 확인:

```bash
python scripts/check_upstreams.py --lock upstreams.lock.json --report upstream-report.md
```

인터넷/토큰 제한 상황에서는 오류를 명확히 출력하고 성공으로 가장하지 않습니다. GitHub Actions는 `GH_TOKEN` 없이도 공개 API를 조회할 수 있으나 rate limit 방지를 위해 자동 제공되는 `GITHUB_TOKEN`을 우선 활용합니다.

## PR checklist

- [ ] 기존 채택 SHA와 신규 후보 SHA, diff URL, 채택 이유.
- [ ] 원본 라이선스 및 저작권 고지 변경 확인.
- [ ] API 또는 문서 인터페이스 변경 분석.
- [ ] 명령별 호환·회귀 테스트 결과.
- [ ] 기존 프로젝트/인계 파일 migration dry-run 및 rollback 확인.
- [ ] 위험한 script / hook / 네트워크 권한 변경 수동 검토.
- [ ] release note와 사용법, 지원 CLI 버전 갱신.
- [ ] 승인된 SHA만 lock에 반영.

## Update cadence

기본적으로 매주 월요일 UTC 02:00 점검하고, 수동 `workflow_dispatch` 제공. 새 HEAD가 있으면 동일한 tracking issue에 최신 보고서를 갱신. 검토/적용 스케줄은 별도이며 업데이트 가용성이나 유지보수 SLA를 의미하지 않습니다.

## Failure policy

- 원본이 사라지거나 라이선스가 바뀌면 자동 배포 중단, 마지막 검증된 버전 유지.
- 호환성 테스트 실패 시 자동 배포 중단, 원인과 재현 조건 기록.
- upstream changed + monitor failed는 별도의 오류로 보고, **업데이트 없음**으로 오인하지 않음.
- 기존 사용자 자료 구조는 SemVer, schema_version, migration 정책을 별도 적용.
