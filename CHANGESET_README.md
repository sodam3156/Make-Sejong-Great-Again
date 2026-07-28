# 최영 변경파일 전달 패키지

- 기준 저장소: `sodam3156/Make-Sejong-Great-Again`
- 기준 커밋: `20de26c90c3ece5b4ed174d50f487f8181c5d62c`
- 생성 시각: `2026-07-29T01:08:24+09:00`
- 포함 파일: 수정·추가 파일 38개

## 적용 방법

이 ZIP의 `Make-Sejong-Great-Again/` 폴더 내용을 같은 저장소 루트에 덮어쓰면 됩니다. 기존 사용자 파일을 보존하려면 적용 전에 별도 브랜치나 백업을 만드세요.

- `CHANGED_FILES_MANIFEST.txt`: 파일별 상태, 크기, SHA256
- `TRACKED_CHANGES.patch`: 기존 추적 파일 수정분의 Git 패치
- `GIT_STATUS.txt`: 패키징 당시 작업트리 상태
- 새 파일은 패치가 아니라 실제 파일 전체로 포함됩니다.

## 제외 항목

가상환경, 빌드 캐시, 실행 로그, `.git`, `build/`, `dist/`, PyInstaller 내부 파일과 이미 별도 생성된 Windows 실행 ZIP은 제외했습니다. Notion API 토큰은 포함하거나 저장하지 않았습니다.

## 검증

저장소 루트에서 다음을 실행합니다.

```bash
python -m pytest backend/tests -q
python scripts/generate_contract_artifacts.py --check
```
