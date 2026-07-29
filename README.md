# Make Sejong Great Again

> **센서는 이미 있다. 이제 도시가 판단하게 만들 차례다.**

**RainFlow Sejong**은 합성 세종형 연속 회전교차로 회랑에서 우천으로 인한 진입용량 저하와 spillback을 재현하고, 세 가지 대응 정책을 비교한 뒤 결정론적 안전·공정성 가드와 운영자 승인을 거치는 오프라인 디지털 트윈 프로토타입입니다.

이 프로젝트는 실제 세종 도로 또는 신호기를 제어한다고 주장하지 않습니다. **상태 재현 → 정책 비교 → 안전검사 → 규칙 기반 설명과 순위화 → 운영자 승인 → 결과 기록** 흐름을 합성 데이터로 시연합니다.

## 한 문장 문제 정의

> 건조 상태에서 처리되던 연속 회전교차로 회랑도 우천으로 진입용량이 수요 아래로 떨어지면 짧은 연결도로의 대기행렬이 상류까지 역류할 수 있으므로, 운영자가 무대응과 복구 정책의 효과·부작용·안전 근거를 같은 조건에서 비교할 수 있어야 한다.

## 우리가 만드는 것

- 합성 회전교차로 3개(`R1 → R2 → R3`)와 평행 우회로 `BYPASS`
- 건조·우천·사고 조건에서 같은 입력과 seed로 재현되는 결정론적 큐 시뮬레이터
- `no_action`, `fixed_metering`, `corridor_gating` 세 정책의 KPI 비교
- 진입로 P95 지체, 우회 전가 지체, 안전 대리지표, 데이터 신선도와 장비 상태를 검사하는 결정론적 가드
- 외부 LLM 없이도 동일하게 동작하는 규칙 기반 정책 순위·근거·위험 설명
- 운영자 승인 직전 후보 해시·규칙 버전·데이터 품질 재검사
- 실행 JSON과 JSONL 감사 로그, cached/fixture 폴백, 3분 정적 데모

## 해커톤 MVP

실데이터 연동이 없더라도 재현 가능한 합성 시뮬레이션 데이터로 다음 장면을 3분 안에 보여줍니다.

1. 건조 상태에서 세 회전교차로가 정상 처리된다.
2. 강우로 하류 진입용량이 감소하고 연결도로 spillback이 상류로 전파된다.
3. 동일한 수요와 seed에서 세 정책을 실행한다.
4. 네 가지 동결 KPI와 정책별 부작용을 비교한다.
5. 안전·공정성 가드가 위험 후보를 탈락시킨다.
6. 규칙 기반 결정 계층이 통과 후보를 순위화하고 운영자가 승인·거절·보류한다.
7. 승인 결과, 적용 전후 KPI, 입력·버전·후보 해시를 저장하고 다시 조회한다.

화면의 개선율은 실제 세종시 성과가 아니라 동일한 합성 수요와 고정 난수 시드에서 계산된 데모용 시뮬레이션 결과로 표시합니다.

`result_source=live_simulation`은 요청 시점에 합성 큐 모델을 계산했다는 뜻이며 실시간 세종 데이터를 사용했다는 뜻이 아닙니다. 현재 허용 데이터셋은 `synthetic-v0` 하나뿐입니다.

### 7월 28일 동결 계약

`docs/15_DAY1_FREEZE_DECISION.md`에 따라 RainFlow Sejong 단일 제출안과 다음 계약을 사용합니다.

| 구분 | 동결 값 |
|---|---|
| 시나리오 3종 | `dry_base`, `rain_spillback_a`, `rain_spillback_b` |
| 정책 3종 | `no_action`, `fixed_metering`, `corridor_gating` |
| KPI 4종 | `spillback_time_sec`, `recovery_time_sec`, `total_travel_time_sec`, `worst_approach_delay_sec` |
| API 4경로 | `GET /api/health`, `POST /api/simulations`, `GET /api/simulations/{run_id}`, `POST /api/approvals` |
| 결과 출처 | `live_simulation`, `cached_simulation`, `fixture` |
| 기본 데이터셋 | `synthetic-v0` (실자료 어댑터 미설치) |

프론트와 백엔드의 결과 계약 정본은 `contracts/rainflow.schema.json`과 `backend/fixtures/demo_run.json`입니다. `docs/12_TECH_STACK_AND_BACKEND_SCOPE.md`의 합성 5개 신호교차로 core MVP는 기술 원칙을 참고하기 위한 레거시 설계이며 제출 범위가 아닙니다.

## RainFlow Sejong 8월 2일 제출 체제

![RainFlow Sejong 6일 압축 제작 로드맵](docs/assets/rainflow-6day-roadmap.png)

실질적인 개발 마감은 8월 1일 밤이다. 8월 2일은 새 Windows x64 컴퓨터에서 실행 검증과 제출만 수행한다.

| 날짜 | 준 · PM·UX | 최영 · AI·백엔드 | 시우 · 근거·KPI | 프론트엔드 | 디자인 | 야간 게이트 |
|---|---|---|---|---|---|---|
| 7월 28일 | 3분 흐름, 화면 ID, 와이어프레임, 문구 동결 | 상태 스키마, OpenAPI, fixtures, 백엔드 골격 | provisional 시나리오와 KPI 기준 | fixtures 기반 전체 라우팅과 상태 저장소 | 토큰, 상태 아이콘, 에셋 규격 | 계약 동결, 가짜 데이터로 처음부터 끝까지 완주 |
| 7월 29일 | 모든 버튼과 상태 인수 기준 확정 | 건조·우천·spillback·정책 비교를 API에서 단독 실행 | 근거·가정 분리, 공정성 규칙, QA 케이스 | 정상·경고·마비·후보·승인·결과 화면 완성 | 핵심 에셋 1차 완료 | 백엔드와 프론트가 각각 독립 완주 |
| 7월 30일 | 실제 연동 UX 검수와 기능 삭제 | 실제 결과 한 경로 연결, 안전 가드와 폴백 | 결과 수치와 문구 대조 | API 어댑터 연결, 실패 시 fixtures 자동 전환 | 핵심 장면 에셋 교체 | 네트워크와 LLM 없이 실제 연동 1회 완주 |
| 7월 31일 | 3분 대사와 화면 타이밍 고정 | PyInstaller 실행 번들, 로그, health check | 제출 수치 1차 동결 | 정적 빌드와 백엔드에 포함, 오류 화면 완성 | 발표 시각물과 누락 에셋 완료 | Windows x64 압축본에서 start.bat 실행 성공 |
| 8월 1일 | 기능 동결과 최종 승인 | 치명적 버그만 수정, 릴리스 체크섬 생성 | 전체 팩트체크와 실행 매뉴얼 검증 | 치명적 UI 오류만 수정 | 발표물 최종본 | 초기화된 외부 PC 두 대에서 각각 두 번 연속 성공 |
| 8월 2일 | 제출 총괄과 현장 시연 | 실행 지원과 로그 확인 | 제출 파일 대조 | 대기 | 대기 | 코드 추가 금지, 압축본·소스·영상·문서 제출 |

### 외부 컴퓨터 실행 계약

제출 심사본은 Windows x64 압축파일을 푼 뒤 `start.bat` 한 번으로 로컬 서버와 브라우저가 실행되어야 한다. Node, Python, SUMO, API 키, 인터넷 연결을 요구하지 않는다. 프론트 정적 빌드와 FastAPI 백엔드를 하나의 실행파일에 포함하고, 교통 결과는 사전 계산 fixtures를 기본값으로 사용한다. 개발 재현 경로는 `docker compose up --build`로 별도 제공한다.

외부 PC 통과 기준은 `start.bat` 실행 후 60초 이내 화면 표시, 정상에서 복구 결과까지 3분 흐름 완주, 재실행 시 포트 충돌 없음, 한글 경로와 공백 경로에서 실행, 인터넷 차단 상태 동작, LLM·SUMO 미설치 상태 동작이다.

현재 작업트리에는 Windows Python 3.11로 빌드한 `release/windows-x64/RainFlowSejong.exe`, `start.bat`, `stop.bat`, `SHA256SUMS.txt`와 `release/RainFlowSejong-windows-x64.zip`이 있다. 현재 한글·공백 경로와 ZIP 재압축 해제 경로에서 health check, 7단계 API, 재실행 서버 재사용, 종료를 확인했다. 초기화된 외부 Windows x64 PC 두 대의 인터넷 차단 반복 검증은 남아 있다.

소스·fixture가 바뀐 PR을 병합한 뒤에는 기존 ZIP을 최종 제출본으로 재사용하지 않는다. Windows에서 다시 빌드하고 smoke gate·SHA-256을 갱신한 뒤 외부 PC 검증을 반복한다.

### 예상 시뮬레이션 전개

![RainFlow Sejong 예상 시뮬레이션 전개도](docs/assets/rainflow-simulation-storyboard.png)

## 핵심 문서

| 문서 | 용도 |
|---|---|
| [AI 구현 컨텍스트](ai-context/PROJECT_STACK.yaml) | AI 코딩 도구가 먼저 읽는 고정 스택, API, 디렉터리, 금지사항과 P0 완료 조건 |
| [프로젝트 전체 맥락](docs/00_PROJECT_CONTEXT.md) | 아이디어가 나온 배경과 현재 결론 |
| [문제 정의와 근거](docs/01_PROBLEM_AND_EVIDENCE.md) | 세종 ITS 현황, 문제 구조, 팩트·가설 구분 |
| [제품 정의](docs/02_PRODUCT_DEFINITION.md) | 고객, 가치제안, 사용자 흐름, 차별점 |
| [MVP 범위와 시연](docs/03_MVP_AND_DEMO.md) | 구현 범위, 데모 시나리오, 성공 기준 |
| [기술 구조](docs/04_TECHNICAL_ARCHITECTURE.md) | 데이터·AI·안전·승인·시뮬레이션 설계 |
| [실행 계획](docs/05_EXECUTION_PLAN.md) | 역할, 일정, 의사결정 원칙 |
| [발표 서사](docs/06_PITCH_STORY.md) | 3분 피치와 예상 질문 |
| [개발 백로그](docs/07_BACKLOG.md) | GitHub Issue로 옮길 작업 목록 |
| [출처 목록](docs/08_SOURCES.md) | 근거 링크와 사용 시 주의사항 |
| [RainFlow Sejong](docs/09_RAINFLOW_SEJONG.md) | 우천 연속 회전교차로 디지털 트윈 설계와 검증 기준 |
| [병렬 제작 운영과 최영 작업 명세](docs/10_TEAM_PARALLEL_EXECUTION.md) | 8월 2일 제출을 위한 역할, 병렬 계약, 날짜별 납품과 외부 실행 기준 |
| [프로젝트 실현 가능성 검증 보고서](docs/11_PROJECT_FEASIBILITY_VALIDATION.md) | 구현 가능 범위, 과장 방지 기준, 기술 구조 충돌, 필수 테스트와 발표 전 체크리스트 |
| [기술 스택과 백엔드 구현 범위](docs/12_TECH_STACK_AND_BACKEND_SCOPE.md) | 제출 범위에서 제외된 5개 신호교차로 core MVP의 레거시 참조 설계 |
| [PM 진척 체크 로그](docs/14_PM_STATUS_LOG.md) | 2시간 주기 진척 확인, 리스크, 담당자별 다음 작업 추천 |
| [데이터 필요조건·투입·롤백 기준](docs/evidence/rainflow_data_requirements.md) | 합성 데모·실제 회랑 보정·현장 연동 자료를 구분하고 안전한 전환·복귀 절차를 규정 |

## 프로젝트 원칙

- 안전이 최적화보다 우선한다.
- 정책은 동결된 코드가 실행하고 KPI는 시뮬레이터가 계산하며, 안전 판정과 정책 순위는 버전이 고정된 결정론적 코드가 담당한다.
- 외부 LLM은 핵심 실행 경로에 없으며 KPI 계산, 안전 판정 또는 최종 승인을 맡지 않는다.
- 최종 적용 상태 전이는 운영자 승인 없이는 진행되지 않는다.
- 실제 데이터, 의원 발언, 정부 사업 소개, 기업 자료, 팀 추론, 검증 가설, 시뮬레이션 결과를 구분한다.
- 346개 교차로와 366대 제어기 수치는 집계 단위와 시점이 다를 수 있으므로 합치지 않는다.
- 실제 세종 데이터 접근, 실제 제어기 연동, 현장 안전성 및 개선 효과를 구현 완료로 주장하지 않는다.
- 해커톤에서는 합성 데이터 기반 디지털트윈형 프로토타입과 승인 워크플로를 시연한다.

## 현재 상태

현재 공유 작업트리 기준으로 다음 항목이 구현되어 있습니다.

- RainFlow 결과 스키마와 7단계 완결 fixture
- Pydantic 입출력 모델과 동결 API 4경로
- 3개 시나리오·3개 정책·4개 KPI의 결정론적 큐 시뮬레이터
- 버전이 기록되는 정책, 안전·공정성 가드, 승인 직전 재검사
- 외부 LLM 없는 결정론적 정책 순위와 구조화된 근거·위험·사유
- JSON 실행 저장, JSONL 감사 로그, 실행 재조회
- `live_simulation` 실패 시 cached/fixture 경로로 전환하는 폴백 코드
- `synthetic-v0` 기본 데이터셋 경계, 미설치 dataset 거절, 시나리오가 다른 저장 결과의 폴백 차단
- 실제 계산에서 동결하고 스키마 검증한 `cached_run.json`
- live/cached/fixture API 어댑터와 오프라인 폴백을 갖춘 7단계 정적 프론트
- A·B 각각 seed 1~10의 KPI 분포·가드 실패·미회복 seed 검증자료
- Docker 개발 실행 경로와 Windows x64 PyInstaller 실행본·ZIP·SHA256 체크섬
- 백엔드 테스트 75건 통과

남은 제출 작업은 다음과 같습니다.

- Docker Desktop 실행 후 실제 이미지 빌드 검증
- 이 변경 병합 뒤 Windows 실행본·ZIP 재빌드와 SHA-256 재동결
- 인터넷 차단 조건의 초기화된 외부 Windows x64 PC 2대 반복 검증
- 검증된 수치·실행 로그·README·영상·발표 자료의 최종 버전 일치 확인
