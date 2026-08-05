# 제출 패키징 검증 (2026-07-29)

노션 제출 계약(즉시 실행 zip / start.bat / RainFlow.exe / README_RUN.md / source.zip
또는 GitHub 태그 / SHA256SUMS.txt)에 맞춰 `release/package_release.ps1`을 작성하고
실제 실행으로 검증했다.

## 실행 명령

```
powershell -ExecutionPolicy Bypass -File release\package_release.ps1
# 기본 -Version "v0.1.0-day2"
```

환경: Windows 11, Python 3.14.6, PyInstaller 6.21.0. (`pip install pyinstaller`가
설치하는 `pyinstaller.exe`가 `%APPDATA%\Python\Python314\Scripts`에 생성되는데 이
경로가 PATH에 없으면 `build_windows.ps1`의 `pyinstaller` 호출이 실패한다. 해당
경로가 PATH에 있는 셸에서 실행해야 한다. 스크립트 자체는 수정하지 않음 — 개발 PC
환경 설정 문제이며 `pip install pyinstaller` 직후 통상적으로 PATH에 잡힌다.)

## 스크립트가 만든 산출물

`release/out/`:

| 파일 | 크기 | SHA256 |
|---|---|---|
| `RainFlow-demo-windows-x64-v0.1.0-day2.zip` | 16,805,454 bytes (약 16.0MB) | `c7d42df5e03e4cd01858c9ca474b5e272609665375d1463e7db633768df6f71c` |
| `source-v0.1.0-day2.zip` | 1,681,298 bytes (약 1.6MB) | `daac9a6f86fd3c1f56403999c98652f8c0d3e4af4f5141b734e45ec94d76358d` |

`SHA256SUMS.txt` 내용:

```
c7d42df5e03e4cd01858c9ca474b5e272609665375d1463e7db633768df6f71c  RainFlow-demo-windows-x64-v0.1.0-day2.zip
daac9a6f86fd3c1f56403999c98652f8c0d3e4af4f5141b734e45ec94d76358d  source-v0.1.0-day2.zip
```

데모 zip 안에는 `RainFlow.exe`, `start_exe.bat`, `README_RUN.md`, PyInstaller
`_internal/` 런타임 자원이 들어있다. 소스 zip은 `git archive HEAD` 스냅샷이다.

## 스크립트 실행 로그 요약 (6단계)

1. `build_windows.ps1` 호출 → `release\windows-x64\RainFlow.exe` fresh 빌드 성공
2. `README_RUN.md`, `start_exe.bat`을 `windows-x64\`에 복사
3. `Compress-Archive`로 데모 zip 생성
4. `git archive --format=zip -o release/out/source-<Version>.zip HEAD`로 소스 zip 생성
5. 두 zip의 `Get-FileHash -Algorithm SHA256`을 `SHA256SUMS.txt`에 기록
   (Windows PowerShell 5.1은 `Set-Content -Encoding utf8NoBOM`을 지원하지 않아
   `[System.IO.File]::WriteAllLines` + `UTF8Encoding($false)`로 BOM 없는 UTF-8을
   직접 기록하도록 스크립트를 조정함)
6. 데모 zip을 임시 폴더에 풀어 `RainFlow.exe` / `start_exe.bat` / `README_RUN.md`
   존재를 확인 — 통과

```
[6/6] 데모 zip 압축 해제 검증
검증 통과: RainFlow.exe, start_exe.bat, README_RUN.md 모두 존재

===== 패키징 완료 =====
```

## start_exe.bat 실행 검증 (별도 압축 해제 폴더에서)

데모 zip을 저장소 밖 임시 폴더에 풀고 `start_exe.bat`을 실제로 실행해 확인했다.

### 발견 및 수정한 버그: LF 줄바꿈이 cmd 배치 파서를 깨뜨림

최초 작성한 `release/start_exe.bat`은 Write 도구가 LF(`\n`)만으로 저장했다.
기존 `release/start.bat`(CRLF)과 비교해보니, 같은 구조(한글 REM 주석 +
`chcp 65001` + `:try_port` 레이블을 `call`로 재진입 + `for /l` 루프)임에도
LF 전용 파일에서만 실행 중간에 파서가 깨졌다:

```
'ER_PID' is not recognized as an internal or external command, ...
'IS_RAINFLOW' is not recognized as an internal or external command, ...
do was unexpected at this time.
```

원인: cmd.exe 배치 인터프리터는 CRLF를 전제로 라인/블록을 버퍼링하며, LF 전용
파일 + UTF-8 다국어(한글) 텍스트 조합에서 `call`로 재진입하는 레이블 블록을
잘못 토큰화한다. `start.bat`(CRLF, 정상 동작 확인됨)과 동일한 내용을 LF로만
바꿔도 같은 증상이 재현됨을 별도 테스트로 확인했다.

수정: `start_exe.bat`을 CRLF로 재저장(`\n` → `\r\n` 정규화, BOM 없는 UTF-8
유지). 또한 `start "..." /min "%EXE_PATH%" %PORT% >> log 2>&1`처럼 `start`
명령에 직접 리다이렉션을 거는 방식도 `start.bat`에 없는 패턴이라 함께
제거하고, `start.bat`이 쓰는 것과 동일한 "러너 배치파일 생성 후 그 배치를
`start`로 실행" 패턴(`%RUNNER%`)으로 맞췄다.

### 수정 후 실행 로그

압축 해제 폴더에서 `start_exe.bat` 실행 → `logs\start_bat_events.log`:

```
[2026-07-29  3:35:03.79] start_exe.bat 실행 시작
[2026-07-29  3:35:03.91] PORT=8000
[2026-07-29  3:35:05.60] 서버 준비 완료 (포트 8000)
```

health 재확인 (`Invoke-WebRequest http://127.0.0.1:8000/api/health`):

```
STATUS: 200
BODY: {"status":"ok","version":"0.1.0","fixture_available":true,"llm":"unavailable","runs_in_memory":1}
```

이후 `RainFlow.exe` 프로세스를 `Stop-Process -Force`로 종료해 정리했다.
브라우저 자동 오픈(`start "" "http://127.0.0.1:%PORT%"`) 단계는 무해하므로
별도 검증하지 않음.

## 결론

`release/package_release.ps1` 실행 → zip 2개 + `SHA256SUMS.txt` 생성 → 압축
해제 검증 → `start_exe.bat` 실행 → health 200 확인 → 프로세스 종료까지 전 과정
통과. `start_exe.bat`의 LF/CRLF 버그는 이번 검증 과정에서 발견해 수정했고,
수정하지 않았다면 실제 심사 PC에서 배치파일이 깨진 채로 배포될 뻔했다.
