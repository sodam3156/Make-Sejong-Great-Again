# Day 3 오프라인 이중 경로 완주 증거 — rc2

## 판정

같은 Windows x64 릴리스 ZIP의 압축 해제본에 대해 실제 API 경로와
fixture 폴백 경로를 각각 실제 3분 동안 완주했다. 두 캡처 모두
브라우저 외부 호스트 요청을 차단했고, 백엔드 health는
`rule_based_fallback`을 반환했다.

| 항목 | live API | fixture 폴백 |
|---|---|---|
| 증거 종류 | `day3_gate` | `fixture_fallback_gate` |
| 경과 시간 | 181.047초 | 181.125초 |
| run ID | `live-rain_spillback_a-s42-57ab9f71a5` | `fixture-qa-v2-001` |
| 상태 | 7개 의미 상태, 20/20 | 7개 의미 상태, 20/20 |
| 승인 | API 저장 후 `EVALUATED` | UI 로컬 승인, 승인 API 요청 0건 |
| 폴백 유도 | 해당 없음 | `POST /api/simulations` 503 1회 |
| 전체 assertion | 17/17 통과 | 20/20 통과 |
| 판정 | PASS | PASS |

## 릴리스 정렬

- 로컬 릴리스 태그: `v0.2.0-day3-rc2`
- 태그·ZIP source commit:
  `15bab0cd08d0a734b169f554f9776611992419d3`
- 모델 source-touch commit:
  `98ef5ec0394b72000cb931646041f839447f11f6`
- freeze ID: `freeze-20260730-191723-kst`
- freeze 시각: `2026-07-30T19:17:23+09:00`
- ZIP SHA-256:
  `44458b041bf6cbe5b392dd6ec68efb8f0d71088349423eb6b0c5b1668265ad42`
- live 증거 매니페스트 SHA-256:
  `5b27811391f2d350e394358c74a1520d6d27f39d2f90c1c24899f858e6a1eac1`
- fixture 증거 매니페스트 SHA-256:
  `d42bc6a95ec20a36f3d6e8667b22db64b0ceb6c5482ddeabd1ef177a243bca12`

ZIP 내부 `RELEASE-METADATA.json`의 `source_commit_sha`와
`release_tag_commit_sha`는 모두 위 태그 commit과 일치한다.

## 런처와 프로세스

빌드 게이트가 새 압축 해제본에서 다음 순서를 통과했다.

1. `start.bat`
2. `/api/health` HTTP 200, `status=ok`
3. `start.bat` 재실행
4. 같은 PID·port 유지, health 200
5. `stop.bat`
6. PID/port 파일 제거, health 불통

증거 캡처 뒤 독립 재확인에서도 PID `33528`, port `64752`가 재실행
전후 동일했고 종료 후 health 불통과 runtime 파일 제거를 확인했다.

런처 5개 `start.bat`, `launch.ps1`, `stop.bat`, `stop.ps1`,
`README.txt`가 ZIP 루트에 모두 존재한다.

## 네트워크·LLM 경계

- 브라우저 요청은 localhost/127.0.0.1만 허용했다.
- 실행 프로세스의 외부 목적지 established TCP 연결은 0건이었다.
- 알려진 AI 자격증명 환경변수 이름은 0개였다.
- health의 LLM 모드는 `rule_based_fallback`이었다.

이는 애플리케이션이 외부 네트워크나 LLM 없이 완주했다는 실행
증거다. 물리 네트워크 어댑터를 비활성화했다는 증거는 아니며,
그 조건은 외부 PC 수동 검증과 혼동하지 않는다.

## 증거 인덱스

- `day3_live_rc2_20260730/summary.json`: live 전체 판정
- `day3_live_rc2_20260730/run.json`: 승인 후 최종 API 결과
- `day3_live_rc2_20260730/audit.json`: 생성·승인 감사 이벤트
- `day3_live_rc2_20260730/screenshots/`: 7개 상태, 승인, 20/20
- `day3_fixture_rc2_20260730/summary.json`: fixture 전체 판정
- `day3_fixture_rc2_20260730/fixture-provenance.json`: 503 유도와
  정적 자산 SHA 대조
- `day3_fixture_rc2_20260730/screenshots/`: 폴백 로드, 7개 상태,
  로컬 승인, 20/20
- 각 폴더의 `localhost.har`, 요청·응답 로그, 콘솔·페이지 오류 로그
- 각 폴더의 `SHA256SUMS.txt`: 모든 파일 무결성 목록
- `day3_rc2_lifecycle_20260730.json`: 재실행·종료 판정
- `day3_rc2_process_network_20260730.json`: 프로세스 소켓·LLM 환경 판정

두 `SHA256SUMS.txt`는 GNU `sha256sum -c`로 전 항목 `OK`를 확인했다.

## 아직 완료로 표시하지 않는 항목

- clean Windows x64 외부 PC 2대 × 각 2회 수동 검증
- 독립 검토자의 provisional 파라미터 승인 또는 기각
- 원격 GitHub tag·Release 및 이슈 체크리스트 변경

위 세 항목은 실제 외부 장비, 독립 검토자, GitHub 쓰기 자격증명이
필요하므로 이 로컬 실행으로 대체하거나 완료로 주장하지 않는다.
