# 기술 스택과 백엔드 구현 범위

문서 기준일은 2026년 7월 28일이다. 이 문서는 합성 데이터 기반 5개 교차로 교통운영 오케스트레이터 MVP의 고정 기술 선택과 백엔드 구현 범위를 정의한다.

AI 코딩 도구는 먼저 `ai-context/PROJECT_STACK.yaml`을 읽고 이 문서를 보조 설명으로 사용한다. 기술 선택이 기존 문서와 충돌하면 구현 스택은 `ai-context/PROJECT_STACK.yaml`, 사실 주장과 안전 한계는 `docs/11_PROJECT_FEASIBILITY_VALIDATION.md`를 우선한다.

`docs/09_RAINFLOW_SEJONG.md`와 `docs/10_TEAM_PARALLEL_EXECUTION.md`의 RainFlow Sejong은 별도 변형안이다. RainFlow의 시나리오 ID와 KPI 이름을 본 5개 교차로 MVP에 자동으로 혼합하지 않는다.

## 1. 현재 저장소 상태

현재 저장소 검색에서는 FastAPI 실행 코드나 `backend/app` 구현이 확인되지 않았다. 따라서 아래 기능은 현재 완성된 코드가 아니라 지금부터 백엔드 파트에서 구현 가능한 P0 범위다.

현재 완료된 것은 문제 정의, 제품 범위, 기술 구조, 백로그, 실행 계획, 실현 가능성 검증과 같은 문서 설계다.

현재 미완료된 것은 교통 시뮬레이터, KPI 엔진, 후보 생성기, 안전 가드, AI 검토 모듈, 상태 전이, 승인 API, 감사 로그와 Windows 실행 번들이다.

## 2. 고정 기술 스택

### 프론트엔드

| 항목 | 선택 | 목적 |
|---|---|---|
| 언어 | TypeScript | 데이터 계약 오류 감소 |
| UI | React | 관제 화면과 승인 흐름 구현 |
| 빌드 | Vite | 빠른 정적 빌드와 단순 패키징 |
| 상태 관리 | Zustand 또는 React Context 중 하나 | 시나리오와 실행 상태 관리 |
| 교차로 시각화 | 자체 SVG | 외부 지도 없이 5개 교차로와 정체 전파 표시 |
| KPI 차트 | Recharts | 기준안과 후보안 비교 |
| 요청 | REST | 실행, 조회, 승인, 평가 |
| 재생 | Server-Sent Events | 시뮬레이션 타임라인 스트리밍 |

P0에서는 지도 타일 API, 외부 CDN과 모바일 중심 화면을 사용하지 않는다.

### 백엔드

| 항목 | 선택 | 목적 |
|---|---|---|
| 언어 | Python 3.11 이상 3.13 미만 | 시뮬레이션, 규칙, API의 단일 언어화 |
| API | FastAPI | REST, SSE, OpenAPI 제공 |
| 스키마 | Pydantic v2 | 입력과 출력 구조 검증 |
| 서버 | Uvicorn | 로컬 ASGI 실행 |
| 데이터베이스 | SQLite | 승인과 실행 로그 저장 |
| 저장 계층 | SQLAlchemy 2 저장소 계층 | API와 DB 로직 분리 |
| 로그 | JSON 구조화 로그 | 실행 재현과 오류 추적 |
| 설정 | pydantic-settings | 개발 설정 관리 |

제출 실행본에서는 Python 설치를 요구하지 않는다. PyInstaller가 백엔드 런타임을 실행파일에 포함한다.

### 교통 시뮬레이션

| 항목 | 선택 | 목적 |
|---|---|---|
| 엔진 | 자체 결정론적 큐 기반 시뮬레이터 | 짧은 일정과 오프라인 실행 보장 |
| 네트워크 | 방향 그래프 | 5개 교차로와 링크 연결 표현 |
| 수요 | 고정 도착 trace와 seed | 동일 조건 재현 |
| 정체 전파 | 상류 방출량을 하류 도착량에 연결 | 교차로 간 영향 구현 |
| spillback | 링크 저장용량 초과 시 상류 진입 차단 | 실제 정체 전파의 핵심 현상 구현 |
| 보행 | 보행 호출과 대기시간 상태 | 보행 안전 KPI 계산 |

SUMO는 후속 확장 기술이며 P0 실행 경로에 포함하지 않는다.

### 후보 생성과 최적화

후보 생성은 LLM이 아니라 제한된 조합 탐색 코드가 담당한다.

기준 TOD를 중심으로 녹색시간 분할, 주기와 오프셋을 허용 범위 내에서 조정한다. 생성된 조합을 시뮬레이터로 평가하고 상위 후보를 선택한다.

후보 A는 큰 지체 개선을 보이지만 정해진 안전 위반 fixture를 재현하는 교육용 위험안이다.

후보 B는 안전 규칙을 지키는 최적화안이다.

후보 C는 기준 TOD와 가까운 보수적 복구안이다.

강화학습, 블랙박스 최적화와 LLM이 자유롭게 생성한 신호안은 P0에서 제외한다.

### AI 기술

| 기능 | AI의 역할 |
|---|---|
| 상황 요약 | 구조화된 교통 상태를 운영자 문장으로 변환 |
| 교통 흐름 검토 | 지체, 대기행렬, spillback 부작용 검토 |
| 보행 안전 검토 | 보행 대기와 변경안의 운영상 주의점 설명 |
| 긴급 대응 검토 | 긴급 상황에서 후보안의 대응성 설명 |
| 장비 및 데이터 신뢰도 검토 | 지연, 결측, 장비 이상에 따른 신뢰도 설명 |
| 운영자 설명 | 후보 생성 이유, 장점, 위험과 승인 고려사항 생성 |

AI 출력은 Pydantic 스키마로 검증되는 JSON이어야 한다. 공급자별 API 코드는 `LLMClient` 어댑터 뒤에 둔다.

실시간 LLM이 실패하면 저장된 검토 JSON 또는 규칙 기반 설명을 동일한 응답 스키마로 반환한다.

AI는 KPI 수치를 생성하지 않는다. AI는 신호 후보를 자유롭게 만들지 않는다. AI는 안전 통과 여부를 결정하지 않는다.

P0에서는 LangChain, CrewAI, 벡터 데이터베이스와 자율 도구 실행 에이전트를 사용하지 않는다. 네 가지 관점의 구조화된 검토가 필요할 뿐 복잡한 에이전트 프레임워크는 필요하지 않다.

### 안전 기술

안전 판정은 버전이 고정된 Python 규칙 엔진이 담당한다.

필수 규칙 코드는 다음과 같다.

| 코드 | 검사 |
|---|---|
| PED_MIN_TIME | 보행 최소시간 |
| GREEN_MIN | 최소 녹색시간 |
| GREEN_MAX | 최대 녹색시간 |
| YELLOW_MIN | 황색시간 |
| ALL_RED_MIN | 전적색시간 |
| CONFLICT_PHASE | 상충 이동류 동시 허용 |
| PHASE_SEQUENCE | 허용되지 않은 현시 전환 |
| CYCLE_SUM | 주기 합계 불일치 |
| SPLIT_CHANGE_LIMIT | 분할 변경폭 초과 |
| OFFSET_CHANGE_LIMIT | 오프셋 변경폭 초과 |
| DATA_STALE | 데이터 신선도 초과 |
| DEVICE_FAULT | 장비 이상 |
| CANDIDATE_HASH_MISMATCH | 승인 직전 후보 변경 |

후보 생성 시 한 번 검사하고 끝내지 않는다. 승인 직전에 후보 해시, 규칙 버전, 데이터 신선도, 장비 상태와 승인자 권한을 다시 검사한다.

### 테스트와 패키징

| 영역 | 기술 |
|---|---|
| 단위 테스트 | pytest |
| 규칙 속성 테스트 | Hypothesis |
| API 테스트 | FastAPI TestClient 또는 HTTPX |
| 화면 흐름 테스트 | Playwright |
| 실행파일 | PyInstaller |
| 프론트 배포 | Vite 정적 빌드를 FastAPI가 제공 |
| 실행 명령 | start.bat |
| 개발 재현 | docker compose up --build |

## 3. 권장 저장소 구조

```text
ai-context/
  PROJECT_STACK.yaml
backend/
  app/
    main.py
    api/
      health.py
      scenarios.py
      simulations.py
      approvals.py
      evaluations.py
      audit.py
    domain/
      models.py
      enums.py
      schemas.py
    simulation/
      network.py
      demand.py
      engine.py
      spillback.py
      kpi.py
    optimization/
      candidates.py
      scoring.py
    safety/
      rules.py
      engine.py
      versions.py
    ai/
      client.py
      prompts.py
      schemas.py
      reviewers.py
      fallback.py
    services/
      orchestrator.py
      state_machine.py
      approval_service.py
      evaluation_service.py
    storage/
      database.py
      repositories.py
      audit_repository.py
  fixtures/
    scenarios/
    demand_traces/
    cached_runs/
    ai_reviews/
  tests/
    unit/
    property/
    api/
    contract/
frontend/
release/
  windows-x64/
start.bat
compose.yaml
```

## 4. P0 API 계약

### GET /api/health

서버, SQLite, fixture와 선택적 LLM 상태를 반환한다.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "ready",
  "fixture_mode": true,
  "llm": "unavailable"
}
```

### GET /api/scenarios

고정된 합성 시나리오 목록을 반환한다.

최소 시나리오는 정상, 출퇴근 혼잡과 사고 차로 폐쇄다.

### POST /api/simulations

기준안과 후보안의 예측 실행을 생성한다.

필수 입력은 시나리오 ID, seed, 기준 TOD와 선택적 실행 모드다.

응답에는 run_id, 상태, result_source와 조회 주소를 포함한다.

### GET /api/simulations/{run_id}

타임라인, 기준 KPI, 후보별 예상 KPI, AI 검토, 안전 결과와 현재 상태를 반환한다.

`result_source`는 반드시 `live_simulation`, `cached_simulation`, `fixture` 중 하나여야 한다.

### GET /api/simulations/{run_id}/events

시뮬레이션 화면 재생에 필요한 상태 이벤트를 SSE로 전달한다.

### POST /api/approvals

안전검사를 통과한 후보를 승인하거나 거절한다.

서버는 승인 직전에 후보 해시와 규칙 버전을 다시 검사한다. 안전 실패, 데이터 만료, 후보 변경 또는 권한 오류가 있으면 적용 상태 전이를 거부한다.

### POST /api/evaluations

승인된 후보를 예측과 다른 평가 trace에 적용한다. 예측값과 적용 후 시뮬레이션 관측값을 분리한다.

### GET /api/audit/{run_id}

입력 스냅샷, seed, 후보, KPI, AI 구조화 출력, 안전 결과, 승인과 평가 결과를 조회하거나 JSON으로 내보낸다.

## 5. 현재 백엔드 파트에서 완성 가능한 코드 기능

### BE-01 데이터 계약과 fixture 검증

Pydantic으로 Intersection, Observation, SignalPlan, Proposal, SafetyResult, Decision과 Evaluation 모델을 만든다.

잘못된 시간, 음수 교통량, 존재하지 않는 교차로, 허용 범위를 벗어난 신호시간과 스키마가 다른 AI 응답을 API 진입 단계에서 차단할 수 있다.

이 기능이 완성되면 프론트엔드는 실제 백엔드를 기다리지 않고 동일한 예제 JSON으로 전체 화면을 구현할 수 있다.

### BE-02 결정론적 시나리오 생성기

정상, 출퇴근 혼잡과 사고 시나리오의 차량 도착 trace를 생성하거나 고정 파일에서 읽는다.

같은 시나리오 ID와 seed를 사용하면 같은 차량 유입과 사건 시점이 반환되어야 한다.

### BE-03 5개 교차로 큐 및 spillback 시뮬레이터

각 교차로의 차로군별 대기 차량 수, 신호 현시, 잔여시간과 보행 상태를 관리한다.

각 링크의 주행시간, 저장 가능 차량 수, 점유율과 회전 비율을 관리한다.

상류 교차로에서 방출된 차량이 링크 주행시간 이후 하류 교차로에 도착하도록 연결한다.

하류 링크가 포화되면 상류 방출을 제한해 정체가 뒤로 번지는 spillback을 재현한다.

이 기능이 있어야 화면의 정체 전파가 단순 애니메이션이 아니라 계산 결과가 된다.

### BE-04 KPI 계산 엔진

평균 지체, 최대 및 평균 대기행렬, 정지율, 보행 대기시간과 spillback 위험을 계산한다.

각 KPI는 수식, 단위, 집계구간과 반올림 방식을 코드 상수와 문서에서 동일하게 관리한다.

화면에 표시하는 개선율은 기준안과 후보안 실행 결과에서 계산하며 목표 수치를 하드코딩하지 않는다.

### BE-05 신호 후보 생성기

기준 TOD 주변의 허용된 녹색시간, 주기와 오프셋 조합을 생성한다.

명백한 범위 위반을 먼저 제거하고 나머지 후보를 같은 수요와 seed로 시뮬레이션한다.

점수 함수로 후보를 정렬하고 A, B, C 후보를 반환한다.

### BE-06 결정론적 안전 가드

후보별로 보행 최소시간, 최소 및 최대 녹색시간, 황색과 전적색, 상충 현시, 주기 합계, 변경폭, 데이터 신선도와 장비 상태를 검사한다.

결과는 통과 여부뿐 아니라 안정적인 규칙 코드와 설명을 반환한다.

위험 후보 A가 항상 동일한 규칙 코드로 탈락하도록 fixture 테스트를 만들 수 있다.

### BE-07 구조화된 AI 다관점 검토

시뮬레이터가 계산한 KPI와 안전 결과를 네 가지 관점의 입력으로 변환한다.

AI는 각 관점에서 verdict, risk_codes, explanation과 questions를 구조화된 JSON으로 반환한다.

실시간 LLM 응답이 없거나 스키마가 틀리면 저장된 응답 또는 규칙 기반 설명으로 전환한다.

프론트는 라이브와 폴백을 구분하지 않고 같은 스키마를 사용할 수 있다.

### BE-08 상태 전이와 운영자 승인

서버 상태는 다음 순서를 따른다.

```text
CREATED
→ PREDICTED
→ AI_REVIEWED
→ SAFETY_PASSED 또는 SAFETY_REJECTED
→ HUMAN_APPROVED 또는 HUMAN_REJECTED
→ TWIN_APPLIED
→ EVALUATED
```

예외 상태는 EXPIRED, DATA_STALE, SIMULATION_FAILED, APPLY_FAILED와 ROLLED_BACK이다.

클라이언트가 직접 상태를 바꾸지 못하게 하고 모든 전이를 서버에서 검증한다.

### BE-09 적용 후 평가

승인 전 예상 KPI와 승인 후 평가 KPI를 같은 실행값으로 재사용하지 않는다.

예측용 수요 trace와 별도의 평가 trace를 사용해 기준안과 승인안을 다시 비교한다.

화면의 actual은 실제 도로 실측치가 아니라 적용 후 시뮬레이션 관측 KPI로 반환한다.

### BE-10 감사 로그와 재현

한 실행을 다시 재생할 수 있도록 다음 항목을 저장한다.

시나리오 ID와 입력 스냅샷

관측시각과 수집시각

교차로 및 링크 구성 버전

기준 TOD와 후보 파라미터

후보 점수와 동점 처리

시뮬레이터와 규칙 버전

모델과 프롬프트 버전

AI 구조화 출력

seed

승인자, 시각과 사유

적용 전후 KPI

AI 내부 사고과정은 저장 대상으로 표현하지 않는다.

### BE-11 REST와 SSE 제공

FastAPI가 고정 API 계약을 제공하고 OpenAPI 문서를 자동 생성한다.

프론트는 simulation 생성, 실행 조회, SSE 재생, 승인과 평가 요청만 연결하면 된다.

### BE-12 폴백과 오프라인 시연

실제 시뮬레이터가 실패하면 검증된 cached_simulation을 반환한다.

캐시도 읽지 못하면 fixture를 반환한다.

LLM 실패 시 규칙 기반 설명 또는 저장된 AI 검토를 반환한다.

모든 응답에 결과 출처를 표시하여 실제 계산과 재생 데이터를 구분한다.

### BE-13 Windows 실행 번들

Vite 정적 빌드를 FastAPI가 제공하도록 묶는다.

PyInstaller로 서버와 Python 의존성을 하나의 실행 디렉터리로 만든다.

`start.bat`은 사용 가능한 로컬 포트를 찾고 서버를 실행한 뒤 브라우저를 연다.

프로그램 종료와 재실행 시 포트 충돌이나 잔류 프로세스가 생기지 않게 한다.

## 6. 백엔드 완료 순서

가장 먼저 Pydantic 스키마와 완결된 fixture를 만든다.

그다음 시나리오 생성기, 큐 시뮬레이터와 KPI 엔진을 구현한다.

이후 후보 생성기와 안전 가드를 연결한다.

그다음 AI 검토와 폴백을 동일 스키마로 구현한다.

마지막으로 상태 전이, 승인, 평가, 감사 로그, SSE와 Windows 패키징을 연결한다.

프론트가 기다리지 않도록 실제 시뮬레이터보다 fixture 계약을 먼저 완성한다.

## 7. P0 완료 판정

다음 조건을 모두 만족하면 백엔드 P0를 완료한 것으로 본다.

동일 입력과 seed에서 동일한 KPI와 후보 순위가 나온다.

5개 교차로 사이의 정체 전파와 spillback이 계산된다.

후보 A가 명시된 안전 규칙 코드로 탈락한다.

후보 B 또는 C 중 하나가 안전검사를 통과한다.

안전 실패 후보는 승인 API가 거부한다.

오래된 데이터와 변경된 후보도 승인 API가 거부한다.

예측 실행과 적용 후 평가 실행이 분리된다.

화면 수치와 저장된 실행 로그가 일치한다.

인터넷, API 키, Python, Node와 SUMO가 없는 Windows x64에서 `start.bat`으로 실행된다.

정상 상태부터 후보 비교, 안전검사, 승인과 복구 결과까지 3분 안에 완주한다.

## 8. AI 코딩 도구 규칙

AI는 실제 세종시 센서 데이터를 발명하지 않는다. 모든 테스트 데이터는 합성이라고 표시한다.

AI는 18퍼센트나 13퍼센트와 같은 목표 개선율을 코드에 하드코딩하지 않는다.

AI는 KPI 계산, 안전 판정과 최종 승인을 LLM에 위임하지 않는다.

라이브, 캐시와 fixture 모드는 동일한 Pydantic 응답 스키마를 사용한다.

모든 실행은 seed, 입력, 버전, 후보 해시, 승인과 KPI를 기록한다.

main 브랜치는 라이브 기능이 미완성이어도 fixture 모드로 3분 시연이 가능해야 한다.

P0에서는 무거운 네이티브 의존성보다 순수 Python 구현을 우선한다.
