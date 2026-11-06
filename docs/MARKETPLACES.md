# 공개 마켓플레이스 배포 계획 — 선택 사항

**우선순위:** 1) GitHub Public + Agent Skills 설치, 2) 양 플랫폼의 실제 설치 검증, 3) 마켓플레이스 플러그인 포장, 4) 공개/디렉터리 노출.

## Claude Code Plugin Marketplace

Claude Code의 플러그인 marketplace 형식은 `.claude-plugin/marketplace.json` 기반. 플러그인 내부 자체 매니페스트/skills 경로를 맞춰야 함. 원본 ③의 `/handoff:*`와 충돌하지 않도록 통합 플러그인은 고유 이름 `agent-handoff-manager`를 사용.

- 개발 시 Claude 공식 marketplace/plugin authoring 문서와 검증 도구의 최신 버전 확인.
- plugin directory, skill folder, 실행 코어의 상대경로/설치 부작용을 검증.
- 예시 사용자 흐름은 `/plugin marketplace add YOUR_GITHUB_ID/agent-handoff-manager` 이후 정확한 marketplace name으로 `/plugin install <plugin>@<marketplace>`.
- **현재 marketplace 매니페스트 미포함:** 코어가 없으므로 잘못된 설치 가능한 플러그인을 공개하지 않기 위함.

## GitHub Copilot Plugin Marketplace

2026 GitHub Copilot은 자체 플러그인 및 Marketplace를 제공하지만 Claude plugin marketplace와 동일하지 않습니다. GitHub 문서 기준 Marketplace 카탈로그 위치는 `.github/plugin/marketplace.json`; 각 plugin 폴더의 source/manifest도 필요.

- Copilot CLI, VS Code, Copilot App에서 plugin이 제대로 동작하는지 따로 검증.
- 코드 완성 후 공식 marketplace starter template을 선택하거나 스키마에 맞춰 매니페스트 생성.
- Marketplace 등록이 **Agent Skills 설치의 필수조건이 아니며**, 발견·배포 채널로 활용.
- 공식: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/create-and-share-plugin-marketplaces
- 공식: https://docs.github.com/en/copilot/concepts/customizations/plugins

## GitHub `gh skill publish` 및 검색 노출

- GitHub CLI의 `gh skill publish --dry-run` 및 `gh skill publish` 사용 가능 (공개 preview; 릴리스 시 최신 문서 검토).
- 해당 명령을 실행하기 전에 실제 LICENSE, 저작권, 릴리스 태그, 데이터 보안, 실행 코어 포함 여부를 확인.
- `gh skill publish`의 동작이나 디렉터리/검색 노출을 검증하지 않고 자동 등록되었다고 주장하지 않음.
- 공식: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills

## Marketplace PR Exit Gate

- [ ] 설치 테스트: 비어있는 사용자 프로필에 신규 설치
- [ ] Remove/Uninstall 및 Upgrade/Rollback 테스트
- [ ] 각 플랫폼에서 skill id 중복/충돌 없음
- [ ] 플러그인 매니페스트 lint/스키마 검사
- [ ] 설치한 skill이 실제 core를 실행함 (단순 문서 발견만으로는 FAIL)
- [ ] 두 업스트림 및 본 프로젝트 LICENSE notices 확인
- [ ] 외부 공개 문서와 설치 명령이 테스트 로그로 검증됨
