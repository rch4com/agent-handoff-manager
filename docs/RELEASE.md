# 공개 릴리스 체크리스트 — Agent Handoff Manager

## 대상 배포물

- Public GitHub repo: `rch4com/agent-handoff-manager`
- `skills/agent-handoff-manager/SKILL.md` 및 해당 경로 내 모든 실행 리소스
- 작동하는 Python 공통 코어: 스킬 폴더 안에 포함 (ADR-0002)
- Windows/Linux 설치·업데이트·제거 및 롤백 정책
- Claude Code, Codex, OpenCode, Antigravity, GitHub Copilot (VS Code/CLI/Cloud) 호환성 보고서
- MIT 등 최종 LICENSE + 원본 ④/③ 저작권·재배포 고지

## Preflight (모두 실제 통과해야 함)

- [x] 실제 `LICENSE`(MIT, rch4com), upstream notices는 원본 LICENSE blob과 대조해 `THIRD_PARTY_NOTICES.md`에 기록
- [x] `upstreams.lock.json` ④/③ 채택 SHA 고정 및 ADR 작성 (ADR-0003)
- [x] 스킬 설치 직후 core 호출이 성공 (gh skill/npx skills 설치본 실행, clean-copy 테스트)
- [ ] 5호스트 7표면과 Windows/Linux 테스트 결과 공개 (Windows 5호스트 중 일부만; `docs/COMPATIBILITY.md`)
- [ ] write→list→resume→archive→restore, 충돌/비밀정보/마이그레이션 테스트 통과
- [x] `gh skill preview`/`gh skill install` 실제 Public 원격 테스트 (gh 2.103.3, Windows 11)
- [x] `npx skills add` 실제 Public 원격 테스트 (대체 경로)
- [x] 프로젝트 스킬 설치 시 AGENTS.md 등 기존 설정 무손상 (SHA-256 동일 확인)
- [ ] 버전 pin/업데이트/제거/롤백 E2E 통과 (pin 건너뜀과 제거 후 재설치 데이터 보존만 검증; 새 태그로의 update는 미검증)
- [ ] 보안 리뷰/비밀 스캔 및 Copilot Cloud 실행 권한 검증
- [ ] 사용자 설치/사용 문서의 모든 명령이 실제 동작

## Release versioning

- `v0.1.0`: internal beta / 실 사용자 설치 검증 전; README에서 알림
- `v0.x`: 릴리스 후보, breaking schema changes 문서 필수
- `v1.0.0`: 기능 4개 + 5호스트 호환 + 공개 배포 검증 완료 후
- Tag/Release 간 Python 코어와 SKILL.md 버전 정합성 필수

## External publication

1. GitHub Public repository 생성 (소유자 승인 후).
2. `gh skill publish --dry-run` 지원 가능 환경에서 확인; 결과 및 검증 로그 보관.
3. GitHub Release와 체크섬 발행.
4. 외부 사용자 계정에서 `gh skill preview` → `gh skill install` → 실제 4명령 검증.
5. 선택: Claude/Copilot 각각의 Plugin Marketplace 설정 및 플러그인 설치 테스트.
6. `docs/INSTALLATION_AND_SHARING.md`, README 영어/한국어 갱신.

## Upstream update and rollback

업스트림 watcher는 issue만 갱신하며 승인되지 않은 source code를 제품에 반영하지 않는다. 새 원본 적용은 review PR과 테스트, 승인을 거친 tag에서만 가능. 롤백 시 기존 schema/data 백업을 보존하고 사용자 인계 기록을 삭제하지 않음.
