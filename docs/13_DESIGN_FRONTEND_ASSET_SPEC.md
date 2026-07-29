# 김경은 디자인 병렬 작업 및 프론트엔드 에셋 규격

> [!IMPORTANT]
> **프론트 적용 대상 대체 공지 — 2026-07-29**
>
> 이 문서의 에셋 크기·파일명·상태 ID·색상 규격은 계속 유효하지만,
> 적용 대상은 React/Vite 컴포넌트가 아니라 제출 정본인
> `frontend/index.html` 정적 단일 페이지다.
>
> - 정본 프론트: `frontend/index.html`, `frontend/demo_run.js`,
>   `frontend/public/assets/`
> - 구현 방식: 무빌드 HTML·CSS·JavaScript, 로컬 SVG/CSS 자산
> - 제공 방식: FastAPI의 정적 파일 mount
> - 폴백: API 실패 시 `window.DEMO_RUN` fixture 재생
> - 비정본: `frontend/src/*.tsx`는 post-hackathon 참고 코드이며
>   8월 2일 제출 빌드·실행·패키징 경로가 아님
>
> 아래에서 “컴포넌트”는 시각 상태와 배치 규격을 뜻한다. 실제 제출
> 구현은 정적 HTML 요소와 CSS 클래스로 반영한다.
>
> Notion 공유본:
> [12 실행 명세](https://app.notion.com/p/3ab5d8c25aa4810684e5d9dddd24543f),
> [13 팀 실행 계획](https://app.notion.com/p/3ab5d8c25aa4815cb381d7fc602979cb)

에셋 규격은 2026년 7월 28일 확정본이며, 구현 대상은 위 대체 공지를
따른다. 김경은은 프론트엔드와 백엔드의 완성을 기다리지 않고, 고정된
화면 상태와 아래 규격을 기준으로 디자인 에셋을 독립 제작한다.

## 1. 김경은의 최종 책임

김경은은 RainFlow Sejong의 디자인 담당으로서 다음 결과물에 최종 책임을 가진다.

| 작업 영역 | 해야 할 일 | 완료 산출물 |
|---|---|---|
| 디자인 토큰 | 상태 색상, 배경, 텍스트, 테두리, 그림자, 간격, 모서리 규격 확정 | `frontend/public/assets/design-tokens.css` |
| 상태 아이콘 | 정상, 우천, 정체, spillback, 안전 통과, 안전 탈락, 승인, 거절, 센서 결측, 통신 지연, 데이터 출처 아이콘 제작 | SVG 아이콘 세트 |
| 교차로 그래픽 | 정상, 우천 경고, 마비, 정책 적용, 복구 상태를 조합 가능한 레이어로 제작 | 교차로 배경과 상태별 SVG 레이어 |
| 정책 카드 | `no_action`, `fixed_metering`, `corridor_gating`의 기본, 선택, 추천, 탈락 상태 설계 | 정책 카드 컴포넌트 규격 |
| KPI 카드 | 기준, 개선, 악화, 위험, 데이터 없음, fixture 상태 설계 | KPI 카드 규격 |
| 안전 검토 | 검사 대기, 진행, 통과, 탈락, 승인 불가와 탈락 사유 시각화 | 안전 검토 패널 규격 |
| 발표 시각물 | 정상, 우천 정체 전파, 승인 후 복구의 핵심 장면 제작 | README와 발표 자료용 이미지 3장 |

김경은은 정책 내용, KPI 계산식, 사용자 흐름을 새로 기획하지 않는다. 준이 확정한 화면 흐름과 최영의 데이터 계약을 시각적으로 구현한다.

## 2. 화면 크기 표준

### 기본 데스크톱 기준

| 항목 | 확정 규격 |
|---|---|
| 기준 디자인 프레임 | 1440 × 900 px |
| 최소 지원 화면 | 1280 × 720 px |
| 권장 브라우저 배율 | 100% |
| 전체 바깥 여백 | 24 px |
| 상단 헤더 높이 | 64 px |
| 그리드 | 12열 |
| 열 사이 간격 | 24 px |
| 기본 간격 체계 | 8 px 배수 |
| 카드 모서리 | 12 px |
| 모달 모서리 | 16 px |
| 최소 클릭 영역 | 44 × 44 px |

1440 × 900 화면을 기준으로 설계하되 1280 × 720에서도 핵심 시연 흐름이 스크롤 없이 보이도록 한다. 1280 px 미만에서는 핵심 패널을 세로 배치할 수 있으나 제출 시연은 데스크톱을 기준으로 한다.

### 화면 영역 배치

| 영역 | 기준 크기 및 비율 |
|---|---|
| 상단 헤더 | 전체 폭, 높이 64 px |
| 교차로 시뮬레이션 영역 | 8열, 최소 860 × 520 px |
| 우측 판단 패널 | 4열, 최소 폭 360 px |
| 하단 KPI 영역 | 전체 폭, 카드 4개 동일 너비 |
| 모달 최대 폭 | 720 px |
| 로그 패널 최대 높이 | 240 px, 내부 스크롤 |

교차로 영역의 제작 기준 뷰박스는 `0 0 960 540`으로 고정한다. 프론트는 비율을 유지해 확대 또는 축소한다.

## 3. 반응형 기준

| 구간 | 동작 |
|---|---|
| 1440 px 이상 | 8열 교차로와 4열 우측 패널을 나란히 표시 |
| 1280–1439 px | 같은 구조 유지, 패널 내부 간격 축소 |
| 1024–1279 px | 교차로 위, 정책과 안전 패널 아래 배치 |
| 1023 px 이하 | QA 확인용만 지원, 제출 시연 대상에서 제외 |

핵심 버튼, 승인 상태, 안전 탈락 사유, 결과 출처 표시는 모든 구간에서 숨기지 않는다.

## 4. 에셋 파일 규격

### 아이콘

| 항목 | 규격 |
|---|---|
| 기본 형식 | SVG |
| 기본 뷰박스 | `0 0 24 24` |
| 기본 표시 크기 | 24 × 24 px |
| 보조 크기 | 16 × 16 px, 20 × 20 px, 32 × 32 px |
| 선 굵기 | 2 px |
| 선 끝과 연결 | round |
| 색상 | 가능하면 `currentColor` 사용 |
| 배경 | 투명 |

### 교차로 및 상태 그래픽

| 항목 | 규격 |
|---|---|
| 기본 형식 | SVG |
| 기준 뷰박스 | `0 0 960 540` |
| 배경 | 투명 또는 별도 배경 레이어 |
| 구성 | 도로, 차량, 빗방울, 대기행렬, 위험 구역, 정책 효과를 별도 그룹으로 분리 |
| 애니메이션 | CSS로 제어할 수 있도록 레이어 ID 부여 |
| 금지 | 외부 URL 이미지, CDN 의존, 포함되지 않은 웹폰트 |

### 발표 이미지

| 항목 | 규격 |
|---|---|
| 기본 해상도 | 1920 × 1080 px |
| 비율 | 16:9 |
| 형식 | PNG |
| 배율 | 2배 내보내기 원본 보관 |
| 용도 | README, 발표 슬라이드, 데모 장애 대비 화면 |

PNG는 발표용 완성 장면과 스크린샷에만 사용한다. 앱 내부 아이콘과 교차로 그래픽은 SVG를 기본으로 한다.

## 5. 파일명과 저장 위치

파일명은 영문 소문자와 하이픈을 사용한다.

```text
frontend/public/assets/icons/status-normal.svg
frontend/public/assets/icons/status-rain-warning.svg
frontend/public/assets/icons/status-spillback.svg
frontend/public/assets/icons/safety-pass.svg
frontend/public/assets/icons/safety-reject.svg
frontend/public/assets/icons/operator-approve.svg
frontend/public/assets/icons/data-fixture.svg
frontend/public/assets/intersection/corridor-base.svg
frontend/public/assets/intersection/rain-layer.svg
frontend/public/assets/intersection/queue-layer.svg
frontend/public/assets/intersection/recovery-layer.svg
frontend/public/assets/presentation/scene-normal.png
frontend/public/assets/presentation/scene-spillback.png
frontend/public/assets/presentation/scene-recovery.png
frontend/public/assets/design-tokens.css
```

파일명에 공백, 한글, 괄호, 최종, 진짜최종 같은 버전 표현을 사용하지 않는다. 수정 버전은 Git 기록으로 관리한다.

## 6. 디자인 토큰 기준

다음 토큰 이름을 프론트와 공통으로 사용한다.

```css
:root {
  --status-normal: #2563eb;
  --status-rain-warning: #d97706;
  --status-spillback: #dc2626;
  --status-safe: #15803d;
  --status-rejected: #b91c1c;
  --status-approval: #7c3aed;
  --status-recovery: #0f766e;

  --surface-canvas: #f8fafc;
  --surface-panel: #ffffff;
  --surface-muted: #f1f5f9;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --border-default: #cbd5e1;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  --radius-card: 12px;
  --radius-modal: 16px;
}
```

색상은 상태를 구분하는 보조 수단이다. 아이콘, 텍스트, 패턴을 함께 사용하여 색상만으로 의미를 전달하지 않는다. 일반 텍스트는 배경과 최소 4.5:1 대비를 확보한다.

## 7. 폰트와 문구 규격

앱은 오프라인 실행을 위해 시스템 폰트를 우선 사용한다.

```css
font-family: Pretendard, "Noto Sans KR", "Segoe UI", Arial, sans-serif;
```

웹폰트를 포함하지 못한 환경에서도 레이아웃이 무너지지 않아야 한다.

| 용도 | 크기 | 굵기 |
|---|---:|---:|
| 화면 제목 | 24 px | 700 |
| 패널 제목 | 18 px | 700 |
| 카드 수치 | 28 px | 700 |
| 본문 | 14–16 px | 400–500 |
| 상태 배지 | 12–13 px | 600 |
| 보조 설명 | 12–14 px | 400 |

## 8. 상태별 필수 에셋

| 화면 상태 | 필수 디자인 결과물 |
|---|---|
| `normal` | 정상 교통 흐름, 정상 센서, 기본 KPI 카드 |
| `rain_warning` | 빗방울 레이어, 우천 경고 배지, 속도 저하 표현 |
| `spillback` | 대기행렬, 상류 전파, 위험 구역, 마비 경고 |
| `policy_compare` | 세 정책 카드, 선택과 추천 상태 |
| `safety_review` | 검사 진행, 통과, 탈락, 탈락 사유 |
| `operator_approval` | 변경 요약, 승인, 거절, 승인 불가 상태 |
| `recovery_compare` | 적용 전후 비교, 회복 흐름, 개선 KPI |

## 9. 김경은의 병렬 납품 순서

| 순서 | 납품 항목 | 다른 팀원이 즉시 사용하는 방법 |
|---:|---|---|
| 1 | 디자인 토큰과 상태 색상 | 프론트가 CSS 변수로 즉시 적용 |
| 2 | 교차로 기본 SVG와 네 가지 상태 레이어 | fixture 화면에 즉시 배치 |
| 3 | 안전 통과와 탈락 아이콘 | 안전 검토 패널 구현 |
| 4 | 정책 카드 3종 | 정책 비교 컴포넌트 구현 |
| 5 | KPI 카드 상태 규격 | KPI 데이터 연결 |
| 6 | 발표용 핵심 장면 3장 | README와 발표 자료에 적용 |

김경은은 전체 화면 완성이나 API 연동을 기다리지 않는다. 준이 화면 구조를 변경하더라도 `960 × 540` 교차로 뷰박스, SVG 아이콘, 8 px 간격 체계와 상태 ID가 유지되는 한 작업을 계속한다.

## 10. 오늘 완료 기준

다음 항목이 전달되면 김경은의 7월 28일 작업을 완료로 판정한다.

- `design-tokens.json` 또는 동일 내용을 가진 CSS 변수 파일
- 상태 아이콘 최소 12개
- `960 × 540` 교차로 기본 SVG
- 정상, 우천, 마비, 복구 상태 레이어
- 정책 카드 3종 규격
- KPI 카드 규격
- 안전검사 통과와 탈락 패널
- 발표용 16:9 이미지 초안 3장
- 프론트에서 확인 가능한 파일명과 저장 위치 목록

핵심 우선순위는 교차로 SVG, 상태 토큰, 안전검사 아이콘, 정책 카드다. 캐릭터와 장식 요소는 P0 시연이 완성된 뒤에만 추가한다.
