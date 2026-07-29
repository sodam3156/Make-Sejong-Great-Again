# PyInstaller 번들 리그레션 (백엔드 확장 후, 2026-07-29)

`feat/backend`에 `origin/main`을 병합한 뒤 (최영 측 백엔드 확장 반영), 기존에
검증된 PyInstaller 번들 경로(`release/build_windows.ps1`, PR #17·#18)가 여전히
동작하는지 리그레션한 결과.

## 1. 백엔드 변경 규모 (병합으로 유입된 내용)

`git merge origin/main --no-edit` (fast-forward, 5892b9f → 6e56397), 관련 백엔드 diff:

- `backend/app/main.py`: +962줄
- 신규 모듈: `backend/app/decision.py` (+208), `backend/app/domain.py` (+197),
  `backend/app/storage.py` (+74), `backend/app/policies.py` (+49)
- `backend/app/safety.py`, `backend/app/simulation.py` 수정
- 신규 픽스처: `backend/fixtures/cached_run.json` (+983)
- 신규 테스트: `test_backend_contract_regressions.py`, `test_decision.py`,
  `test_generated_artifacts.py`

## 2. 저장소 상태 확인

```
python -m pytest backend/tests -q
```

결과: **42 passed** (예상치와 일치), 경고 1건 (`httpx` deprecation, 무관).

## 3. 빌드

- 환경: Windows 11, `requirements.txt`가 명시하는 `>=3.11,<3.13` 계약에 맞춰
  Python 3.11.15 (uv 배포판)로 별도 venv를 만들어 빌드 (시스템 기본
  `python`이 3.14라 계약 범위 밖이라 그대로 쓰지 않음). PyInstaller 6.21.0.
- 명령: `powershell -ExecutionPolicy Bypass -File release\build_windows.ps1`
  (PATH 앞에 위 venv의 Scripts를 넣어 pip/pyinstaller가 3.11을 쓰도록 함)
- 결과: **빌드 성공**, `release\windows-x64\RainFlow.exe` 생성됨
- `warn-RainFlow.txt` 확인: `missing module named backend.*` 경고 없음
  (`backend.app.domain` 관련 `pydantic.BaseModel` 항목은 pydantic 표준
  패턴에서 나오는 무해한 오탐이고 실제 backend 서브모듈 누락이 아님)
- 번들 산출물에 신규 픽스처 포함 확인: `_internal/backend/fixtures/cached_run.json`,
  `_internal/backend/fixtures/demo_run.json` 존재
- `storage.py`는 SQLite가 아니라 평문 JSON 파일(`backend/logs/runs/*.json`,
  `audit.jsonl`) 기반이라 DB 경로 문제는 발생하지 않음

**수정 사항: 없음.** 기존 `--paths .` 플래그(PR #17/#18에서 반영됨)만으로
새 서브모듈(`decision`, `domain`, `policies`, `storage`)도 PyInstaller 정적
분석에 자동으로 포함됐다. `release/build_windows.ps1`, `release/rainflow_entry.py`
둘 다 변경 불필요.

## 4. 스모크 (저장소 밖 한글·공백 경로, 포트 8961)

경로: `C:\Users\USER\AppData\Local\Temp\claude\스모크 테스트 폴더\RainFlow\`

| 항목 | 결과 |
|---|---|
| `GET /api/health` | 200, `{"status":"ok","version":"0.2.0","fixture_available":true,"cached_fixture_available":true,...}` |
| `POST /api/simulations` `{"scenario_id":"rain_spillback_a","seed":42}` | 200, `result_source: live_simulation` (run_id `live-rain_spillback_a-s42-ed95c7ae49`) |
| 신규 필드 확인 (`GET /api/simulations/{run_id}`) | `decision.recommended_policy_id = "corridor_gating"` 존재, `policies[].candidate_hash` 3건 모두 존재 (예: `5eedf9a7...e560e0af2`) |
| `POST /api/approvals` corridor_gating approve | 200, `{"status":"approved","policy_id":"corridor_gating",...,"workflow_state":"EVALUATED"}` |
| `POST /api/approvals` fixed_metering approve | **409**, `{"detail":{"code":"INVALID_STATE_TRANSITION",...}}` — 이미 승인 완료된 실행은 다른 정책으로 전이 불가 (기대 동작) |
| 종료 후 재실행 (동일 포트 8961) | 정상 기동, 포트 충돌 없음. `GET /api/health` 재확인 200, `persisted_runs:1`로 승인된 run이 디스크에 정상 영속화됐음도 확인 |

모든 항목 통과. 정리: 스모크용 임시 폴더, 빌드 산출물(`build/`, `dist/`,
`RainFlow.spec`, 빌드용 venv) 삭제 완료.

## 결론

백엔드가 대폭 확장됐지만(main.py +962줄, 신규 모듈 4개) 기존 PyInstaller 번들
경로(`release/build_windows.ps1`)는 코드 수정 없이 그대로 동작한다. PR #17/#18에서
넣은 `--paths .`가 신규 서브모듈까지 커버하고, storage가 SQLite가 아닌 JSON 파일
기반이라 번들 내 DB 경로 문제도 없다. `scripts/build_windows.ps1` /
`launcher/run_rainflow.py` 경로는 이번 리그레션 대상이 아니며 별도로 검증 필요.
