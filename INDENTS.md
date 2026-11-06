# INDENTS.md — Code and documentation formatting

> 이 파일은 요청하신 `indents.md` 표기를 반영한 **서식/들여쓰기 정책**입니다. 목표 및 개발 의도는 `INTENTS.md`에 작성합니다. 둘 다 Agent Skills 표준 필수 파일은 아닙니다.

## Source style

- Python 3.10+; PEP 8; 들여쓰기 공백 4칸; line ending LF; UTF-8 (BOM 없음).
- Python 함수와 명령은 작은 단위로 분리하고 타입 힌트 포함. 프로세스 종료 코드는 명확히 정의.
- JSON: 공백 2칸, 키 순서 안정화(출력 시 `sort_keys=True`), UTF-8, 종단 개행.
- YAML: 공백 2칸, 탭 금지, 명령/권한 최소화.
- Markdown: 제목 한 번만 `#`, 하위 헤더 연속, 명령 코드는 언어 지정, 예제의 입력/출력 구분.
- CLI 명령은 Bash/PowerShell 모두에서 의미가 일관돼야 하며, 셸 의존 부분을 별도로 표기.
- 날짜: UTC ISO 8601; 파일 ID `YYYYMMDDTHHMMSSZ-<8hex>`; 사용자 현지 날짜는 출력만 현지화.

## Document evidence convention

실제로 수행한 작업만 `[verified]`라고 표기. 미실행 `[not-run]`, 가정 `[assumption]`, 확인 불가 `[unknown]`.
완료 보고에는 명령, 실행 환경, 결과, 시각, 커밋을 적을 것.

## Naming

- 코드: `snake_case.py`, 클래스 `PascalCase`, CLI `kebab-case`.
- 문서: 저장소 루트 정책 파일은 `UPPER_SNAKE_CASE.md`, 사용자 문서는 설명적인 이름.
- 변경사항: `fix:`, `feat:`, `docs:`, `test:`, `chore:` 형태의 커밋 제목 권장.

## Style gates

- 포매터/린터 자동 수정은 변경 diff를 검토한 뒤 적용.
- 근거 없이 대량 리포맷 금지; 작업과 무관한 소스 수정 금지.
- 공식 기록과 세션 이력의 내용은 기본적으로 한국어/영어 둘 다 지원하되, 시스템용 메타데이터 키는 영어로 고정.
