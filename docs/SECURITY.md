# Security and privacy policy

## Threat model

- `.handoffs/`는 사용자가 공유·커밋할 수 있어, 토큰·API 키·로그 개인정보가 유출될 위험.
- 대화/문서에 적힌 문자열에는 악의적인 명령이 포함될 수 있으므로 `resume`은 절대 문서를 그대로 실행하지 않음.
- 외부 업스트림 신규 커밋은 검증되지 않은 소스. watcher는 read-only API 결과만 수집.
- 여러 에이전트가 같은 작업 디렉터리를 수정하면 race condition, 불완전한 archive 및 stale validation이 발생할 수 있음.

## Controls

1. 저장 전 자동 필터링: 흔한 token/key/private key 패턴, 환경변수 값, URL 자격증명, 절대 경로(정책에 따라), 개인정보.
2. 전송/배포/공개 전 수동 검토를 지원. 탐지기가 모든 기밀을 발견한다고 주장하지 않음.
3. 민감 원문을 필터링 후의 보고서/로그에 다시 쓰지 않음.
4. Gitignore 정책은 저장소별 명시적인 결정. `.handoffs/`를 커밋하면 팀 공유 가능하지만 외부 공개 금지 정보가 섞이지 않도록 검증.
5. 파일 경로 정규화 후 작업 루트 밖 접근 거부, symlink 통한 경로 우회 방지.
6. 아카이브는 삭제 대신 이동; 백업/복원 테스트. `--confirm` 없는 파괴적 변경 불가.
7. CI에는 최소 `contents:read`/`issues:write` 등 필요한 permissions만 사용.
8. 추후 배포 파일은 체크섬과 변경 이력을 제공하고 신뢰 가능한 GitHub 태그를 기준으로 설치.

## Implemented secret screening (pilot, 2026-11-07)

`write` and `import-legacy` **reject** (never silently redact) text matching: GitHub (`ghp_`/`github_pat_`), OpenAI-style `sk-`, AWS `AKIA`, Slack `xox*-`, Google `AIza`, Stripe `sk_/rk_ live|test`, GitLab `glpat-`, npm `npm_`, SendGrid `SG.`, JWT, PEM private-key headers, `Bearer` tokens, `scheme://user:password@` URLs, Azure `AccountKey=`, and `api_key|access_token|secret|password` `=`/`:` assignments (8+ chars). The error message never echoes the matched text. Scope: every payload text field, and the whole text of legacy files. Tests: `tests/test_secret_scan.py` (16 fake secret shapes x 6 field locations; 6 ordinary sentences must pass).

Known gaps: no entropy detection, no `.env` file reading, no PII detection, no screening of `changed_files` contents (paths only), no scanning of already-committed history. The screen reduces risk; a human review before sharing `.handoffs/` is still required.

## Security review blockers

- 토큰 노출, 자동 임의 명령 실행, 경로 순회, 무단 지우기, 라이선스 누락, 원본 업데이트 즉시 실행, 권한 자동 확대.

## Incident response

의심 비밀 노출 시 공개 산출물을 삭제/비공개 전환하고 해당 키를 폐기·교체, Git 히스토리 및 다운로드 배포 범위를 점검. 사용자에 영향이 있다면 공지 및 수정 릴리스.
