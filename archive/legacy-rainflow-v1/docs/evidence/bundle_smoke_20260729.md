# PyInstaller 번들 스모크 테스트 (2026-07-29)

7/31 게이트: PyInstaller onedir 실빌드 + 번들 스모크 테스트 결과.

## 빌드

- 명령: 저장소 루트에서 `powershell -ExecutionPolicy Bypass -File release\build_windows.ps1`
- 환경: Windows 11, Python 3.14.6, PyInstaller 6.21.0 (`pyinstaller-hooks-contrib` 2026.6)
- 결과: `release\windows-x64\RainFlow.exe` 생성 성공
- 번들 크기: 전체 `release\windows-x64\` 32MB, `RainFlow.exe` 6.6MB

### 빌드 중 발견 및 수정한 문제

`release/rainflow_entry.py`는 `from backend.app.main import app`을 함수 내부에서
지연 임포트한다. 원래 `build_windows.ps1`은 PyInstaller에 `--paths` 없이 실행돼서,
저장소 루트가 모듈 탐색 경로에 없어 PyInstaller 정적 분석이 `backend` 패키지를
찾지 못했다 (`warn-RainFlow.txt`: `missing module named backend ... (delayed)`).
그 결과 최초 빌드 산출물은 `backend/app/*.py` 소스 자체가 통째로 빠졌고, 실행 시
`ModuleNotFoundError: No module named 'backend.app'`로 즉시 죽었다.

수정: `release/build_windows.ps1`의 pyinstaller 호출에 `--paths .` 추가.
저장소 루트가 탐색 경로에 들어가면서 PyInstaller가 `backend.app.main`을 정적으로
해석해 `backend/app/*.py`뿐 아니라 그 안에서 임포트하는 `fastapi`, `starlette`,
`pydantic`, `uvicorn` 등도 자동으로 함께 수집한다. 수정 후 `warn-RainFlow.txt`에
`backend`/`fastapi` 관련 missing module 경고가 사라졌고 정상 기동을 확인했다.

## 스모크 테스트 (저장소 밖 한글·공백 경로)

- 번들 복사 위치: `C:\Users\USER\AppData\Local\Temp\claude\한글 공백 테스트\windows-x64\`
  (저장소 밖, 경로에 한글과 공백 포함 조건 재현)
- 실행 명령: `RainFlow.exe 8951` (포트 인자 지정)

### 1) 최초 실행 및 API 확인

```
RainFlow.exe 8951
INFO:     Uvicorn running on http://127.0.0.1:8951 (Press CTRL+C to quit)
```

| 요청 | 응답 코드 | 비고 |
|---|---|---|
| `GET /api/health` | 200 | `{"status":"ok","version":"0.1.0","fixture_available":true,"llm":"unavailable","runs_in_memory":0}` |
| `GET /` | 200 | `frontend/index.html` 정적 서빙 확인 |
| `POST /api/simulations` `{"scenario_id":"rain_spillback_a","seed":42}` | 200 | `{"run_id":"live-rain_spillback_a-s42","status":"completed","result_source":"live_simulation", ...}` — `result_source`가 `live_simulation`으로 fixture 폴백이 아닌 실계산 경로임을 확인 |

### 2) 종료 후 재실행 (포트 충돌 확인)

- 첫 프로세스를 `taskkill /F /IM RainFlow.exe`로 종료
- 동일 포트(8951)로 재실행 → 정상 기동, 포트 바인딩 충돌 없음
- 재실행 후 `GET /api/health` → 200 재확인
- 두 번째 프로세스 종료

```
INFO:     Started server process [33924]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8951 (Press CTRL+C to quit)
GET /api/health -> HTTP 200
```

### 3) fixture 폴백 자원 포함 확인

- 번들 내부 경로 확인: `release\windows-x64\_internal\backend\fixtures\demo_run.json` 존재
- `GET /api/health` 응답의 `fixture_available: true`로 실행 시점에도 접근 가능함을 재확인

## 결론

4개 스모크 항목(health 200 / root 200 / simulations live_simulation 200 /
재실행 무충돌) 전부 통과. fixture 폴백 파일도 번들에 정상 포함됨.
`--paths .` 수정 없이는 exe가 기동조차 하지 못했으므로, 이 수정은
`release/build_windows.ps1`에 반드시 반영되어야 한다.
